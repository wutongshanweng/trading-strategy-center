"""
仓库全量/批量采集编排 — 进程内版本 (复用 collectors, 写 DuckDB)。

与 scripts/download_all.py 的区别:
- 可在 FastAPI 进程内通过 asyncio.to_thread 异步运行 (采集是同步阻塞的)
- start_date 参数化: 测试环境只下近1个月, 生产环境下全量
- 进度写 download_checkpoint.json (与脚本共用, 支持断点续传)

阶段顺序: futures -> stocks -> options。macro/aggregate/cross-market 留给脚本。
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from ..collectors import FuturesCollector, StocksCollector, OptionsCollector
from ..db.seed_loader import load_all
from ..storage import get_store

_CKPT = Path(__file__).resolve().parent.parent / "download_checkpoint.json"


def _read_ckpt() -> Dict:
    if _CKPT.exists():
        try:
            return json.loads(_CKPT.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": [], "failures": {}, "stats": {}}


def _write_ckpt(data: Dict) -> None:
    _CKPT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def reset_ckpt() -> None:
    """清空 checkpoint — 用于定期全量复跑 (数据校验/补漏)。"""
    _write_ckpt({"done": [], "failures": {}, "stats": {}})


def _products(asset_type: str) -> List[str]:
    df = get_store().query(
        "SELECT code FROM products WHERE asset_type = ? ORDER BY code", [asset_type]
    )
    return df["code"].tolist()


def collect_futures_product(product: str, year: Optional[int] = None,
                            end_year: Optional[int] = None, with_minute: bool = False,
                            start_date: Optional[str] = None) -> Dict:
    """同步采集单个期货品种。
    year 指定: 枚举 year~end_year 每年全部12个月合约; 留空: 采当前在交易合约。"""
    fc = FuturesCollector()
    if year is None:
        return fc.collect_product(product, with_minute=with_minute, start_date=start_date)
    y1 = year
    y2 = end_year or year
    totals = {"D1": 0, "M5": 0, "contracts": 0, "years": []}
    for y in range(y1, y2 + 1):
        res = fc.collect_product_year(product, y, with_minute=with_minute, start_date=start_date)
        totals["D1"] += res.get("D1", 0)
        totals["M5"] += res.get("M5", 0)
        totals["contracts"] += res.get("contracts", 0)
        totals["years"].append(y)
    return totals


def _run_full_sync(phase: str, year: Optional[int], end_year: Optional[int],
                   start_date: Optional[str], with_minute: bool,
                   stock_limit: Optional[int], reset_checkpoint: bool = False) -> Dict:
    """同步执行全量/批量采集。在 to_thread 中调用。
    stock_limit: 测试期股票只下前 N 只; None=全市场。
    reset_checkpoint: 定期全量复跑前清空进度 (数据校验/补漏)。
    start_date=None: 股票从上市日起全历史。"""
    # 归一化资产类型: API 用单数(futures/stock/option), 内部阶段用复数(stocks/options)
    phase = {"stock": "stocks", "option": "options"}.get(phase, phase)
    if reset_checkpoint:
        reset_ckpt()
    load_all()  # 幂等: 确保 products 种子就绪
    ckpt = _read_ckpt()
    results: Dict = {}

    if phase in ("futures", "all"):
        totals = {"D1": 0, "M5": 0, "contracts": 0, "products": 0}
        for product in _products("futures"):
            key = f"fut:{product}:{year or 'live'}-{end_year or ''}"
            if key in ckpt["done"]:
                continue
            try:
                res = collect_futures_product(product, year, end_year, with_minute, start_date)
                totals["D1"] += res.get("D1", 0)
                totals["M5"] += res.get("M5", 0)
                totals["contracts"] += res.get("contracts", 0)
                totals["products"] += 1
                ckpt["done"].append(key)
                ckpt["stats"][key] = {"D1": res.get("D1", 0), "contracts": res.get("contracts", 0)}
                _write_ckpt(ckpt)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"{product} 采集失败: {e}")
                ckpt["failures"][key] = str(e)
                _write_ckpt(ckpt)
        results["futures"] = totals

    if phase in ("stocks", "all"):
        sc = StocksCollector()
        symbols = sc.list_all_symbols()
        if stock_limit:
            symbols = symbols[:stock_limit]
        totals = {"rows": 0, "stocks": 0, "universe": len(symbols)}
        for code in symbols:
            key = f"stk:{code}:{start_date or 'full'}"
            if key in ckpt["done"]:
                continue
            try:
                n = sc.collect_kline(code, start_date=start_date)
                totals["rows"] += n
                if n > 0:
                    totals["stocks"] += 1
                ckpt["done"].append(key)
                _write_ckpt(ckpt)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"{code} 股票采集失败: {e}")
                ckpt["failures"][key] = str(e)
                _write_ckpt(ckpt)
        results["stocks"] = totals

    if phase in ("options", "all"):
        oc = OptionsCollector()
        totals = {"rows": 0, "contracts": 0, "underlyings": 0,
                  "commodity_kline": 0, "commodity_greeks": 0}

        def _codes_col(df):
            if df is None or df.empty:
                return None
            return next((c for c in ("期权代码", "合约代码", "代码") if c in df.columns), None)

        # ETF 期权优先: 50/300/500 ETF, 看涨+看跌 (当前在挂, 代码无年月, 有数据)
        # 放在商品期权之前 — 避免被商品期权全年逐日空转的长循环堵住。
        for und in ("510050", "510300", "510500"):
            got = False
            for otype in ("看涨期权", "看跌期权"):
                try:
                    cdf = oc._opt.get_etf_option_codes(option_type=otype, underlying=und)
                    col = _codes_col(cdf)
                    if not col:
                        continue
                    for c in [str(x) for x in cdf[col].tolist()]:
                        key = f"opt:{und}:{c}"
                        if key in ckpt["done"]:
                            continue
                        try:
                            n = oc.collect_etf_option_daily(c, und)
                            totals["rows"] += n
                            if n > 0:
                                totals["contracts"] += 1; got = True
                            ckpt["done"].append(key); _write_ckpt(ckpt)
                        except Exception as e:  # noqa: BLE001
                            logger.warning(f"{c} 期权采集失败: {e}")
                            ckpt["failures"][key] = str(e); _write_ckpt(ckpt)
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"{und}/{otype} 合约枚举失败: {e}")
            if got:
                totals["underlyings"] += 1

        # 商品期权: 指定 year 时按年逐交易日全量 (覆盖该年所有挂过的合约 + IV/Delta)
        # 注意 2026 时钟下远程数据滞后, 多数交易日返回空属正常。
        if year is not None:
            ckpt_done = set(k for k in ckpt["done"] if k.startswith("copt:"))
            try:
                ct = oc.collect_commodity_year(
                    year, ckpt_done={k[5:] for k in ckpt_done})
                totals["commodity_kline"] = ct.get("kline_rows", 0)
                totals["commodity_greeks"] = ct.get("greeks_rows", 0)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"商品期权 {year} 年采集失败: {e}")

        results["options"] = totals

    return results


async def run_full(phase: str = "all", year: Optional[int] = None,
                   end_year: Optional[int] = None, start_date: Optional[str] = None,
                   with_minute: bool = False, stock_limit: Optional[int] = None,
                   reset_checkpoint: bool = False) -> Dict:
    """异步入口 — 在线程池里跑同步采集, 不阻塞事件循环。"""
    return await asyncio.to_thread(
        _run_full_sync, phase, year, end_year, start_date, with_minute,
        stock_limit, reset_checkpoint
    )


def default_test_start() -> str:
    """测试默认起始: 近1个月。"""
    return (datetime.now() - timedelta(days=31)).strftime("%Y-%m-%d")
