"""
统一数据仓库 API (DuckDB) — 查询 products/symbols/kline/macro/cross-market,
并触发采集任务。前缀 /api/v1/warehouse。

与旧 /api/v1/data-center (Parquet 缓存 + 实时取数) 并存:
- data-center: 实时按需取数 + 多源校验
- warehouse:   已落库的统一历史仓库 (设计文档 DuckDB schema)
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..storage.duckdb_store import get_store
from ..collectors import FuturesCollector
from ..history.collect_jobs import get_jobs
from ..history import full_downloader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/warehouse", tags=["warehouse"])


@router.get("/products")
async def list_products(asset_type: Optional[str] = None):
    """品种列表 (可按 asset_type 过滤)。"""
    store = get_store()
    if asset_type:
        df = store.query("SELECT * FROM products WHERE asset_type = ? ORDER BY code", [asset_type])
    else:
        df = store.query("SELECT * FROM products ORDER BY asset_type, code")
    return {"count": len(df), "products": df.to_dict("records")}


@router.get("/symbols")
async def list_symbols(product: Optional[str] = None, limit: int = 200):
    """合约列表 (可按品种过滤)。"""
    store = get_store()
    if product:
        df = store.query(
            """SELECT sy.* FROM symbols sy JOIN products p ON sy.product_id=p.product_id
               WHERE p.code = ? ORDER BY sy.code LIMIT ?""",
            [product.upper(), limit],
        )
    else:
        df = store.query("SELECT * FROM symbols ORDER BY symbol_id LIMIT ?", [limit])
    return {"count": len(df), "symbols": df.to_dict("records")}


@router.get("/kline")
async def get_kline(
    code: str = Query(..., description="合约代码 如 RB2510 / 600019.SH"),
    timeframe: str = Query("D1", description="M5/M15/M30/H1/H4/D1/W1/M1"),
    limit: int = Query(500, description="返回最大条数"),
    start: Optional[str] = Query(None, description="起始 YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="结束 YYYY-MM-DD"),
):
    """查询统一 kline 表。"""
    store = get_store()
    sid = store.query("SELECT symbol_id FROM symbols WHERE code = ?", [code.upper()])
    if sid.empty:
        raise HTTPException(404, f"未找到合约: {code}")
    symbol_id = int(sid.iloc[0]["symbol_id"])
    sql = ("SELECT datetime, open, high, low, close, volume, open_interest, settlement "
           "FROM kline WHERE symbol_id=? AND timeframe=?")
    params: list = [symbol_id, timeframe]
    if start:
        sql += " AND datetime >= ?"; params.append(start)
    if end:
        sql += " AND datetime <= ?"; params.append(end)
    sql += " ORDER BY datetime DESC LIMIT ?"; params.append(limit)
    df = store.query(sql, params).sort_values("datetime")
    return {
        "code": code.upper(), "timeframe": timeframe, "bars": len(df),
        "datetime": [str(d) for d in df["datetime"].tolist()],
        "open": df["open"].tolist(), "high": df["high"].tolist(),
        "low": df["low"].tolist(), "close": df["close"].tolist(),
        "volume": df["volume"].tolist(),
        "open_interest": df["open_interest"].tolist(),
    }


@router.get("/macro")
async def get_macro(code: str = Query(..., description="宏观指标 如 CPI/PMI/M2")):
    """查询宏观指标时间序列。"""
    store = get_store()
    df = store.query(
        """SELECT md.date, md.value, md.value_yoy, md.unit FROM macro_data md
           JOIN products p ON md.product_id=p.product_id
           WHERE p.code = ? ORDER BY md.date""",
        [code.upper()],
    )
    return {"code": code.upper(), "points": len(df),
            "date": [str(d) for d in df["date"].tolist()],
            "value": df["value"].tolist()}


@router.get("/cross-market")
async def get_cross_market():
    """跨市场映射关系 (含相关系数)。"""
    store = get_store()
    df = store.query(
        """SELECT pa.code AS product_a, pb.code AS product_b, m.relation_type,
                  m.logic_desc, m.corr_20d, m.corr_60d, m.lead_lag_corr, m.lag_days
           FROM cross_market_mapping m
           JOIN products pa ON m.product_id_a=pa.product_id
           JOIN products pb ON m.product_id_b=pb.product_id
           WHERE m.status='active'"""
    )
    return {"count": len(df), "mappings": df.to_dict("records")}


@router.get("/stats")
async def warehouse_stats():
    """仓库总体统计。"""
    store = get_store()
    by_tf = store.query(
        "SELECT timeframe, count(*) bars, count(DISTINCT symbol_id) symbols FROM kline GROUP BY timeframe"
    )
    by_asset = store.query(
        """SELECT p.asset_type, count(DISTINCT sy.symbol_id) symbols
           FROM symbols sy JOIN products p ON sy.product_id=p.product_id GROUP BY p.asset_type"""
    )
    return {
        "products": int(store.query("SELECT count(*) n FROM products").iloc[0]["n"]),
        "symbols": int(store.query("SELECT count(*) n FROM symbols").iloc[0]["n"]),
        "kline_rows": int(store.query("SELECT count(*) n FROM kline").iloc[0]["n"]),
        "macro_rows": int(store.query("SELECT count(*) n FROM macro_data").iloc[0]["n"]),
        "by_timeframe": by_tf.to_dict("records"),
        "by_asset_type": by_asset.to_dict("records"),
    }


# ========== 采集 (写仓库) ==========

@router.get("/contracts/discover")
async def discover_contracts(product: str = Query(..., description="期货品种代码 如 RB")):
    """枚举某品种当前真实子合约 (RB2607/2608/...), 标出主力。"""
    fc = FuturesCollector()
    codes, main = fc._discover(product.upper())
    return {
        "product": product.upper(), "count": len(codes), "main_contract": main,
        "contracts": [{"code": c, "is_main": c == main} for c in codes],
    }


@router.post("/collect/product")
async def collect_product(
    product: str = Query(..., description="期货品种代码 如 RB"),
    year: Optional[int] = Query(None, description="年份 如 2026, 留空=当前在交易的合约"),
    end_year: Optional[int] = Query(None, description="结束年份 (与 year 组成区间, 留空=仅 year 一年)"),
    with_minute: bool = Query(False, description="是否同时采集 M5 分钟线"),
    start_date: Optional[str] = Query(None, description="起始日期 YYYY-MM-DD, 只保留之后数据"),
):
    """采集某品种合约到仓库 (后台任务)。
    指定 year: 枚举该年(或 year~end_year 区间)全部12个月合约 (M2601~M2612)。
    不指定 year: 采集当前在交易的真实合约 (实时枚举)。不判断主力。"""
    jobs = get_jobs()
    name = f"collect:{product.upper()}:{year or 'live'}"
    try:
        jobs.start(name, lambda: _collect_one_product(
            product.upper(), year, end_year, with_minute, start_date))
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"status": "started", "job": name, "product": product.upper(),
            "year": year, "end_year": end_year, "with_minute": with_minute}


async def _collect_one_product(product: str, year: Optional[int], end_year: Optional[int],
                               with_minute: bool, start_date: Optional[str]):
    import asyncio
    return await asyncio.to_thread(
        full_downloader.collect_futures_product, product, year, end_year, with_minute, start_date
    )


@router.post("/main-contracts/refresh")
async def refresh_main_contracts(
    product: Optional[str] = Query(None, description="品种代码, 留空=刷新所有期货品种"),
):
    """按实时持仓量重算主力合约并写 main_contracts 表 (独立于下载, 供交易流程查询)。"""
    fc = FuturesCollector()
    store = get_store()
    if product:
        products = [product.upper()]
    else:
        df = store.query("SELECT code FROM products WHERE asset_type='futures' ORDER BY code")
        products = df["code"].tolist()
    import asyncio
    result = {}
    for p in products:
        try:
            main = await asyncio.to_thread(fc.refresh_main_contract, p)
            result[p] = main
        except Exception as e:  # noqa: BLE001
            logger.warning(f"刷新主力 {p} 失败: {e}")
            result[p] = None
    return {"count": len(result), "main_contracts": result}


@router.get("/main-contracts")
async def list_main_contracts():
    """查询已记录的主力合约。"""
    store = get_store()
    df = store.query(
        """SELECT p.code product, m.symbol_code main, m.updated_at
           FROM main_contracts m JOIN products p ON m.product_id=p.product_id
           ORDER BY p.code"""
    )
    return {"count": len(df), "main_contracts": df.to_dict("records")}


@router.post("/collect/full")
async def collect_full(
    phase: str = Query("all", description="futures/stocks/options/all"),
    year: Optional[int] = Query(None, description="期货起始年份 如 2026"),
    end_year: Optional[int] = Query(None, description="期货结束年份 (区间)"),
    start_date: Optional[str] = Query(None, description="起始日期 YYYY-MM-DD, 留空=测试默认近1月"),
    with_minute: bool = Query(False, description="期货是否采集 M5"),
    stock_limit: Optional[int] = Query(50, description="股票测试限量(前N只), 生产传0=全市场"),
):
    """触发全量/批量采集 (后台任务)。测试环境默认只下近1个月、股票限前50只。"""
    if phase not in ("futures", "stocks", "options", "all"):
        raise HTTPException(400, f"无效阶段: {phase}")
    sd = start_date or full_downloader.default_test_start()
    limit = None if (stock_limit is not None and stock_limit <= 0) else stock_limit
    jobs = get_jobs()
    name = f"collect-full:{phase}:{year or sd}"
    try:
        jobs.start(name, lambda: full_downloader.run_full(
            phase, year, end_year, sd, with_minute, limit))
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"status": "started", "job": name, "phase": phase,
            "year": year, "end_year": end_year, "start_date": sd, "stock_limit": limit}


@router.get("/collect/progress")
async def collect_progress():
    """采集任务进度 + checkpoint 统计。"""
    state = get_jobs().status()
    ckpt = full_downloader._read_ckpt()
    return {
        "job": state,
        "checkpoint": {
            "done": len(ckpt.get("done", [])),
            "failures": len(ckpt.get("failures", {})),
            "recent_stats": dict(list(ckpt.get("stats", {}).items())[-10:]),
        },
    }


@router.get("/preview")
async def preview_warehouse(
    code: str = Query(..., description="合约代码 如 RB2609 / 600019.SH"),
    timeframe: str = Query("D1", description="M5/M15/M30/H1/D1/W1/M1"),
    limit: int = Query(200, le=2000),
):
    """从仓库读取 K 线 + 数据质量检查 (用于校验下载数据)。"""
    store = get_store()
    sid = store.query("SELECT symbol_id FROM symbols WHERE code = ?", [code.upper()])
    if sid.empty:
        raise HTTPException(404, f"仓库中未找到合约: {code}")
    symbol_id = int(sid.iloc[0]["symbol_id"])
    df = store.query(
        """SELECT datetime, open, high, low, close, volume, open_interest
           FROM kline WHERE symbol_id=? AND timeframe=? ORDER BY datetime""",
        [symbol_id, timeframe],
    )
    if df.empty:
        raise HTTPException(404, f"{code} {timeframe} 无数据")

    close = df["close"]
    high, low = df["high"], df["low"]
    quality = {
        "rows": int(len(df)),
        "start": str(df["datetime"].iloc[0]),
        "end": str(df["datetime"].iloc[-1]),
        "nan_close": int(close.isna().sum()),
        "zero_close": int((close == 0).sum()),
        "negative_values": int((close < 0).sum() + (low < 0).sum()),
        "high_lt_low": int((high < low).sum()),
        "duplicate_timestamps": int(df["datetime"].duplicated().sum()),
    }
    quality["is_clean"] = (quality["nan_close"] == 0 and quality["negative_values"] == 0
                           and quality["high_lt_low"] == 0 and quality["duplicate_timestamps"] == 0)

    head = df.tail(limit)
    rows = [
        {"datetime": str(r.datetime), "open": _f(r.open), "high": _f(r.high),
         "low": _f(r.low), "close": _f(r.close), "volume": _f(r.volume)}
        for r in head.itertuples()
    ]
    return {
        "code": code.upper(), "timeframe": timeframe, "total": int(len(df)),
        "quality": quality, "rows": rows,
        "chart": {"datetime": [str(d) for d in df["datetime"].tolist()],
                  "close": [_f(x) for x in close.tolist()]},
    }


def _f(v):
    """DECIMAL/NaN -> float/None (JSON 安全)。"""
    if v is None:
        return None
    try:
        f = float(v)
        return None if f != f else f
    except (TypeError, ValueError):
        return None
