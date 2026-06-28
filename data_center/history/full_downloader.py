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


def collect_futures_product_month(product: str, year: int, month: int,
                                  with_minute: bool = False, sleep: float = 0.3,
                                  start_date: Optional[str] = None) -> Dict:
    """采集单个期货品种某年某月的数据。按月处理，断点续传友好。"""
    fc = FuturesCollector()
    key = f"fut:{product}:{year}m{month:02d}"
    ckpt = _read_ckpt()
    if key in ckpt.get("done", []):
        logger.info(f"[{key}] 已完成，跳过")
        return {"D1": 0, "M5": 0, "contracts": 0, "year": year, "month": month}
    try:
        res = fc.collect_product_month(product, year, month, with_minute=with_minute,
                                       sleep=sleep, start_date=start_date)
        # 保存进度
        ckpt = _read_ckpt()
        if key not in ckpt.get("done", []):
            ckpt.setdefault("done", []).append(key)
            ckpt["stats"] = ckpt.get("stats", {})
            ckpt["stats"][key] = {"D1": res.get("D1", 0), "M5": res.get("M5", 0),
                                   "contracts": res.get("contracts", 0)}
            _write_ckpt(ckpt)
        logger.info(f"[{key}] 完成: D1={res.get('D1', 0)}, M5={res.get('M5', 0)}")
        return {"D1": res.get("D1", 0), "M5": res.get("M5", 0),
                "contracts": res.get("contracts", 0), "year": year, "month": month}
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[{key}] 采集失败: {e}")
        ckpt = _read_ckpt()
        ckpt.setdefault("failures", {})[key] = str(e)
        _write_ckpt(ckpt)
        return {"D1": 0, "M5": 0, "contracts": 0, "year": year, "month": month, "error": str(e)}


async def run_futures_month(
    product: str, year: int, month: int,
    with_minute: bool = False, start_date: Optional[str] = None,
    reset_checkpoint: bool = False
) -> Dict:
    """异步入口: 按月采集期货数据。在线程池运行，不阻塞事件循环。"""
    if reset_checkpoint:
        key = f"fut:{product}:{year}m{month:02d}"
        ckpt = _read_ckpt()
        ckpt["done"] = [k for k in ckpt.get("done", []) if k != key]
        _write_ckpt(ckpt)
    return await asyncio.to_thread(
        collect_futures_product_month, product, year, month, with_minute, 0.3, start_date
    )


async def run_full_futures_year(
    product: str, year: int, with_minute: bool = False,
    start_date: Optional[str] = None, reset_checkpoint: bool = False
) -> Dict:
    """异步入口: 按年采集期货数据。最多同步到当前月份。"""
    if reset_checkpoint:
        reset_ckpt()
    max_month = _max_month_for_year(year)
    if max_month == 0:
        logger.info(f"[fut] {product} {year}年是未来年份，跳过")
        return {"D1": 0, "M5": 0, "contracts": 0, "months": [], "note": f"{year}年未到，跳过"}
    totals = {"D1": 0, "M5": 0, "contracts": 0, "months": []}
    for month in range(1, max_month + 1):
        res = await run_futures_month(product, year, month, with_minute, start_date, reset_checkpoint=False)
        totals["D1"] += res.get("D1", 0)
        totals["M5"] += res.get("M5", 0)
        totals["contracts"] += res.get("contracts", 0)
        totals["months"].append({"month": month, **res})
    return totals


def collect_stocks_month(year: int, month: int,
                          symbols: Optional[List[str]] = None,
                          stock_limit: Optional[int] = None) -> Dict:
    """采集股票某年某月的数据。按月处理，断点续传友好。

    Args:
        year: 年份
        month: 月份 (1-12)
        symbols: 股票代码列表 (空时自动获取全市场)
        stock_limit: 限制采集数量 (测试用)
    """
    sc = StocksCollector()
    key = f"stk:{year}m{month:02d}"
    ckpt = _read_ckpt()
    if key in ckpt.get("done", []):
        logger.info(f"[{key}] 已完成，跳过")
        return {"rows": 0, "stocks": 0, "skipped": 0, "universe": 0}

    try:
        if symbols is None:
            symbols = sc.list_all_symbols()
        if stock_limit:
            symbols = symbols[:stock_limit]

        stats = sc.collect_kline_month(symbols=symbols, year=year, month=month)
        # 保存进度
        ckpt = _read_ckpt()
        if key not in ckpt.get("done", []):
            ckpt.setdefault("done", []).append(key)
            ckpt["stats"] = ckpt.get("stats", {})
            ckpt["stats"][key] = {"rows": stats.get("rows", 0),
                                  "stocks": stats.get("synced", 0)}
            _write_ckpt(ckpt)
        logger.info(f"[{key}] 完成: rows={stats.get('rows', 0)}, stocks={stats.get('synced', 0)}")
        return stats
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[{key}] 采集失败: {e}")
        ckpt = _read_ckpt()
        ckpt.setdefault("failures", {})[key] = str(e)
        _write_ckpt(ckpt)
        return {"rows": 0, "stocks": 0, "skipped": 0, "universe": 0, "error": str(e)}


async def run_stocks_month(year: int, month: int,
                            stock_limit: Optional[int] = None,
                            reset_checkpoint: bool = False) -> Dict:
    """异步入口: 按月采集股票数据。在线程池运行，不阻塞事件循环。"""
    if reset_checkpoint:
        key = f"stk:{year}m{month:02d}"
        ckpt = _read_ckpt()
        ckpt["done"] = [k for k in ckpt.get("done", []) if k != key]
        _write_ckpt(ckpt)
    return await asyncio.to_thread(
        collect_stocks_month, year, month, None, stock_limit
    )


def _max_month_for_year(year: int) -> int:
    """返回某年最大可同步月份：未来年=0，当前年=当前月，历史年=12。"""
    today = datetime.now()
    if year > today.year:
        return 0
    if year < today.year:
        return 12
    return today.month


async def run_full_stocks_year(year: int,
                                stock_limit: Optional[int] = None,
                                reset_checkpoint: bool = False) -> Dict:
    """异步入口: 按年采集股票数据。最多同步到当前月份，避免下载未来数据。"""
    if reset_checkpoint:
        reset_ckpt()
    max_month = _max_month_for_year(year)
    if max_month == 0:
        logger.info(f"[stock] {year}年是未来年份，跳过")
        return {"rows": 0, "stocks": 0, "months": [], "note": f"{year}年未到，跳过"}
    totals = {"rows": 0, "stocks": 0, "months": []}
    for month in range(1, max_month + 1):
        res = await run_stocks_month(year, month, stock_limit, reset_checkpoint=False)
        totals["rows"] += res.get("rows", 0)
        totals["stocks"] += res.get("stocks", 0)
        totals["months"].append({"month": month, **res})
    return totals


async def run_full_options_year(year: int, reset_checkpoint: bool = False) -> Dict:
    """异步入口: 按年采集期权数据 (按月分批，写 opt:YYYYmMM checkpoint)。"""
    import time as _time
    if reset_checkpoint:
        reset_ckpt()
    max_month = _max_month_for_year(year)
    if max_month == 0:
        logger.info(f"[option] {year}年是未来年份，跳过")
        return {"rows": 0, "contracts": 0, "months": [], "note": f"{year}年未到，跳过"}
    totals = {"rows": 0, "contracts": 0, "months": []}
    oc = OptionsCollector()
    for month in range(1, max_month + 1):
        key = f"opt:{year}m{month:02d}"
        ckpt = _read_ckpt()
        if key in ckpt.get("done", []):
            logger.info(f"[{key}] 已完成，跳过")
            continue
        try:
            res = await asyncio.to_thread(oc.collect_month, year, month)
            totals["rows"] += res.get("greeks_rows", 0)
            totals["contracts"] += res.get("etf_contracts", 0) + res.get("index_contracts", 0)
            totals["months"].append({"month": month, **res})
        except Exception as e:  # noqa: BLE001
            logger.warning(f"期权 {year}年{month}月采集失败: {e}")
        # 月份之间休眠，避免数据库压力
        _time.sleep(2)
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
        fc = FuturesCollector()
        totals = {"D1": 0, "M5": 0, "contracts": 0, "products": 0}
        for product in _products("futures"):
            # 按月分批处理，断点续传友好
            for month in range(1, 13):
                key = f"fut:{product}:{year}m{month:02d}"
                if key in ckpt["done"]:
                    continue
                try:
                    res = fc.collect_product_month(product, year, month,
                                                   with_minute, 0.3, start_date)
                    totals["D1"] += res.get("D1", 0)
                    totals["M5"] += res.get("M5", 0)
                    totals["contracts"] += res.get("contracts", 0)
                    totals["products"] += 1
                    ckpt = _read_ckpt()
                    if key not in ckpt["done"]:
                        ckpt.setdefault("done", []).append(key)
                        ckpt.setdefault("stats", {})[key] = {
                            "D1": res.get("D1", 0), "contracts": res.get("contracts", 0)}
                        _write_ckpt(ckpt)
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"{product} {year}m{month:02d} 采集失败: {e}")
                    ckpt = _read_ckpt()
                    ckpt.setdefault("failures", {})[key] = str(e)
                    _write_ckpt(ckpt)
        results["futures"] = totals

    if phase in ("stocks", "all"):
        sc = StocksCollector()
        symbols = sc.list_all_symbols()
        if stock_limit:
            symbols = symbols[:stock_limit]
        totals = {"rows": 0, "stocks": 0, "universe": len(symbols)}
        # 按月处理: year 指定时按月循环，断点续传
        if year is not None:
            for month in range(1, 13):
                key = f"stk:{year}m{month:02d}"
                if key in ckpt["done"]:
                    continue
                try:
                    stats = sc.collect_kline_month(symbols=symbols, year=year, month=month)
                    totals["rows"] += stats.get("rows", 0)
                    totals["stocks"] += stats.get("synced", 0)
                    ckpt["done"].append(key)
                    ckpt["stats"] = ckpt.get("stats", {})
                    ckpt["stats"][key] = {"rows": stats.get("rows", 0),
                                          "stocks": stats.get("synced", 0)}
                    _write_ckpt(ckpt)
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"{year}年{month}月 股票采集失败: {e}")
                    ckpt["failures"][key] = str(e)
                    _write_ckpt(ckpt)
        else:
            # 不指定年份时: 逐股票采集 (旧行为)
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
                  "commodity_kline": 0, "commodity_greeks": 0, "months": []}

        # 按月采集 ETF/股指期权 (写入 opt:YYYYmMM checkpoint)
        max_month = _max_month_for_year(year) if year else 12
        for month in range(1, max_month + 1):
            key = f"opt:{year}m{month:02d}"
            if key in ckpt.get("done", []):
                logger.info(f"[{key}] 已完成，跳过")
                continue
            try:
                res = oc.collect_month(year, month)
                totals["rows"] += res.get("greeks_rows", 0)
                totals["contracts"] += res.get("etf_contracts", 0) + res.get("index_contracts", 0)
                totals["months"].append({"month": month, **res})
            except Exception as e:  # noqa: BLE001
                logger.warning(f"期权 {year}年{month}月采集失败: {e}")

        def _codes_col(df):
            if df is None or df.empty:
                return None
            return next((c for c in ("期权代码", "合约代码", "代码") if c in df.columns), None)

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

    # 分钟线聚合: 采了 M5 后, 重采样生成 M15/M30/H1/H4 (供日内/小时级策略)
    if with_minute:
        try:
            from ..aggregator import aggregate_all
            agg = aggregate_all()
            results["aggregated"] = agg
            logger.info(f"分钟线聚合完成: {agg}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"分钟线聚合失败: {e}")

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
