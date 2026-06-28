"""
统一数据仓库 API (DuckDB) — 查询 products/symbols/kline/macro/cross-market,
并触发采集任务。前缀 /api/v1/warehouse。

与旧 /api/v1/data-center (Parquet 缓存 + 实时取数) 并存:
- data-center: 实时按需取数 + 多源校验
- warehouse:   已落库的统一历史仓库 (设计文档 DuckDB schema)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from ..history.collect_jobs import get_jobs
from . import _scheduler

from fastapi import APIRouter, HTTPException, Query

from ..storage.duckdb_store import get_store
from ..collectors import FuturesCollector
from ..history.collect_jobs import get_jobs
from ..history import full_downloader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/warehouse", tags=["warehouse"])


def _clean_json(obj):
    """递归把 NaN/Inf 替换为 None (Starlette JSONResponse 不接受非法 float)。"""
    import math
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _clean_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_json(v) for v in obj]
    return obj


def _records(df):
    """DataFrame -> JSON 安全的 records (NaN/Inf -> None)。"""
    return _clean_json(df.to_dict("records"))


@router.get("/products")
async def list_products(asset_type: Optional[str] = None):
    """品种列表 (可按 asset_type 过滤)。"""
    store = get_store()
    if asset_type:
        df = store.query("SELECT * FROM products WHERE asset_type = ? ORDER BY code", [asset_type])
    else:
        df = store.query("SELECT * FROM products ORDER BY asset_type, code")
    return {"count": len(df), "products": _records(df)}


@router.get("/symbols")
async def list_symbols(product: Optional[str] = None, limit: int = 200):
    """合约列表 (可按品种过滤), 含合约状态(在挂/已到期/连续)。"""
    from ..knowledge.contract_lifecycle import status as life_status
    store = get_store()
    if product:
        df = store.query(
            """SELECT sy.* FROM symbols sy JOIN products p ON sy.product_id=p.product_id
               WHERE p.code = ? ORDER BY sy.code LIMIT ?""",
            [product.upper(), limit],
        )
    else:
        df = store.query("SELECT * FROM symbols ORDER BY symbol_id LIMIT ?", [limit])
    rows = _records(df)
    for r in rows:
        r["status"] = life_status(str(r.get("code", "")))
    return {"count": len(rows), "symbols": rows}


@router.get("/contracts/status")
async def contract_status(code: str = Query(..., description="合约代码 如 M2609 / 10011251")):
    """单合约状态 (在挂/已到期/连续) + 到期日 + 有效数据窗口。期货期权统一。"""
    from ..knowledge.contract_lifecycle import status as life_status, parse_expiry, lifecycle_window
    exp = parse_expiry(code)
    win = lifecycle_window(code)
    return {
        "code": code.upper(),
        "status": life_status(code),
        "expire_date": str(exp) if exp else None,
        "valid_window": {"earliest": str(win[0]), "expire": str(win[1])} if win else None,
    }


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
    return {"count": len(df), "mappings": _records(df)}


@router.post("/options/greeks/commodity")
async def collect_commodity_greeks(
    exchange: str = Query(..., description="大商所/郑商所/上期所"),
    symbol_cn: str = Query(..., description="品种中文名 如 豆粕期权"),
    trade_date: Optional[str] = Query(None, description="交易日 YYYYMMDD, 留空=当日"),
):
    """商品期权 Greeks/IV (Black76 自算, akshare 不直接提供) -> options_daily。
    需标的期货 D1 收盘已在仓库 (先采集对应期货)。"""
    from ..collectors import OptionsCollector
    import asyncio
    oc = OptionsCollector()
    try:
        n = await asyncio.to_thread(
            oc.collect_commodity_greeks, exchange, symbol_cn, trade_date or "")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"商品期权 Greeks 采集失败: {e}")
    return {"exchange": exchange, "symbol": symbol_cn, "trade_date": trade_date,
            "rows_written": n}


@router.get("/options/greeks")
async def get_options_greeks(
    code: Optional[str] = Query(None, description="期权合约代码, 留空=全部最近"),
    limit: int = Query(200, description="返回最大条数"),
):
    """查询 options_daily 的 Greeks/IV。"""
    store = get_store()
    if code:
        df = store.query(
            """SELECT od.*, sy.code FROM options_daily od
               JOIN symbols sy ON od.symbol_id=sy.symbol_id
               WHERE sy.code = ? ORDER BY od.date DESC LIMIT ?""",
            [code.upper(), limit],
        )
    else:
        df = store.query(
            """SELECT od.date, sy.code, od.iv, od.delta, od.gamma, od.vega,
                      od.theta, od.rho, od.underlying_close FROM options_daily od
               JOIN symbols sy ON od.symbol_id=sy.symbol_id
               ORDER BY od.date DESC, sy.code LIMIT ?""",
            [limit],
        )
    return {"count": len(df), "greeks": _records(df)}


# ========== 一键同步最新 ==========

@router.get("/sync/latest")
async def sync_latest(
    asset_types: Optional[str] = Query(None, description="资产类型逗号分隔, 留空=全部 futures,stock,option"),
    buffer_days: int = Query(5, description="容忍落后天数, 超过才触发同步"),
    start_days: int = Query(180, description="同步回溯天数 (默认180=近6个月)"),
    with_minute: bool = Query(True, description="是否同步分钟线M5并聚合M15/M30/H1/H4"),
):
    """一键同步到最新 — 自动检测各资产最后数据日期,
    只对落后超过 buffer_days 的品种触发增量同步。

    - start_days: 日线回溯天数，默认180天(近6个月)
    - with_minute: 是否同步M5并聚合M15/M30/H1/H4
    - 同步完成后自动开启5分钟实时同步 (SyncScheduler)
    """
    from datetime import datetime, timedelta as _td
    store = get_store()

    targets = asset_types.split(",") if asset_types else ["futures", "stock", "option"]
    result = {}

    for asset in targets:
        if asset not in ("futures", "stock", "option"):
            continue
        if asset in ("futures", "option"):
            latest_row = store.query(
                """SELECT MAX(k.datetime) AS latest FROM kline k
                   JOIN symbols sy ON k.symbol_id=sy.symbol_id
                   JOIN products p ON sy.product_id=p.product_id
                   WHERE p.asset_type=?""",
                [asset],
            )
        else:
            latest_row = store.query(
                """SELECT MAX(k.datetime) AS latest FROM kline k
                   JOIN symbols sy ON k.symbol_id=sy.symbol_id
                   JOIN products p ON sy.product_id=p.product_id
                   WHERE p.asset_type='stock'"""
            )
        import pandas as pd
        latest_dt = latest_row.iloc[0]["latest"] if not latest_row.empty else None
        today = datetime.now().date()
        if latest_dt is not None and not pd.isna(latest_dt):
            latest_date = latest_dt.date() if hasattr(latest_dt, "date") else latest_dt
        else:
            latest_date = None
        days_behind = (today - latest_date).days if latest_date else 999
        result[asset] = {
            "latest_date": str(latest_date) if latest_date else None,
            "days_behind": days_behind,
            "need_sync": days_behind > buffer_days,
        }

    # 只要有任何资产需要同步，就触发一个合并任务（期货→股票→期权顺序执行）
    need_any = any(v["need_sync"] for v in result.values())
    if need_any:
        try:
            jobs = get_jobs()
            start = (datetime.now() - _td(days=start_days)).strftime("%Y-%m-%d")
            jobs.start("sync-latest:all", asyncio.coroutine(
                lambda s=start, w=with_minute, t=targets:
                    _do_futures_incremental(s, w,
                        include_stock="stock" in t, include_option="option" in t)))
            for asset in result:
                result[asset]["sync_triggered"] = result[asset]["need_sync"]
                if result[asset]["sync_triggered"]:
                    result[asset]["job"] = "sync-latest:all"
        except RuntimeError as e:
            for asset in result:
                result[asset]["sync_triggered"] = False
                result[asset]["detail"] = f"任务冲突: {e}"
            result[asset]["detail"] = "数据已最新"

    return {"assets": result, "today": str(today)}


@router.get("/jobs/status")
async def jobs_status():
    """当前后台采集任务状态，供前端轮询进度。"""
    return get_jobs().status()


async def _do_futures_incremental(start: str, with_minute: bool = True,
                             include_stock: bool = True, include_option: bool = True):
    """后台执行期货/股票/期权品种增量同步。同步完成后聚合分钟线到更高周期，并开启5分钟实时同步。"""
    import asyncio
    from ..aggregator import aggregate_all
    from ..collectors import FuturesCollector, StocksCollector, OptionsCollector
    from ..fetchers.akshare_fetcher import AKShareFetcher
    from . import _scheduler
    from ..storage.duckdb_store import get_store
    fc = FuturesCollector()
    store = get_store()

    # 确保期货产品在数据库中 (从FUTURES_SYMBOL_MAP填充)
    product_map = AKShareFetcher.FUTURES_SYMBOL_MAP
    for code, meta in product_map.items():
        existing = store.query("SELECT product_id FROM products WHERE code = ? AND asset_type = 'futures'", [code])
        if existing.empty:
            try:
                store.execute(
                    "INSERT INTO products (code, name, exchange, asset_type) VALUES (?, ?, ?, 'futures')",
                    [code, meta["name"], meta["exchange"]]
                )
                logger.info(f"[sync-latest] 添加期货产品: {code} {meta['name']}")
            except Exception as e:
                logger.warning(f"[sync-latest] 添加期货产品 {code} 失败: {e}")

    products = store.query("SELECT code FROM products WHERE asset_type='futures'")
    synced, failed = 0, 0
    for _, row in products.iterrows():
        code = row["code"]
        try:
            fc.collect_product(code, with_minute, 0.3, start)
            synced += 1
        except Exception as e:
            logger.warning(f"[sync-latest] 期货 {code} 失败: {e}")
            failed += 1

    # 股票 - 在线程池中运行以免阻塞事件循环
    stock_synced = 0
    if include_stock:
        def _sync_stocks():
            sc = StocksCollector()
            return sc.incremental_sync(symbols=None, buffer_days=5, full_start=start)
        try:
            loop = asyncio.get_event_loop()
            stock_synced = await loop.run_in_executor(None, _sync_stocks)
            logger.info(f"[sync-latest] 股票增量同步完成, {stock_synced} 条")
        except Exception as e:
            logger.warning(f"[sync-latest] 股票增量同步失败: {e}")

    # 期权 - 在线程池中运行 (使用希腊值快照)
    option_synced = 0
    if include_option:
        def _sync_options():
            oc = OptionsCollector()
            # collect_greeks_snapshot 获取全市场ETF/股指期权希腊值快照
            return oc.collect_greeks_snapshot()
        try:
            loop = asyncio.get_event_loop()
            option_synced = await loop.run_in_executor(None, _sync_options)
            logger.info(f"[sync-latest] 期权希腊值快照完成: {option_synced}")
        except Exception as e:
            logger.warning(f"[sync-latest] 期权同步失败: {e}")

    agg_result = aggregate_all(store)
    logger.info(f"[sync-latest] 全部同步完成, 期货 {synced}/{failed}, 股票 {stock_synced}, 期权 {option_synced}, 聚合 {agg_result}")

    # 自动开启5分钟实时同步: 添加所有期货品种 (后台运行，不阻塞)
    try:
        scheduler = _scheduler
        for _, row in products.iterrows():
            scheduler.add_symbol(row["code"], "futures", with_minute=with_minute, sync_seconds=300)
        # start() 创建后台任务，不 await (调度器有无限循环)
        asyncio.create_task(scheduler.start())
        logger.info(f"[sync-latest] 已将 {synced} 个期货品种加入5分钟实时同步调度器")
    except Exception as e:
        logger.warning(f"[sync-latest] 开启实时同步失败: {e}")

    return {"futures": {"synced": synced, "failed": failed},
            "stock": stock_synced, "option": option_synced,
            "aggregated": agg_result}


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
        "by_timeframe": _records(by_tf),
        "by_asset_type": _records(by_asset),
    }


@router.get("/db-size")
async def db_physical_size():
    """DuckDB 仓库物理文件大小 (含 WAL)。"""
    import os
    from ..storage.duckdb_store import _DEFAULT_DB
    base = str(_DEFAULT_DB)
    files = {}
    total = 0
    for suffix in ("", ".wal"):
        p = base + suffix
        if os.path.exists(p):
            sz = os.path.getsize(p)
            files[os.path.basename(p)] = round(sz / (1024 * 1024), 2)
            total += sz
    return {"path": base, "total_mb": round(total / (1024 * 1024), 2), "files": files}


# ========== 按年同步面板 (生产) ==========

# 同步面板覆盖年份: 当前年倒推至此
_SYNC_MIN_YEAR = 2015


@router.get("/sync/year-status")
async def sync_year_status():
    """按年 × 资产类型 的同步状态 (一年一行, 倒序)。

    状态推导自仓库实有数据:
    - 期货/期权: 按 symbols.contract_year 统计该年合约数 + 有K线的合约数
    - 股票: 按该年有 D1 数据的股票数
    同步中: 若有采集任务正在跑且任务名含该年/资产, 标注 running + checkpoint 进度。
    """
    from datetime import datetime
    store = get_store()

    # 期货/期权: 按合约年份
    contract_stat = store.query(
        """SELECT p.asset_type, sy.contract_year AS yr,
                  COUNT(DISTINCT sy.symbol_id) AS syms,
                  COUNT(DISTINCT CASE WHEN k.symbol_id IS NOT NULL THEN sy.symbol_id END) AS with_data
           FROM symbols sy JOIN products p ON sy.product_id=p.product_id
           LEFT JOIN kline k ON k.symbol_id=sy.symbol_id AND k.timeframe='D1'
           WHERE p.asset_type IN ('futures','option') AND sy.contract_year IS NOT NULL
           GROUP BY p.asset_type, sy.contract_year"""
    )
    # 股票: 按 K 线所属自然年
    stock_stat = store.query(
        """SELECT CAST(EXTRACT(year FROM k.datetime) AS INTEGER) AS yr,
                  COUNT(DISTINCT sy.symbol_id) AS with_data
           FROM kline k JOIN symbols sy ON k.symbol_id=sy.symbol_id
           JOIN products p ON sy.product_id=p.product_id
           WHERE p.asset_type='stock' AND k.timeframe='D1'
           GROUP BY EXTRACT(year FROM k.datetime)"""
    )

    fut = {int(r["yr"]): r for _, r in contract_stat[contract_stat["asset_type"] == "futures"].iterrows()}
    opt = {int(r["yr"]): r for _, r in contract_stat[contract_stat["asset_type"] == "option"].iterrows()}
    stk = {int(r["yr"]): int(r["with_data"]) for _, r in stock_stat.iterrows()}

    job = get_jobs().status()
    running_name = (job.get("name") or "") if job.get("running") else ""
    done = 0
    try:
        done = len(full_downloader._read_ckpt().get("done", []))
    except Exception:
        pass

    # 读取 checkpoint 获取已完成的月份
    try:
        ckpt = full_downloader._read_ckpt()
        ckpt_done = set(ckpt.get("done", []))
    except:
        ckpt_done = set()

    def _cell(asset: str, year: int):
        if asset == "stock":
            wd = stk.get(year, 0)
            syms = wd
        else:
            row = (fut if asset == "futures" else opt).get(year)
            if row is not None:
                syms = int(row["syms"])
                wd = int(row["with_data"])
            else:
                # 期权可能没有 contract_year，用总量兜底
                if asset == "option":
                    total_opt = store.query(
                        "SELECT COUNT(*) AS cnt FROM symbols sy JOIN products p ON sy.product_id=p.product_id WHERE p.asset_type='option'"
                    )
                    syms = int(total_opt.iloc[0]["cnt"]) if len(total_opt) else 0
                    # 检查有K线的期权合约数
                    has_kline = store.query(
                        "SELECT COUNT(DISTINCT k.symbol_id) AS cnt FROM kline k JOIN symbols sy ON k.symbol_id=sy.symbol_id JOIN products p ON sy.product_id=p.product_id WHERE p.asset_type='option' AND k.timeframe='D1'"
                    )
                    wd = int(has_kline.iloc[0]["cnt"]) if len(has_kline) else 0
                else:
                    syms = 0
                    wd = 0
        running = bool(running_name) and (str(year) in running_name) and (asset in running_name)
        if running:
            status = "同步中"
        elif wd > 0:
            status = "已同步"
        else:
            status = "未同步"

        # 获取每个月状态 (检查多种 key 格式)
        months = {}
        for m in range(1, 13):
            # 检查不同资产类型的 checkpoint key 格式
            # 格式: stock → stk:YYYYmMM, option → option:YYYYmMM, futures → fut:XXX:YYYYmMM
            keys_to_check = [f"{asset}:{year}m{m:02d}"]
            # 兼容旧格式
            if asset == "stock":
                keys_to_check.append(f"stk:{year}m{m:02d}")
            if asset == "option":
                keys_to_check.append(f"opt:{year}m{m:02d}")
            # 期货额外检查 fut:XXX:YYYYmMM 格式 (尝试常见品种)
            if asset == "futures":
                for p in ["RB", "IF", "IC", "IH", "IM", "TA", "MA", "RM", "M", "Y", "P", "J", "JM"]:
                    keys_to_check.append(f"fut:{p}:{year}m{m:02d}")
            month_done = any(k in ckpt_done for k in keys_to_check)
            months[m] = {"done": month_done}

        return {"status": status, "contracts": syms, "with_data": wd,
                "checkpoint_done": done if running else None, "months": months}

    cur = datetime.now().year
    years = []
    for y in range(cur, _SYNC_MIN_YEAR - 1, -1):   # 倒序
        years.append({
            "year": y,
            "futures": _cell("futures", y),
            "stock": _cell("stock", y),
            "option": _cell("option", y),
        })
    return {"years": years, "running": running_name or None,
            "running_done": done if running_name else None}


@router.post("/sync/year")
async def sync_year(
    asset_type: str = Query(..., description="futures/stock/option"),
    year: int = Query(..., description="同步年份 如 2026"),
    reset_checkpoint: bool = Query(False, description="复跑前清空进度 (校验补漏)"),
    with_minute: bool = Query(False, description="同采分钟线 M5 并聚合 M15/M30/H1/H4 (近月, 日内策略用)"),
):
    """按年同步某资产类型 (后台任务, 断点续传)。具体合约, 生命周期守卫保证挂牌/交割范围。

    with_minute=True: D1 走全年 + M5 采近月并自动聚合 M15/M30/H1/H4 (日内/小时级策略数据)。
    """
    if asset_type not in ("futures", "stock", "option"):
        raise HTTPException(400, f"无效资产类型: {asset_type}")
    start_date = f"{year}-01-01"
    jobs = get_jobs()
    name = f"sync-year:{asset_type}:{year}"

    # 期权使用按月同步函数 (写 opt:YYYYmMM checkpoint)
    if asset_type == "option":
        try:
            jobs.start(name, lambda: full_downloader.run_full_options_year(year, reset_checkpoint))
        except RuntimeError as e:
            raise HTTPException(409, str(e))
    else:
        try:
            jobs.start(name, lambda: full_downloader.run_full(
                asset_type, year, year, start_date, with_minute, None, reset_checkpoint))
        except RuntimeError as e:
            raise HTTPException(409, str(e))

    return {"status": "started", "job": name, "asset_type": asset_type,
            "year": year, "reset_checkpoint": reset_checkpoint, "with_minute": with_minute}


@router.post("/sync/month")
async def sync_month(
    asset_type: str = Query(..., description="futures/stock/option"),
    year: int = Query(..., description="同步年份"),
    month: int = Query(..., description="同步月份 1-12"),
    product: Optional[str] = Query(None, description="期货品种代码 (futures 时必填)"),
    reset_checkpoint: bool = Query(False, description="复跑前清空该月进度"),
    with_minute: bool = Query(False, description="是否同步 M5 分钟线"),
):
    """按月同步某资产类型。期货按品种按月处理，股票和期权也支持按月。

    用途:
    - 期货: 指定 product + year + month，按月处理避免长任务中断
    - 股票: 按月采集全市场日线数据
    - 期权: 按月采集 ETF/股指期权 Greeks 快照
    """
    if asset_type == "futures":
        if not product:
            raise HTTPException(400, "期货同步必须指定 product 品种代码")
        if month < 1 or month > 12:
            raise HTTPException(400, "month 必须为 1-12")
        jobs = get_jobs()
        name = f"sync-month:{asset_type}:{product}:{year}m{month:02d}"
        try:
            async def _do_month():
                return await asyncio.to_thread(
                    full_downloader.collect_futures_product_month,
                    product.upper(), year, month, with_minute, 0.3, None
                )
            jobs.start(name, _do_month)
        except RuntimeError as e:
            raise HTTPException(409, str(e))
        return {"status": "started", "job": name, "asset_type": asset_type,
                "product": product.upper(), "year": year, "month": month}

    elif asset_type == "stock":
        if month < 1 or month > 12:
            raise HTTPException(400, "month 必须为 1-12")
        jobs = get_jobs()
        name = f"sync-month:stock:{year}m{month:02d}"
        try:
            async def _do_stock():
                return await asyncio.to_thread(
                    full_downloader.collect_stocks_month, year, month, None, None
                )
            jobs.start(name, _do_stock)
        except RuntimeError as e:
            raise HTTPException(409, str(e))
        return {"status": "started", "job": name, "asset_type": asset_type,
                "year": year, "month": month}

    elif asset_type == "option":
        if month < 1 or month > 12:
            raise HTTPException(400, "month 必须为 1-12")
        jobs = get_jobs()
        name = f"sync-month:option:{year}m{month:02d}"
        try:
            from ..collectors import OptionsCollector
            async def _do_option():
                return await asyncio.to_thread(
                    OptionsCollector().collect_month, year, month
                )
            jobs.start(name, _do_option)
        except RuntimeError as e:
            raise HTTPException(409, str(e))
        return {"status": "started", "job": name, "asset_type": asset_type,
                "year": year, "month": month}

    raise HTTPException(400, f"无效资产类型: {asset_type}")


@router.post("/sync/stocks-year")
async def sync_stocks_year(
    year: int = Query(..., description="同步年份 如 2026"),
    reset_checkpoint: bool = Query(False, description="复跑前清空进度 (校验补漏)"),
    stock_limit: Optional[int] = Query(None, description="限制采集数量 (测试用)"),
):
    """按年同步股票数据（12个月，后台逐月处理，断点续传）。

    用途: 补历史数据时按月分批，避免长任务中断后重复采集。
    stock_limit: 测试用，只下前 N 只股票。
    """
    jobs = get_jobs()
    name = f"sync-year:stock:{year}"
    try:
        jobs.start(name, lambda: full_downloader.run_full_stocks_year(
            year, stock_limit, reset_checkpoint))
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"status": "started", "job": name, "asset_type": "stock",
            "year": year, "stock_limit": stock_limit,
            "reset_checkpoint": reset_checkpoint}


@router.get("/sync/year/verify")
async def verify_year(
    asset_type: str = Query(..., description="futures/stock/option"),
    year: int = Query(..., description="校验年份"),
):
    """校验某资产某年已入库数据的质量 (条数/缺口/NaN/重复)。"""
    store = get_store()
    asset = asset_type
    if asset == "stock":
        rows = store.query(
            """SELECT sy.code, COUNT(*) bars, MIN(k.datetime) mn, MAX(k.datetime) mx,
                      SUM(CASE WHEN k.close IS NULL THEN 1 ELSE 0 END) nan_close
               FROM symbols sy JOIN products p ON sy.product_id=p.product_id
               JOIN kline k ON k.symbol_id=sy.symbol_id AND k.timeframe='D1'
               WHERE p.asset_type='stock'
                 AND CAST(EXTRACT(year FROM k.datetime) AS INTEGER)=?
               GROUP BY sy.code ORDER BY sy.code""",
            [year],
        )
    elif asset == "option":
        # ETF 期权无 contract_year, 用 kline.datetime 过滤
        sql = """SELECT sy.code, COUNT(*) bars, MIN(k.datetime) mn, MAX(k.datetime) mx,
                      SUM(CASE WHEN k.close IS NULL THEN 1 ELSE 0 END) nan_close
               FROM symbols sy JOIN products p ON sy.product_id=p.product_id
               JOIN kline k ON k.symbol_id=sy.symbol_id AND k.timeframe='D1'
               WHERE p.asset_type='option'
                 AND CAST(EXTRACT(year FROM k.datetime) AS INTEGER)=?
               GROUP BY sy.code ORDER BY sy.code"""
        rows = store.query(sql, [year])
    else:
        # 期货用 contract_year 精确匹配
        rows = store.query(
            """SELECT sy.code, COUNT(*) bars, MIN(k.datetime) mn, MAX(k.datetime) mx,
                      SUM(CASE WHEN k.close IS NULL THEN 1 ELSE 0 END) nan_close
               FROM symbols sy JOIN products p ON sy.product_id=p.product_id
               JOIN kline k ON k.symbol_id=sy.symbol_id AND k.timeframe='D1'
               WHERE p.asset_type='futures' AND sy.contract_year=?
               GROUP BY sy.code ORDER BY sy.code""",
            [year],
        )
    total_syms = len(rows)
    total_bars = int(rows["bars"].sum()) if total_syms else 0
    nan_total = int(rows["nan_close"].sum()) if total_syms else 0
    empty = int((rows["bars"] == 0).sum()) if total_syms else 0
    return {
        "asset_type": asset, "year": year,
        "symbols": total_syms, "total_bars": total_bars,
        "nan_close": nan_total, "empty_symbols": empty,
        "is_clean": nan_total == 0 and empty == 0 and total_syms > 0,
        "samples": _records(rows.head(20)),
    }


# ========== 采集 (写仓库) ==========

@router.get("/sync/year/download")
async def download_year_data(
    asset_type: str = Query(..., description="futures/stock/option"),
    year: int = Query(..., description="下载年份"),
):
    """下载某资产某年已入库数据 (JSON)。用于数据校验/备份。"""
    store = get_store()
    asset = asset_type
    if asset in ("futures", "option"):
        rows = store.query(
            """SELECT sy.code as symbol, k.datetime, k.open, k.high, k.low, k.close, k.volume,
                      k.open_interest, k.timeframe, sy.code as contract_code
               FROM symbols sy JOIN products p ON sy.product_id=p.product_id
               JOIN kline k ON k.symbol_id=sy.symbol_id AND k.timeframe='D1'
               WHERE p.asset_type=? AND sy.contract_year=?
               ORDER BY sy.code, k.datetime""",
            [asset, year],
        )
    else:
        rows = store.query(
            """SELECT sy.code as symbol, k.datetime, k.open, k.high, k.low, k.close, k.volume,
                      k.open_interest, k.timeframe, sy.code
               FROM symbols sy JOIN products p ON sy.product_id=p.product_id
               JOIN kline k ON k.symbol_id=sy.symbol_id AND k.timeframe='D1'
               WHERE p.asset_type='stock'
                 AND CAST(EXTRACT(year FROM k.datetime) AS INTEGER)=?
               ORDER BY sy.code, k.datetime""",
            [year],
        )
    data = _records(rows)
    return {
        "asset_type": asset, "year": year,
        "total_bars": len(data),
        "symbols": int(rows["symbol"].nunique()) if len(data) > 0 else 0,
        "data": data,
    }


@router.get("/contracts/discover")
async def discover_contracts(product: str = Query(..., description="期货品种代码 如 RB")):
    """枚举某品种当前真实子合约 (RB2607/2608/...), 标出主力 + 合约状态(在挂/已到期)。"""
    from ..knowledge.contract_lifecycle import status as life_status, parse_expiry
    fc = FuturesCollector()
    codes, main = fc._discover(product.upper())
    return {
        "product": product.upper(), "count": len(codes), "main_contract": main,
        "contracts": [{"code": c, "is_main": c == main,
                       "status": life_status(c),
                       "expire_date": str(parse_expiry(c)) if parse_expiry(c) else None}
                      for c in codes],
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
    return {"count": len(df), "main_contracts": _records(df)}


# ========== 股票知识库 / 基本面 ==========

def _norm_stock_code(code: str) -> str:
    """归一化股票代码: 600019 / 600019.SH / sh600019 -> 600019.SH。
    6 位纯数字按首位补后缀 (6/9->SH, 0/3->SZ); 已带后缀则原样大写。"""
    c = code.strip().upper().replace("SH", "").replace("SZ", "").replace(".", "")
    if "." in code.upper():
        return code.strip().upper()
    if len(c) == 6 and c.isdigit():
        suffix = "SH" if c[0] in ("6", "9") else "SZ"
        return f"{c}.{suffix}"
    return code.strip().upper()


@router.get("/stocks/symbols")
async def list_stock_symbols(
    source: str = Query("warehouse", description="warehouse=已入库 / akshare=全市场实时枚举"),
    limit: int = Query(6000, description="返回上限"),
):
    """A 股代码列表。warehouse: 仓库已入库的; akshare: 全市场实时枚举 (含未下载)。"""
    if source == "akshare":
        from ..collectors import StocksCollector
        import asyncio
        codes = await asyncio.to_thread(StocksCollector().list_all_symbols)
        return {"source": "akshare", "count": len(codes), "symbols": codes[:limit]}
    store = get_store()
    df = store.query(
        """SELECT DISTINCT sy.code, sy.name FROM symbols sy
           JOIN products p ON sy.product_id=p.product_id
           WHERE p.asset_type='stock' ORDER BY sy.code LIMIT ?""",
        [limit],
    )
    return {"source": "warehouse", "count": len(df),
            "symbols": _records(df)}


@router.post("/stocks/fundamental/collect")
async def collect_stock_fundamental(
    symbol: str = Query(..., description="股票代码 如 600019.SH"),
):
    """采集个股信息 + 财务摘要 -> stocks_info / stocks_financial。"""
    from ..collectors import StocksCollector
    import asyncio
    sc = StocksCollector()
    code = _norm_stock_code(symbol)
    try:
        info_n = await asyncio.to_thread(sc.collect_info, code)
        fin_n = await asyncio.to_thread(sc.collect_financial, code)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"基本面采集失败: {e}")
    return {"symbol": code, "info_written": info_n, "financial_periods": fin_n}


@router.get("/stocks/fundamental")
async def get_stock_fundamental(symbol: str = Query(..., description="股票代码 600019 或 600019.SH")):
    """查询个股信息 + 财务历史 (K 线之外的分析维度)。"""
    store = get_store()
    code = _norm_stock_code(symbol)
    sid_df = store.query("SELECT symbol_id FROM symbols WHERE code = ?", [code])
    if sid_df.empty:
        raise HTTPException(404, f"未找到股票: {code}")
    sid = int(sid_df.iloc[0]["symbol_id"])
    info = store.query("SELECT * FROM stocks_info WHERE symbol_id = ?", [sid])
    fin = store.query(
        "SELECT * FROM stocks_financial WHERE symbol_id = ? ORDER BY report_date DESC", [sid])
    return _clean_json({
        "symbol": code,
        "info": info.iloc[0].to_dict() if not info.empty else None,
        "financial": fin.to_dict("records"),
    })


@router.get("/stocks/knowledge")
async def stock_knowledge(sector: Optional[str] = Query(None, description="行业名, 留空=全部")):
    """股票行业知识库 + 行业↔期货联动映射。"""
    from ..knowledge.stock_knowledge import get_stock_knowledge
    from dataclasses import asdict
    kb = get_stock_knowledge()
    if sector:
        s = kb.get_sector(sector)
        if not s:
            raise HTTPException(404, f"未找到行业: {sector}")
        return {"sector": asdict(s),
                "relations": [asdict(r) for r in kb.relations_for_sector(sector)]}
    return {
        "sectors": [asdict(s) for s in kb.list_sectors()],
        "relations": [asdict(r) for r in kb.all_relations()],
    }


@router.get("/options/knowledge")
async def options_knowledge(
    underlying: Optional[str] = Query(None, description="标的代码 如 510050/M, 留空=全部"),
    market_view: Optional[str] = Query(None, description="按市场判断荐策略: 大涨/小涨/震荡/小跌/大跌"),
):
    """期权标的市场特征 + 策略知识库。"""
    from ..knowledge.options_knowledge import get_options_knowledge
    from dataclasses import asdict
    kb = get_options_knowledge()
    if underlying:
        p = kb.get_product(underlying)
        if not p:
            raise HTTPException(404, f"未找到期权标的: {underlying}")
        return {"product": asdict(p)}
    strategies = (kb.strategies_for_view(market_view) if market_view
                  else kb.list_strategies())
    return {
        "products": [asdict(p) for p in kb.list_products()],
        "strategies": [asdict(s) for s in strategies],
    }


@router.post("/collect/full")
async def collect_full(
    phase: str = Query("all", description="futures/stocks/options/all"),
    year: Optional[int] = Query(None, description="期货起始年份 如 2026"),
    end_year: Optional[int] = Query(None, description="期货结束年份 (区间)"),
    start_date: Optional[str] = Query(None, description="起始日期 YYYY-MM-DD, 留空=测试默认近1月"),
    with_minute: bool = Query(False, description="期货是否采集 M5"),
    stock_limit: Optional[int] = Query(50, description="股票测试限量(前N只), 生产传0=全市场"),
    full_history: bool = Query(False, description="全量: 股票从上市日起全历史 (忽略start_date), 默认全市场"),
    reset_checkpoint: bool = Query(False, description="复跑前清空进度 (定期全量校验补漏)"),
):
    """触发全量/批量采集 (后台任务)。
    - 测试: 默认只下近1个月、股票限前50只。
    - 生产全量: full_history=True → 股票从上市日起全历史 + 全市场 (start_date/stock_limit 自动忽略),
      可配合 reset_checkpoint=True 定期复跑校验补漏。断点续传 + 单实例锁防限流/中断。"""
    if phase not in ("futures", "stocks", "options", "all"):
        raise HTTPException(400, f"无效阶段: {phase}")
    if full_history:
        sd = None              # 从上市日/最早可得起
        limit = None           # 全市场
    else:
        sd = start_date or full_downloader.default_test_start()
        limit = None if (stock_limit is not None and stock_limit <= 0) else stock_limit
    jobs = get_jobs()
    name = f"collect-full:{phase}:{'full' if full_history else (year or sd)}"
    try:
        jobs.start(name, lambda: full_downloader.run_full(
            phase, year, end_year, sd, with_minute, limit, reset_checkpoint))
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"status": "started", "job": name, "phase": phase, "full_history": full_history,
            "year": year, "end_year": end_year, "start_date": sd, "stock_limit": limit,
            "reset_checkpoint": reset_checkpoint}


@router.post("/collect/stocks/incremental")
async def collect_stocks_incremental(
    full_start: str = Query("2015-01-01", description="新票全量起始日"),
    buffer_days: int = Query(5, description="已入库票回补天数 (容忍前复权回填)"),
    limit: Optional[int] = Query(None, description="限量(前N只), 留空=全市场"),
):
    """股票增量同步 (后台任务): 只拉落后于最近交易日的票, 已最新的跳过。"""
    from ..collectors import StocksCollector

    def _run():
        sc = StocksCollector()
        syms = sc.list_all_symbols()
        if limit:
            syms = syms[:limit]
        return sc.incremental_sync(symbols=syms, buffer_days=buffer_days, full_start=full_start)

    jobs = get_jobs()
    try:
        jobs.start("stocks-incremental", _run)
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"status": "started", "job": "stocks-incremental",
            "full_start": full_start, "buffer_days": buffer_days, "limit": limit}


@router.get("/debug/option-kline")
async def debug_option_kline():
    """调试: 检查期权 kline 数据"""
    store = get_store()
    # 检查期权符号数
    opt_syms = store.query(
        "SELECT COUNT(*) n FROM symbols sy JOIN products p ON sy.product_id=p.product_id WHERE p.asset_type='option'"
    )
    # 检查有 kline 的期权符号数
    opt_with_kline = store.query(
        """SELECT COUNT(DISTINCT k.symbol_id) n FROM kline k
           JOIN symbols sy ON k.symbol_id=sy.symbol_id
           JOIN products p ON sy.product_id=p.product_id
           WHERE p.asset_type='option' AND k.timeframe='D1'"""
    )
    # 检查 kline.symbol_id 关联的 symbols.asset_type
    sample = store.query(
        """SELECT k.symbol_id, sy.code, p.asset_type, k.datetime
           FROM kline k
           JOIN symbols sy ON k.symbol_id=sy.symbol_id
           JOIN products p ON sy.product_id=p.product_id
           WHERE k.timeframe='D1'
           ORDER BY k.symbol_id DESC LIMIT 10"""
    )
    return {
        "option_symbols": int(opt_syms.iloc[0]["n"]) if not opt_syms.empty else 0,
        "option_with_kline": int(opt_with_kline.iloc[0]["n"]) if not opt_with_kline.empty else 0,
        "sample_kline_symbols": _records(sample),
    }


@router.get("/collect/progress")
async def collect_progress():
    """采集任务进度 + checkpoint 统计 + 当前处理项。"""
    state = get_jobs().status()
    ckpt = full_downloader._read_ckpt()
    done_list = ckpt.get("done", [])
    stats = ckpt.get("stats", {})

    # 从任务名解析当前处理项: "sync-year:futures:2026" -> asset=futures, year=2026
    running_name = state.get("name", "") or ""
    current_item = None
    if state.get("running") and running_name.startswith("sync-year:"):
        parts = running_name.split(":")
        if len(parts) >= 3:
            asset = parts[1]
            year = parts[2]
            # 从 stats 找最后一个完成的，解析产品名
            last_done = list(stats.keys())[-1] if stats else None
            current_product = None
            if last_done:
                segs = last_done.split(":")
                if len(segs) >= 2:
                    current_product = segs[1]
            current_item = {
                "asset": asset,
                "year": year,
                "total_done": len(done_list),
                "last_product": current_product,
            }

    return {
        "job": state,
        "checkpoint": {
            "done": len(done_list),
            "failures": len(ckpt.get("failures", {})),
            "recent_stats": dict(list(stats.items())[-10:]),
        },
        "current_item": current_item,
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


@router.get("/export")
async def export_warehouse(
    asset_type: str = Query(..., description="futures/stock/option"),
    year: int = Query(..., description="导出年份"),
    format: str = Query("csv", description="csv/xlsx/json"),
    symbol: Optional[str] = Query(None, description="指定合约代码, 留空=全品种"),
    timeframe: str = Query("D1", description="时间周期 D1/M5/M15/M30/H1/H4"),
    limit: int = Query(0, description="每品种最大条数, 0=全部"),
):
    """从仓库导出已下载数据 (支持期货/股票/期权)。"""
    import io
    import pandas as pd
    from fastapi.responses import StreamingResponse

    store = get_store()
    year_start = f"{year}-01-01"
    year_end = f"{year}-12-31"

    # 构建查询
    if asset_type == "stock":
        # 股票: 按K线所属年份
        sql = """
            SELECT sy.code AS symbol, k.datetime, k.open, k.high, k.low, k.close, k.volume, k.open_interest
            FROM kline k
            JOIN symbols sy ON k.symbol_id = sy.symbol_id
            JOIN products p ON sy.product_id = p.product_id
            WHERE p.asset_type = 'stock' AND k.timeframe = ?
            AND k.datetime >= ? AND k.datetime <= ?
        """
        params = [timeframe, year_start, year_end]
        if symbol:
            sql += " AND sy.code = ?"
            params.append(symbol.upper().replace(".SH", "").replace(".SZ", ""))
        sql += " ORDER BY sy.code, k.datetime"
    elif asset_type == "option":
        # 期权: Greeks数据
        sql = """
            SELECT sy.code AS symbol, k.datetime, k.open, k.high, k.low, k.close, k.volume, k.open_interest
            FROM kline k
            JOIN symbols sy ON k.symbol_id = sy.symbol_id
            JOIN products p ON sy.product_id = p.product_id
            WHERE p.asset_type = 'option' AND k.timeframe = ?
            AND k.datetime >= ? AND k.datetime <= ?
        """
        params = [timeframe, year_start, year_end]
        if symbol:
            sql += " AND sy.code = ?"
            params.append(symbol.upper())
        sql += " ORDER BY sy.code, k.datetime"
    else:
        # 期货: 按合约年份
        sql = """
            SELECT sy.code AS symbol, sy.contract_year AS year, k.datetime, k.open, k.high, k.low, k.close, k.volume, k.open_interest
            FROM kline k
            JOIN symbols sy ON k.symbol_id = sy.symbol_id
            JOIN products p ON sy.product_id = p.product_id
            WHERE p.asset_type = 'futures' AND k.timeframe = ?
            AND sy.contract_year = ?
        """
        params = [timeframe, year]
        if symbol:
            sql += " AND sy.code = ?"
            params.append(symbol.upper())
        sql += " ORDER BY sy.code, k.datetime"

    df = store.query(sql, params)
    if df.empty:
        raise HTTPException(404, f"无数据: {asset_type} {year} {timeframe}")

    # 限制条数
    if limit > 0:
        df = df.groupby("symbol", group_keys=False).apply(
            lambda x: x.tail(limit)
        ).reset_index(drop=True)

    # 生成文件
    if format == "xlsx":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=f"{asset_type}_{year}"[:31])
        buf.seek(0)
        fname = f"{asset_type}_{year}_{timeframe}.xlsx"
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )
    elif format == "json":
        import json
        fname = f"{asset_type}_{year}_{timeframe}.json"
        return StreamingResponse(
            io.StringIO(df.to_json(orient="records", date_format="iso")),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )
    else:
        # CSV
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        fname = f"{asset_type}_{year}_{timeframe}.csv"
        return StreamingResponse(
            buf,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )


def _f(v):
    """DECIMAL/NaN -> float/None (JSON 安全)。"""
    if v is None:
        return None
    try:
        f = float(v)
        return None if f != f else f
    except (TypeError, ValueError):
        return None
