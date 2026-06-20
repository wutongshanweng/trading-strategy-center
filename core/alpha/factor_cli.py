"""
因子系统统一 CLI 入口 — 一行命令跑出结果, 无需 import 任何类。

数据源 (二选一, 优先级 symbol > data):
  --symbol RB2609   从 DuckDB 仓库直取 (期货/股票/期权全支持, 按 code)
  --data file.csv   从 CSV 读 (需含 open/high/low/close/volume)

命令:
  report    一键全因子研究报告 (排名/冗余/推荐组合/HTML+JSON)
  combine   多因子合成一个综合信号 (equal/ic_weight)
  mine      遗传挖掘新因子 (输出 + 可保存 JSON)
  health    因子健康检测 (单个 --factor / 全市场 --all)
  layered   单因子分层回测
  scan      全市场批量巡检 (多标的健康分布, 生产运维用)

示例:
  python -m core.alpha.factor_cli report --symbol RB2609
  python -m core.alpha.factor_cli mine --symbol 600019.SH --generations 20 --save mined.json
  python -m core.alpha.factor_cli health --symbol RB2609 --all
  python -m core.alpha.factor_cli scan --symbols RB2609,600019.SH,SR609C4600
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

import pandas as pd


# ─────────── 数据加载 (仓库 / CSV, 全资产) ───────────

_API_BASE = "http://localhost:8000"


def _load_via_api(symbol: str, limit: int = 1000) -> Optional[pd.DataFrame]:
    """优先经后端 HTTP API 取数 (后端在跑时避开 DuckDB 独占锁)。"""
    try:
        import urllib.request
        import json
        url = (f"{_API_BASE}/api/v1/warehouse/kline?code={symbol.upper()}"
               f"&timeframe=D1&limit={limit}")
        with urllib.request.urlopen(url, timeout=5) as resp:
            d = json.loads(resp.read().decode("utf-8"))
        if not d.get("datetime"):
            return None
        df = pd.DataFrame({
            "datetime": pd.to_datetime(d["datetime"]),
            "open": d["open"], "high": d["high"], "low": d["low"],
            "close": d["close"], "volume": d["volume"],
        }).set_index("datetime")
        for c in ("open", "high", "low", "close", "volume"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        return df.dropna(subset=["close"])
    except Exception:
        return None


def _load_via_db(symbol: str, limit: int = 1000) -> Optional[pd.DataFrame]:
    """后端未运行时直接开 DuckDB (只读) 取数。"""
    try:
        from data_center.storage.duckdb_store import get_store
        store = get_store()
        sid = store.query("SELECT symbol_id FROM symbols WHERE code = ?", [symbol.upper()])
        if sid.empty:
            return None
        symbol_id = int(sid.iloc[0]["symbol_id"])
        df = store.query(
            "SELECT datetime, open, high, low, close, volume FROM kline "
            "WHERE symbol_id=? AND timeframe='D1' ORDER BY datetime DESC LIMIT ?",
            [symbol_id, limit])
        if df.empty:
            return None
        df = df.sort_values("datetime").set_index("datetime")
        for c in ("open", "high", "low", "close", "volume"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        return df.dropna(subset=["close"])
    except Exception as e:  # noqa: BLE001
        print(f"[warn] 仓库直读失败 (后端可能正持锁, 试用 --data 或停后端): {e}",
              file=sys.stderr)
        return None


def _load_from_warehouse(symbol: str, limit: int = 1000) -> Optional[pd.DataFrame]:
    """取单标的 D1 OHLCV (期货/股票/期权按 code 通用)。
    优先 HTTP API (后端在跑), 否则直读 DuckDB。"""
    df = _load_via_api(symbol, limit)
    if df is None or df.empty:
        df = _load_via_db(symbol, limit)
    return df


def load_market_data(symbol: str, limit: int = 1000) -> Optional[pd.DataFrame]:
    """公共取数入口 — 取单标的 D1 OHLCV (期货/股票/期权按 code)。

    供 ml / api 等外部模块复用, 内部委托 _load_from_warehouse。
    无数据返回 None。
    """
    return _load_from_warehouse(symbol, limit)


def _load_data(symbol: Optional[str], data: Optional[str]) -> pd.DataFrame:
    if symbol:
        df = _load_from_warehouse(symbol)
        if df is None or df.empty:
            raise SystemExit(f"仓库中未找到 {symbol} 的 D1 数据 (先在数据中心采集)")
        print(f"[data] {symbol}: {len(df)} 条 D1 (来源: 仓库)")
        return df
    if data:
        df = pd.read_csv(data)
        if "datetime" in df.columns:
            df = df.set_index(pd.to_datetime(df["datetime"]))
        print(f"[data] {data}: {len(df)} 行 (来源: CSV)")
        return df
    raise SystemExit("必须提供 --symbol (仓库) 或 --data (CSV)")


def _alpha101_factors(df: pd.DataFrame, names: Optional[List[str]] = None) -> pd.DataFrame:
    """计算 Alpha101 因子 (子集或全部), 返回 DataFrame[列=因子名]。"""
    from core.alpha.alpha101.factor_registry import FactorRegistry
    reg = FactorRegistry()
    reg.ensure_initialized()
    # 无条件补齐 alpha101 包内的因子类 —— 不信任全局 registry 状态
    # (其他测试可能 reset 后注册了自己的 dummy 因子, 使 registry 非空但缺真因子)
    try:
        import core.alpha.alpha101 as pkg
        from core.alpha.alpha101.base import AlphaFactor
        existing = set(reg.list_all())
        import warnings as _w
        for obj in vars(pkg).values():
            if isinstance(obj, type) and issubclass(obj, AlphaFactor) and obj is not AlphaFactor:
                try:
                    nm = obj().name
                    if nm not in existing:
                        with _w.catch_warnings():
                            _w.simplefilter("ignore")
                            reg.register(obj)
                except Exception:
                    continue
    except Exception:
        pass
    available = reg.list_all()
    pick = [n for n in (names or available) if n in available]
    out = {}
    for name in pick:
        try:
            cls = reg.get(name)
            inst = cls() if isinstance(cls, type) else cls
            out[name] = inst.compute(df)
        except Exception:
            continue
    return pd.DataFrame(out)


# ─────────── 命令实现 ───────────

def cmd_report(args):
    from core.alpha.management import FactorReportGenerator
    df = _load_data(args.symbol, args.data)
    fwd = df["close"].pct_change().shift(-1)
    factors = _alpha101_factors(df, _split(args.factors))
    if factors.empty:
        raise SystemExit("无可用因子")
    gen = FactorReportGenerator()
    rep = gen.generate(factors, fwd, top_n=args.top)
    gen.print_summary(rep)
    if args.html:
        gen.save_html(rep, args.html); print(f"[out] HTML -> {args.html}")
    if args.json:
        gen.save_json(rep, args.json); print(f"[out] JSON -> {args.json}")

    # 交易建议翻译层
    from core.alpha.factor_combiner import FactorCombiner
    from core.alpha.factor_advisor import FactorAdvisor
    ic_values = {f.name: f.ic_mean for f in rep.top_factors}
    signal = FactorCombiner(factors).ic_weight(factors, ic_values)
    advice = FactorAdvisor().advise_from_report(args.symbol or args.data or "?", rep, signal)
    icon = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪", "WAIT": "🟡"}.get(advice.action, "⚪")
    print(f"\n{'='*60}")
    print(f"  【{advice.symbol}】{icon} {advice.action_cn}  "
          f"置信度: {advice.confidence}  |  综合信号: {advice.signal_value:+.4f}")
    print(f"  理由: {advice.reason}")
    if advice.risk_note:
        print(f"  {advice.risk_note}")
    print(f"{'='*60}")


def cmd_combine(args):
    from core.alpha.factor_combiner import FactorCombiner
    df = _load_data(args.symbol, args.data)
    factors = _alpha101_factors(df, _split(args.factors))
    if factors.empty:
        raise SystemExit("无可用因子")
    c = FactorCombiner(factors)
    if args.method == "ic_weight":
        fwd = df["close"].pct_change().shift(-1)
        from research.factor_lab.factor_analyzer import FactorAnalyzer
        an = FactorAnalyzer()
        ics = {col: (an.calculate_ic(factors[col], fwd, "spearman") or 0.0)
               for col in factors.columns}
        signal = c.ic_weight(factors, ics)
    else:
        signal = c.equal_weight(factors)
    print(f"[combine] method={args.method}, 合成信号长度={len(signal)}")
    print(signal.tail(10).round(4).to_string())


def cmd_mine(args):
    from core.alpha.mining import GeneticFactorMiner, GeneticConfig
    df = _load_data(args.symbol, args.data)
    miner = GeneticFactorMiner(GeneticConfig(
        population_size=args.population, generations=args.generations))
    factors = miner.mine(df, n_factors=args.top)
    print(f"[mine] backend={miner.backend}, 挖出 {len(factors)} 个因子:")
    for f in factors:
        print(f"  {f.name}  IC={f.ic_mean:+.4f}  ICIR={f.icir:+.2f}  "
              f"Sharpe={f.sharpe:+.2f}  fit={f.fitness:.4f}")
    if args.save:
        miner.save_factors(factors, args.save); print(f"[out] 因子 -> {args.save}")


def cmd_health(args):
    from core.alpha.management import FactorDecayDetector
    df = _load_data(args.symbol, args.data)
    fwd = df["close"].pct_change().shift(-1)
    names = None if args.all else [args.factor]
    factors = _alpha101_factors(df, names)
    if factors.empty:
        raise SystemExit("无可用因子")
    det = FactorDecayDetector()
    print(f"{'因子':<12}{'健康':<10}{'IC':>9}{'ICIR':>8}  说明")
    for col in factors.columns:
        ic_series = factors[col].rolling(20, min_periods=10).corr(fwd)
        r = det.check(col, ic_series, factors[col], fwd)
        reason = r.reasons[0] if r.reasons else ""
        print(f"{col:<12}{r.health.value:<10}{r.current_ic:>9.4f}{r.icir:>8.2f}  {reason}")


def cmd_layered(args):
    from research.factor_lab.factor_analyzer import FactorAnalyzer
    df = _load_data(args.symbol, args.data)
    fwd = df["close"].pct_change().shift(-1)
    factors = _alpha101_factors(df, [args.factor])
    if factors.empty:
        raise SystemExit(f"因子 {args.factor} 不可用")
    res = FactorAnalyzer().layered_backtest(factors[args.factor], fwd, args.quantiles)
    print(f"[layered] {args.factor} ({args.quantiles} 层):")
    for k, v in res.items():
        if k.startswith("Q"):
            print(f"  {k}: 收益={v['mean_return']:+.4%}  夏普={v['sharpe']:+.2f}")
        elif k == "long_short":
            print(f"  多空: 收益={v['mean_return']:+.4%}  夏普={v['sharpe']:+.2f}")


def cmd_scan(args):
    """全市场批量巡检 — 多标的因子健康分布 (生产运维)。"""
    from core.alpha.management import FactorDecayDetector
    from collections import Counter
    symbols = _split(args.symbols)
    if not symbols:
        raise SystemExit("--symbols 不能为空 (逗号分隔)")
    det = FactorDecayDetector()
    print(f"{'标的':<14}{'健康':>6}{'警告':>6}{'失效':>6}{'数据':>8}")
    for sym in symbols:
        df = _load_from_warehouse(sym)
        if df is None or len(df) < 30:
            print(f"{sym:<14}{'—':>6}{'—':>6}{'—':>6}{'无数据':>8}")
            continue
        fwd = df["close"].pct_change().shift(-1)
        factors = _alpha101_factors(df, _split(args.factors))
        cnt = Counter()
        for col in factors.columns:
            ic_s = factors[col].rolling(20, min_periods=10).corr(fwd)
            cnt[det.check(col, ic_s, factors[col], fwd).health.value] += 1
        print(f"{sym:<14}{cnt['HEALTHY']:>6}{cnt['WARNING']:>6}"
              f"{cnt['DECAYED']:>6}{len(df):>8}")


def _split(v: Optional[str]) -> Optional[List[str]]:
    return [x.strip() for x in v.split(",") if x.strip()] if v else None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="factor_cli", description="因子系统统一 CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    def _common(sp):
        sp.add_argument("--symbol", help="仓库合约/股票代码 如 RB2609 / 600019.SH")
        sp.add_argument("--data", help="CSV 文件路径 (替代 --symbol)")
        sp.add_argument("--factors", help="因子名子集, 逗号分隔 (默认全部)")

    sp = sub.add_parser("report", help="一键全因子研究报告"); _common(sp)
    sp.add_argument("--top", type=int, default=20)
    sp.add_argument("--html", help="HTML 输出路径")
    sp.add_argument("--json", help="JSON 输出路径")
    sp.set_defaults(func=cmd_report)

    sp = sub.add_parser("combine", help="多因子合成综合信号"); _common(sp)
    sp.add_argument("--method", choices=["equal", "ic_weight"], default="ic_weight")
    sp.set_defaults(func=cmd_combine)

    sp = sub.add_parser("mine", help="遗传挖掘新因子"); _common(sp)
    sp.add_argument("--generations", type=int, default=10)
    sp.add_argument("--population", type=int, default=40)
    sp.add_argument("--top", type=int, default=10)
    sp.add_argument("--save", help="挖掘因子保存到 JSON")
    sp.set_defaults(func=cmd_mine)

    sp = sub.add_parser("health", help="因子健康检测"); _common(sp)
    sp.add_argument("--factor", default="alpha001")
    sp.add_argument("--all", action="store_true", help="全因子巡检")
    sp.set_defaults(func=cmd_health)

    sp = sub.add_parser("layered", help="单因子分层回测"); _common(sp)
    sp.add_argument("--factor", default="alpha001")
    sp.add_argument("--quantiles", type=int, default=5)
    sp.set_defaults(func=cmd_layered)

    sp = sub.add_parser("scan", help="全市场批量巡检")
    sp.add_argument("--symbols", required=True, help="多标的, 逗号分隔")
    sp.add_argument("--factors", help="因子子集, 逗号分隔")
    sp.set_defaults(func=cmd_scan)
    return p


def main(argv: Optional[List[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
