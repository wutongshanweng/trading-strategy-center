"""
期权采集器 — 中国期权日线 + 希腊值 (akshare 免费源)。

设计文档 §五 Phase 5:
- ETF期权 (50/300ETF), 股指期权 (IO/HO), 商品期权 (DCE/CZCE/SHFE)
- options_daily: IV/Greeks/理论价 (akshare option_risk_analysis_em 等)
- 期权以日线为主, Greeks/IV 是核心

注: akshare 希腊值接口为当日实时快照, 历史 Greeks 需逐日累积。
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from loguru import logger

from ..fetchers.options_fetcher import ChinaOptionsFetcher
from ..options_analytics import DEFAULT_RISK_FREE, compute_option_greeks
from .base_collector import BaseCollector

_CKPT = Path(__file__).resolve().parent.parent / "download_checkpoint.json"


def _ckpt_read() -> Dict:
    if _CKPT.exists():
        try:
            return json.loads(_CKPT.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": [], "failures": {}, "stats": {}}


def _ckpt_write(data: Dict) -> None:
    _CKPT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class OptionsCollector(BaseCollector):
    """中国期权采集器。"""

    asset_type = "option"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._opt = ChinaOptionsFetcher()

    def collect_etf_option_daily(self, contract_code: str, product_code: str = "510050") -> int:
        """单个 ETF 期权合约日线 -> kline (timeframe=D1)。"""
        df = self._opt.get_etf_option_daily(contract_code)
        return self._store_option_kline(df, contract_code, product_code)

    def collect_index_option_daily(self, contract_code: str) -> int:
        """股指期权 (IO/HO) 日线 -> kline。"""
        product = contract_code.upper()[:2]
        df = self._opt.get_index_option_daily(contract_code)
        return self._store_option_kline(df, contract_code, product)

    def _store_option_kline(self, df: pd.DataFrame, contract: str, product: str) -> int:
        if df is None or df.empty:
            return 0
        cols = {c: c for c in df.columns}
        # 新浪期权日线列: 日期/开盘/最高/最低/收盘/成交量/持仓量 (或英文)
        rename = {"日期": "date", "开盘": "open", "最高": "high", "最低": "low",
                  "收盘": "close", "成交量": "volume", "持仓量": "open_interest"}
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        tcol = "date" if "date" in df.columns else ("datetime" if "datetime" in df.columns else None)
        if tcol is None or "close" not in df.columns:
            logger.warning(f"{contract} option daily 缺少时间/收盘列: {list(df.columns)}")
            return 0
        sid = self.registry.get_or_create_symbol(
            contract, product, asset_type="option", name=contract,
        )
        out = pd.DataFrame({
            "datetime": pd.to_datetime(df[tcol]),
            "symbol_id": sid, "timeframe": "D1",
            "open": pd.to_numeric(df.get("open"), errors="coerce"),
            "high": pd.to_numeric(df.get("high"), errors="coerce"),
            "low": pd.to_numeric(df.get("low"), errors="coerce"),
            "close": pd.to_numeric(df.get("close"), errors="coerce"),
            "volume": pd.to_numeric(df.get("volume"), errors="coerce"),
        })
        if "open_interest" in df.columns:
            out["open_interest"] = pd.to_numeric(df["open_interest"], errors="coerce")
        out = out.dropna(subset=["close"])
        # 按 key 去重: 同一合约+时间帧保留最后一条 (数据源可能有重复)
        key_cols = ["datetime", "symbol_id", "timeframe"]
        out = out.drop_duplicates(subset=key_cols, keep="last")
        return self.store.upsert_df("kline", out, key_cols)

    def collect_greeks_snapshot(self) -> int:
        """当日全市场期权希腊值快照 (东财, ETF/股指期权) -> options_daily。

        akshare option_risk_analysis_em 直接给 Greeks/IV, 无需 BS 模型。
        是当日快照 (无历史), 需逐日累积。商品期权不在此接口覆盖范围 ->
        见 collect_commodity_greeks (用 Black76 自算)。
        """
        df = self._opt.get_option_risk_analysis()
        if df is None or df.empty:
            logger.info("期权希腊值快照为空 (可能非交易时段)")
            return 0
        rename = {
            "期权代码": "code", "期权名称": "name", "标的价格": "underlying_close",
            "隐含波动率": "iv", "Delta": "delta", "Gamma": "gamma",
            "Vega": "vega", "Theta": "theta", "Rho": "rho", "时间价值": "time_value",
            "内在价值": "intrinsic_value", "理论价格": "theoretical_price", "日期": "date",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        if "code" not in df.columns:
            logger.warning(f"希腊值快照缺少期权代码列: {list(df.columns)[:8]}")
            return 0
        today = pd.Timestamp(df["date"].iloc[0]).date() if "date" in df.columns else date.today()
        rows = []
        for _, r in df.iterrows():
            code = str(r["code"]).strip()
            if not code:
                continue
            sid = self.registry.get_or_create_symbol(
                code, code, asset_type="option", name=str(r.get("name", code)),
            )
            rows.append({
                "date": today, "symbol_id": sid,
                "iv": _num(r.get("iv")), "delta": _num(r.get("delta")),
                "gamma": _num(r.get("gamma")), "vega": _num(r.get("vega")),
                "theta": _num(r.get("theta")), "rho": _num(r.get("rho")),
                "theoretical_price": _num(r.get("theoretical_price")),
                "time_value": _num(r.get("time_value")),
                "intrinsic_value": _num(r.get("intrinsic_value")),
                "underlying_close": _num(r.get("underlying_close")),
            })
        if not rows:
            return 0
        out = pd.DataFrame(rows)
        n = self.store.upsert_df("options_daily", out, ["date", "symbol_id"])
        logger.info(f"期权希腊值快照入库 {n} 行 ({today})")
        return n

    def collect_month(self, year: int, month: int = None) -> Dict[str, int]:
        """按月采集期权数据 (ETF/股指期权 Greeks 快照 + K线)。

        Args:
            year: 年份
            month: 月份 (1-12)，留空则采集当月

        Returns:
            {greeks_rows, etf_contracts, index_contracts, error}
        """
        import calendar
        import datetime as _dt
        import time

        if month is None:
            now = _dt.datetime.now()
            year = year or now.year
            month = month or now.month

        # 月度 checkpoint: opt:YYYYmMM 格式
        key = f"opt:{year}m{month:02d}"
        ckpt = _ckpt_read()
        if key in ckpt.get("done", []):
            logger.info(f"[{key}] 已完成，跳过")
            return {"greeks_rows": 0, "etf_contracts": 0, "index_contracts": 0, "skipped": True}
        # 计算月份范围
        start_day = f"{year}-{month:02d}-01"
        last_day = calendar.monthrange(year, month)[1]
        end_day = f"{year}-{month:02d}-{last_day:02d}"

        totals = {"greeks_rows": 0, "etf_contracts": 0, "index_contracts": 0}

        # ETF 期权: 50/300/500 ETF，每个标的分批处理
        for und in ("510050", "510300", "510500"):
            for otype in ("看涨期权", "看跌期权"):
                try:
                    cdf = self._opt.get_etf_option_codes(option_type=otype, underlying=und)
                    col = _first_col(cdf, ["期权代码", "合约代码", "代码"])
                    if not col:
                        continue
                    for c in [str(x) for x in cdf[col].tolist()]:
                        try:
                            n = self.collect_etf_option_daily(c, und)
                            if n > 0:
                                totals["etf_contracts"] += 1
                                totals["greeks_rows"] += n
                            # 每个合约后休眠一下，减少数据库压力
                            time.sleep(0.05)
                        except Exception as e:
                            logger.warning(f"{c} ETF期权采集失败: {e}")
                except Exception as e:
                    logger.warning(f"{und}/{otype} 枚举失败: {e}")
            # 每个标的完成后休眠一下
            time.sleep(0.3)

        # 股指期权: IO/HO
        for idx in ("IO", "HO", "IM"):
            try:
                cdf = self._opt.get_index_option_codes(index_code=idx)
                col = _first_col(cdf, ["期权代码", "合约代码"])
                if col:
                    for c in [str(x) for x in cdf[col].tolist()]:
                        try:
                            n = self.collect_index_option_daily(c)
                            if n > 0:
                                totals["index_contracts"] += 1
                                totals["greeks_rows"] += n
                        except Exception as e:
                            logger.warning(f"{c} 股指期权采集失败: {e}")
            except Exception as e:
                logger.warning(f"{idx} 枚举失败: {e}")

        # 写月度 checkpoint
        try:
            ckpt = _ckpt_read()
            if key not in ckpt.get("done", []):
                ckpt.setdefault("done", []).append(key)
                ckpt["stats"] = ckpt.get("stats", {})
                ckpt["stats"][key] = totals
                _ckpt_write(ckpt)
        except Exception as e:
            logger.warning(f"写入checkpoint失败: {e}")

        logger.info(f"期权 {year}年{month}月采集: {totals}")
        return totals

    # ─── 商品期权 Greeks (akshare 不提供 -> Black76 自算) ───────────────
    def _underlying_close(self, underlying_code: str, on: date) -> Optional[tuple[int, float]]:
        """取标的期货某日 D1 收盘 (settlement 优先, 否则 close)。返回 (symbol_id, price)。"""
        df = self.store.query(
            """SELECT k.symbol_id, k.close, k.settlement
               FROM kline k JOIN symbols sy ON k.symbol_id = sy.symbol_id
               WHERE sy.code = ? AND k.timeframe = 'D1' AND CAST(k.datetime AS DATE) = ?""",
            [underlying_code.upper(), on],
        )
        if df.empty:
            return None
        row = df.iloc[0]
        price = row["settlement"] if pd.notna(row["settlement"]) else row["close"]
        if pd.isna(price) or float(price) <= 0:
            return None
        return int(row["symbol_id"]), float(price)

    def _resolve_expiry(self, symbol_code: str, year: Optional[int],
                        month: Optional[str]) -> Optional[date]:
        """到期日: 优先 symbols.expire_date; 缺失则用商品期权惯例近似
        (到期月在交割月前一月, 取该月末)。"""
        df = self.store.query(
            "SELECT expire_date FROM symbols WHERE code = ?", [symbol_code.upper()]
        )
        if not df.empty and pd.notna(df.iloc[0]["expire_date"]):
            return pd.Timestamp(df.iloc[0]["expire_date"]).date()
        if not year or not month:
            return None
        m = int(month)
        ey, em = (year - 1, 12) if m == 1 else (year, m - 1)  # 交割月前一月
        last = pd.Timestamp(year=ey, month=em, day=1) + pd.offsets.MonthEnd(0)
        return last.date()

    def collect_commodity_greeks(self, exchange: str, symbol_cn: str,
                                 trade_date: str = "", r: float = DEFAULT_RISK_FREE) -> int:
        """商品期权某交易日全合约 Greeks/IV (Black76 自算) -> options_daily。

        exchange: 大商所/郑商所/上期所; symbol_cn: 如 '豆粕期权'。
        合约代码内嵌标的/类型/行权价 (m2608-C-2500); 标的期货收盘取自仓库 kline。
        """
        df = self._opt.get_commodity_option_daily(exchange, symbol_cn, trade_date)
        if df is None or df.empty:
            logger.info(f"{exchange}/{symbol_cn} {trade_date} 商品期权日线为空")
            return 0
        code_col = _first_col(df, ["合约代码", "合约", "instrument", "代码"])
        close_col = _first_col(df, ["收盘价", "收盘", "close", "结算价", "settle"])
        if not code_col or not close_col:
            logger.warning(f"商品期权日线缺少代码/收盘列: {list(df.columns)}")
            return 0
        on = (pd.Timestamp(trade_date).date() if trade_date else date.today())
        rows = []
        for _, row in df.iterrows():
            code = str(row[code_col]).strip().upper().replace("--", "-")
            meta = self.registry.parse_contract(code)
            if not meta.get("strike_price") or not meta.get("option_type"):
                continue
            price = _num(row[close_col])
            if not price or price <= 0:
                continue
            underlying = code.split("-")[0]  # m2608-C-2500 -> M2608
            u = self._underlying_close(underlying, on)
            if u is None:
                continue
            uid, F = u
            expiry = self._resolve_expiry(code, meta.get("contract_year"), meta.get("contract_month"))
            if expiry is None:
                continue
            t_years = (expiry - on).days / 365.0
            g = compute_option_greeks(price, F, float(meta["strike_price"]), t_years,
                                      meta["option_type"], r, is_futures=True)
            if g is None:
                continue
            sid = self.registry.get_or_create_symbol(code, symbol_cn, asset_type="option", name=code)
            rows.append({"date": on, "symbol_id": sid, "underlying_id": uid,
                         "underlying_close": round(F, 4), **g})
        if not rows:
            logger.info(f"{exchange}/{symbol_cn} {on} 无可算 Greeks 的合约 (缺标的价/到期日?)")
            return 0
        out = pd.DataFrame(rows)
        n = self.store.upsert_df("options_daily", out, ["date", "symbol_id"])
        logger.info(f"{exchange}/{symbol_cn} {on} Greeks 入库 {n} 行")
        return n

    # ─── 商品期权按年逐日采集 (生产: 覆盖该年所有挂过的合约) ───────────────
    def collect_commodity_year(self, year: int, sleep: float = 0.25,
                               ckpt_done: Optional[set] = None,
                               on_progress=None) -> Dict[str, int]:
        """遍历某年所有交易日 × 三所全品种, 落 K线 + IV/Delta (交易所直接提供)。

        各所代码/列名不同, 统一归一化:
        - CZCE: SR609C4600, 列 今收盘/隐含波动率/DELTA
        - SHFE: cu2607C76000, 列 收盘价/德尔塔 (无IV)
        - DCE:  m2608-C-2500, 列 收盘价/隐含波动率/Delta
        ckpt_done: 已完成的 (exchange:symbol:date) 集合, 用于断点续传。
        """
        ak = self._opt._get_ak()
        cal = ak.tool_trade_date_hist_sina()
        cal["trade_date"] = pd.to_datetime(cal["trade_date"])
        today = pd.Timestamp.now().normalize()
        days = [d for d in cal["trade_date"]
                if d.year == year and d <= today]
        ckpt_done = ckpt_done if ckpt_done is not None else set()
        totals = {"kline_rows": 0, "greeks_rows": 0, "contracts": 0, "days": 0}
        # ponytail: DCE API 持续失败，跳过大商所，只同步 CZCE 和 SHFE
        exchanges = {k: v for k, v in self._opt.COMMODITY_OPTION_SYMBOLS.items()
                     if k != "大商所"}  # {交易所中文: [品种中文]}
        import time
        for d in days:
            td = d.strftime("%Y%m%d")
            day_has = False
            for ex_cn, syms in exchanges.items():
                for sym in syms:
                    key = f"{ex_cn}:{sym}:{td}"
                    if key in ckpt_done:
                        continue
                    try:
                        df = self._opt.get_commodity_option_daily(ex_cn, sym, td)
                    except Exception as e:  # noqa: BLE001
                        logger.warning(f"{key} 拉取失败: {e}")
                        continue
                    if df is None or df.empty:
                        continue
                    k, g = self._store_commodity_day(df, sym, d)
                    totals["kline_rows"] += k
                    totals["greeks_rows"] += g
                    if k > 0:
                        day_has = True
                        ckpt_done.add(key)
                        # 只在数据成功存储后才写 checkpoint
                        ck = _ckpt_read()
                        ckey = f"copt:{key}"
                        if ckey not in ck["done"]:
                            ck["done"].append(ckey)
                            _ckpt_write(ck)
                    time.sleep(sleep)
            if day_has:
                totals["days"] += 1
            if on_progress:
                on_progress(td, totals)
        logger.info(f"商品期权 {year} 年采集: {totals}")
        return totals

    def _store_commodity_day(self, df: pd.DataFrame, product_cn: str,
                             dt: pd.Timestamp) -> tuple[int, int]:
        """单交易日某品种全合约 -> kline + options_daily(iv/delta)。返回 (k线行数, greeks行数)。"""
        code_col = _first_col(df, ["合约代码", "合约", "instrument"])
        close_col = _first_col(df, ["今收盘", "收盘价", "收盘", "结算价", "今结算"])
        if not code_col or not close_col:
            return 0, 0
        iv_col = _first_col(df, ["隐含波动率", "隐含波动率(%)", "IV"])
        delta_col = _first_col(df, ["DELTA", "Delta", "德尔塔", "delta"])
        oi_col = _first_col(df, ["持仓量", "持仓量(手)"])
        vol_col = _first_col(df, ["成交量", "成交量(手)"])
        kline_rows, greeks_rows = [], []
        for _, row in df.iterrows():
            code = str(row[code_col]).strip().upper()
            meta = self.registry.parse_contract(code)
            if not meta.get("strike_price"):   # 非期权合约行 (如汇总) 跳过
                continue
            price = _num(row[close_col])
            if not price or price <= 0:
                continue
            # 品种代码: 从合约代码去掉年月+CP+行权价 (如 SR609C4600 -> SR)
            import re as _re
            pm = _re.match(r"^([A-Za-z]{1,3})", code)
            product = pm.group(1) if pm else product_cn
            sid = self.registry.get_or_create_symbol(
                code, product, asset_type="option", name=code)
            kr = {"datetime": dt, "symbol_id": sid, "timeframe": "D1", "close": price}
            o = _num(row.get(_first_col(df, ["今开盘", "开盘价", "开盘"]) or ""))
            h = _num(row.get(_first_col(df, ["最高价", "最高"]) or ""))
            lo = _num(row.get(_first_col(df, ["最低价", "最低"]) or ""))
            if o is not None: kr["open"] = o
            if h is not None: kr["high"] = h
            if lo is not None: kr["low"] = lo
            if vol_col: kr["volume"] = _num(row.get(vol_col))
            if oi_col: kr["open_interest"] = _num(row.get(oi_col))
            kline_rows.append(kr)
            gd = {"date": dt.date(), "symbol_id": sid}
            iv = _num(row.get(iv_col)) if iv_col else None
            dl = _num(row.get(delta_col)) if delta_col else None
            if iv is not None: gd["iv"] = iv
            if dl is not None: gd["delta"] = dl
            if iv is not None or dl is not None:
                greeks_rows.append(gd)
        k = self.store.upsert_df("kline", pd.DataFrame(kline_rows),
                                 ["datetime", "symbol_id", "timeframe"]) if kline_rows else 0
        g = self.store.upsert_df("options_daily", pd.DataFrame(greeks_rows),
                                 ["date", "symbol_id"]) if greeks_rows else 0
        return k, g


def _num(v):
    n = pd.to_numeric(v, errors="coerce")
    return None if pd.isna(n) else float(n)


def _first_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None
