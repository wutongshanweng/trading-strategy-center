"""
Data Center API 路由 — 提供数据中心全部功能接口。

API 端点:
GET    /api/v1/data-center/sources        — 数据源列表
GET    /api/v1/data-center/sources/health — 数据源健康状态
POST   /api/v1/data-center/kline          — 获取 K 线数据
POST   /api/v1/data-center/kline/verify   — 多数据源校验 K 线
GET    /api/v1/data-center/contracts/{symbol}  — 合约知识
POST   /api/v1/data-center/download       — 创建下载任务
GET    /api/v1/data-center/download/{task_id}  — 任务状态
GET    /api/v1/data-center/download/history    — 下载历史
POST   /api/v1/data-center/sync/start     — 启动同步
POST   /api/v1/data-center/sync/stop      — 停止同步
GET    /api/v1/data-center/sync/status    — 同步状态
GET    /api/v1/data-center/storage        — 存储统计
GET    /api/v1/data-center/exchanges      — 交易所列表
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..core.base_fetcher import KlineInterval
from ..core.data_source import DataSourceManager
from ..knowledge.main_contract import MainContractResolver
from ..knowledge.contract_knowledge import ContractKnowledgeBase
from ..history.download_manager import DownloadManager
from ..history.data_store import DataStore
from ..history.sync_scheduler import SyncScheduler
from ..verification.verifier import DataVerifier

logger = logging.getLogger(__name__)

# 全局实例 (单例)
_source_mgr = DataSourceManager()
_knowledge_base = ContractKnowledgeBase()
_main_contract = MainContractResolver()
_data_store = DataStore()
_dl_mgr = DownloadManager(_source_mgr)
_scheduler = SyncScheduler(_dl_mgr, _data_store)
_verifier = DataVerifier(_source_mgr)


# asset_type -> DataStore market 目录名
_MARKET_DIRS = {"futures": "futures", "stock": "stock", "option": "options"}


def _market_for(asset_type: str) -> str:
    return _MARKET_DIRS.get((asset_type or "futures").lower(), "futures")


def _register_default_fetchers() -> None:
    """注册所有可用数据源。无需密钥的优先注册；需密钥的仅在环境变量存在时注册。"""
    import os

    # 无需密钥 — 中国市场优先
    try:
        from ..fetchers.akshare_fetcher import AKShareFetcher
        _source_mgr.register(AKShareFetcher(), priority=10)
    except Exception as e:
        logger.warning(f"akshare 注册失败: {e}")
    try:
        from ..fetchers.tdx_fetcher import TDXFetcher
        _source_mgr.register(TDXFetcher(), priority=20)
    except Exception as e:
        logger.warning(f"tdx 注册失败: {e}")
    try:
        from ..fetchers.baostock_fetcher import BaoStockFetcher
        _source_mgr.register(BaoStockFetcher(), priority=30)
    except Exception as e:
        logger.warning(f"baostock 注册失败: {e}")
    try:
        from ..fetchers.options_fetcher import ChinaOptionsFetcher
        _source_mgr.register(ChinaOptionsFetcher(), priority=40)
    except Exception as e:
        logger.warning(f"china_options 注册失败: {e}")
    try:
        from ..fetchers.yfinance_fetcher import YFinanceFetcher
        _source_mgr.register(YFinanceFetcher(), priority=50)
    except Exception as e:
        logger.warning(f"yfinance 注册失败: {e}")

    # 需密钥/账户 — 仅在凭据存在时注册
    if os.getenv("TUSHARE_TOKEN"):
        try:
            from ..fetchers.tushare_fetcher import TushareFetcher
            _source_mgr.register(TushareFetcher(), priority=15)
        except Exception as e:
            logger.warning(f"tushare 注册失败: {e}")
    if os.getenv("TQ_ACCOUNT") and os.getenv("TQ_PASSWORD"):
        try:
            from ..fetchers.tqsdk_fetcher import TqSdkFetcher
            _source_mgr.register(TqSdkFetcher(), priority=25)
        except Exception as e:
            logger.warning(f"tqsdk 注册失败: {e}")

    # 需密钥 — 仅在环境变量存在时注册
    keyed = [
        ("FRED_API_KEY", "..fetchers.fred_fetcher", "FREDFetcher", 60),
        ("EIA_API_KEY", "..fetchers.eia_cftc_fetcher", "EIAFetcher", 70),
        ("ALPHA_VANTAGE_API_KEY", "..fetchers.alpha_vantage_fetcher", "AlphaVantageFetcher", 80),
        ("FMP_API_KEY", "..fetchers.fmp_fetcher", "FMPFetcher", 80),
        ("TIINGO_API_KEY", "..fetchers.tiingo_fetcher", "TiingoFetcher", 80),
    ]
    import importlib
    for env_var, module_path, cls_name, prio in keyed:
        if not os.getenv(env_var):
            continue
        try:
            mod = importlib.import_module(module_path, package=__name__)
            _source_mgr.register(getattr(mod, cls_name)(), priority=prio)
        except Exception as e:
            logger.warning(f"{cls_name} 注册失败: {e}")


_register_default_fetchers()

router = APIRouter(prefix="/api/v1/data-center", tags=["data-center"])


# ========== 数据源 ==========

@router.get("/sources")
async def list_sources():
    """列出所有数据源"""
    return {"sources": _source_mgr.list_sources()}


@router.get("/sources/health")
async def source_health():
    """数据源健康状态"""
    return _source_mgr.check_health()


# ========== K线数据 ==========

@router.post("/kline")
async def get_kline(
    symbol: str = Query(..., description="品种代码"),
    interval: str = Query("1d", description="K线周期 (1m/5m/15m/30m/60m/1d/1w/1M)"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    contract: Optional[str] = Query(None, description="合约号，如 M2609"),
    source: Optional[str] = Query(None, description="数据源名称"),
):
    """获取 K 线数据"""
    try:
        kline_interval = next(i for i in KlineInterval if i.value == interval)
    except StopIteration:
        raise HTTPException(400, f"无效周期: {interval}")

    # 优先从缓存读取
    data = _data_store.load_kline(symbol, interval, contract=contract)
    if data and data.timestamps:
        return _kline_to_response(data)

    # 从数据源获取
    try:
        data = _source_mgr.get_kline(symbol, kline_interval, start_date, end_date, contract, source)
        # 异步缓存
        _data_store.save_kline(data)
        return _kline_to_response(data)
    except Exception as e:
        raise HTTPException(500, f"获取数据失败: {e}")


@router.post("/kline/verify")
async def verify_kline(
    symbol: str = Query(..., description="品种代码"),
    interval: str = Query("1d", description="K线周期"),
):
    """多数据源交叉验证"""
    try:
        kline_interval = next(i for i in KlineInterval if i.value == interval)
    except StopIteration:
        raise HTTPException(400, f"无效周期: {interval}")

    result = _verifier.cross_validate(symbol, kline_interval)
    return result


# ========== 合约知识 ==========

@router.get("/contracts")
async def list_contracts(exchange: Optional[str] = None, category: Optional[str] = None):
    """列出所有合约品种"""
    if exchange:
        contracts = _knowledge_base.list_by_exchange(exchange)
    elif category:
        contracts = _knowledge_base.list_by_category(category)
    else:
        return {"exchanges": _knowledge_base.get_all_exchanges(),
                "total": len(_knowledge_base.list_all_symbols())}
    return {"contracts": contracts, "count": len(contracts)}


@router.get("/contracts/{symbol}")
async def get_contract_info(symbol: str):
    """获取合约品种信息"""
    info = _knowledge_base.get_contract(symbol.upper())
    if not info:
        raise HTTPException(404, f"未找到品种: {symbol}")
    return info


@router.get("/contracts/{symbol}/main")
async def get_main_contract(symbol: str):
    """获取当前主力合约"""
    code = _main_contract.get_main_contract_code(symbol.upper())
    parsed = _main_contract.parse_contract_code(code)
    cycle = _main_contract.get_contract_cycle(symbol.upper(), 6)
    info = _knowledge_base.get_contract(symbol.upper())
    return {
        "symbol": symbol.upper(),
        "main_contract": code,
        "parsed": parsed,
        "contract_cycle": cycle,
        "contract_info": info,
    }


@router.get("/exchanges")
async def list_exchanges():
    """列出所有交易所"""
    exchanges = _knowledge_base.get_all_exchanges()
    return {"exchanges": exchanges}


# ========== 数据下载 ==========

@router.post("/download")
async def create_download(
    symbol: str = Query(..., description="品种代码"),
    interval: str = Query("1d", description="K线周期 (1m/5m/15m/30m/60m/1d/1w/1M)"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    contract: Optional[str] = Query(None, description="合约号，如 M2609"),
    source: Optional[str] = Query(None, description="数据源"),
):
    """创建数据下载任务，支持指定日期范围"""
    try:
        kline_interval = next(i for i in KlineInterval if i.value == interval)
    except StopIteration:
        raise HTTPException(400, f"无效周期: {interval}")

    task = _dl_mgr.create_task(symbol, kline_interval, start_date, end_date, contract, source or "auto")
    return {"task_id": task.id, "symbol": symbol, "interval": interval,
            "start_date": task.start_date, "end_date": task.end_date,
            "contract": contract, "status": "created"}


@router.post("/download/range")
async def create_range_download(
    symbol: str = Query(..., description="品种代码"),
    interval: str = Query("1d", description="K线周期"),
    start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期 YYYY-MM-DD"),
    contract: Optional[str] = Query(None, description="合约号"),
    asset_type: str = Query("futures", description="资产类别 futures/stock/option"),
):
    """创建指定日期范围的数据下载任务（分钟级支持近3个月）"""
    # 验证日期
    try:
        s = datetime.strptime(start_date, "%Y-%m-%d")
        e = datetime.strptime(end_date, "%Y-%m-%d")
        if s > e:
            raise HTTPException(400, "开始日期不能晚于结束日期")
        # 日线及以上无需严格限制(A股历史可达30年); 分钟级在下方单独限 3 个月
        if (e - s).days > 365 * 30:
            raise HTTPException(400, "日期范围最大30年")
    except ValueError:
        raise HTTPException(400, "日期格式必须为 YYYY-MM-DD")

    try:
        kline_interval = next(i for i in KlineInterval if i.value == interval)
    except StopIteration:
        raise HTTPException(400, f"无效周期: {interval}")

    # 分钟级数据最多3个月
    if kline_interval in (KlineInterval.M1, KlineInterval.M5,
                           KlineInterval.M15, KlineInterval.M30,
                           KlineInterval.M60):
        if (e - s).days > 93:
            raise HTTPException(400, "分钟级数据最多下载3个月")

    market = _market_for(asset_type)
    # 直接执行下载
    data = _source_mgr.get_kline(symbol, kline_interval, start_date, end_date,
                                 contract, market_type=asset_type)
    # 生命周期守卫: 若指定了真实合约 (M2609), 裁剪超出其生命周期的数据
    # (防 fetcher 忽略 contract 返回主力连续, 把 2005 年数据误存成 M2609)
    clipped = 0
    code_for_life = contract or symbol
    if data and data.timestamps:
        from ..knowledge.contract_lifecycle import lifecycle_window
        win = lifecycle_window(code_for_life)
        if win is not None:
            import pandas as pd
            earliest, exp = win
            lo = pd.Timestamp(earliest)
            hi = pd.Timestamp(exp) + pd.offsets.MonthEnd(1)
            keep = [i for i, t in enumerate(data.timestamps)
                    if lo <= pd.Timestamp(t) <= hi]
            if len(keep) < len(data.timestamps):
                clipped = len(data.timestamps) - len(keep)
                data.timestamps = [data.timestamps[i] for i in keep]
                for attr in ("open", "high", "low", "close", "volume"):
                    seq = getattr(data, attr, None)
                    if seq and len(seq) == len(keep) + clipped:
                        setattr(data, attr, [seq[i] for i in keep])
    if data and data.timestamps:
        _data_store.save_kline(data, market=market)
        return {"symbol": symbol, "interval": interval, "asset_type": asset_type,
                "bars": len(data.timestamps), "source": data.source,
                "clipped_out_of_lifecycle": clipped,
                "start": str(data.timestamps[0]) if data.timestamps else "",
                "end": str(data.timestamps[-1]) if data.timestamps else "",
                "status": "completed"}
    return {"symbol": symbol, "interval": interval,
            "bars": 0, "status": "no_data"}


@router.get("/download/{task_id}")
async def get_download_status(task_id: str):
    """获取下载任务状态"""
    task = _dl_mgr.get_task(task_id)
    if not task:
        raise HTTPException(404, f"任务不存在: {task_id}")
    return task


@router.get("/download/history")
async def get_download_history(limit: int = Query(default=20, le=100)):
    """获取下载历史"""
    return {"history": _dl_mgr.get_history(limit)}


@router.post("/download/batch")
async def create_batch_download(
    symbols: str = Query(..., description="品种列表，逗号分隔，如 M,RB,CU"),
    daily: bool = Query(True, description="是否下载日周月 (近1年)"),
    minute: bool = Query(True, description="是否下载分钟小时 (近3月)"),
    contract: Optional[str] = Query(None, description="可选合约号"),
):
    """
    批量下载 — 为多个品种同时下载日周月 + 分钟级数据。
    
    - 日周月 (1d/1w/1M): 近 1 年
    - 分钟小时 (5m/15m/30m/60m): 近 3 个月
    """
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        raise HTTPException(400, "请至少指定一个品种")
    if len(sym_list) > 20:
        raise HTTPException(400, "一次最多下载20个品种")

    daily_intervals = [KlineInterval.DAY, KlineInterval.WEEK, KlineInterval.MONTH] if daily else []
    minute_intervals = [KlineInterval.M5, KlineInterval.M15,
                        KlineInterval.M30, KlineInterval.M60] if minute else []

    if not daily_intervals and not minute_intervals:
        raise HTTPException(400, "至少选择日周月或分钟小时")

    try:
        results = await _dl_mgr.execute_batch_multi_interval(
            symbols=sym_list,
            daily_intervals=daily_intervals or None,
            minute_intervals=minute_intervals or None,
            daily_range_days=365,
            minute_range_days=93,
            contract=contract,
        )
    except Exception as e:
        raise HTTPException(500, f"批量下载失败: {e}")

    def _task_summary(task) -> dict:
        return {
            "symbol": task.symbol,
            "interval": task.interval.value,
            "contract": task.contract or "主力",
            "bars": task.downloaded_bars,
            "status": task.status.value,
            "start_date": task.start_date,
            "end_date": task.end_date,
        }

    summary = {
        "daily": [_task_summary(t) for t in results.get("daily", [])],
        "minute": [_task_summary(t) for t in results.get("minute", [])],
        "total_symbols": len(sym_list),
        "daily_total_bars": sum(t.downloaded_bars for t in results.get("daily", [])),
        "minute_total_bars": sum(t.downloaded_bars for t in results.get("minute", [])),
        "daily_success": sum(1 for t in results.get("daily", []) if t.status.value == "completed"),
        "minute_success": sum(1 for t in results.get("minute", []) if t.status.value == "completed"),
        "daily_total": len(results.get("daily", [])),
        "minute_total": len(results.get("minute", [])),
    }
    return summary


@router.get("/download/stats")
async def get_download_stats():
    """获取下载统计"""
    return {"stats": _dl_mgr.get_statistics()}


# ========== 同步调度 ==========

@router.post("/sync/start")
async def start_sync():
    """启动同步调度"""
    await _scheduler.start()
    return {"status": "started"}


@router.post("/sync/stop")
async def stop_sync():
    """停止同步调度"""
    await _scheduler.stop()
    return {"status": "stopped"}


@router.get("/sync/status")
async def get_sync_status():
    """获取同步状态"""
    return _scheduler.get_status()


@router.post("/sync/add")
async def add_sync_symbol(
    symbol: str = Query(...),
    intervals: str = Query("1d,5m,15m", description="周期列表，逗号分隔"),
):
    """添加同步品种"""
    interval_list = [KlineInterval(i.strip()) for i in intervals.split(",")]
    _scheduler.add_symbol(symbol.upper(), interval_list)
    return {"status": "added", "symbol": symbol.upper()}


# ========== 存储管理 ==========

@router.get("/storage")
async def get_storage_info():
    """获取存储使用统计 (聚合 期货/股票/期权 三类)。"""
    usage = _data_store.get_storage_usage()
    available = []
    for asset in ("futures", "stock", "option"):
        available.extend(_data_store.list_available(market=_market_for(asset)))
    return {"usage": usage, "available": available}


# ========== 数据预览 / 质量校验 ==========

@router.get("/data-files")
async def list_downloaded(asset_type: str = Query("futures", description="资产类别 futures/stock/option")):
    """列出某资产类别已下载缓存文件。"""
    market = _market_for(asset_type)
    return {"asset_type": asset_type, "market": market,
            "files": _data_store.list_available(market=market)}


@router.delete("/data-files")
async def delete_downloaded(
    symbol: str = Query(..., description="品种/股票/期权代码"),
    interval: str = Query("1d", description="K线周期"),
    asset_type: str = Query("futures", description="资产类别 futures/stock/option"),
    contract: Optional[str] = Query(None, description="合约号 (可选)"),
):
    """删除一个已下载的缓存文件 (Parquet 单文件存储)。"""
    market = _market_for(asset_type)
    ok = _data_store.delete(symbol, interval, market=market, contract=contract)
    if not ok:
        raise HTTPException(404, f"文件不存在: {symbol} {interval} {contract or ''}")
    return {"deleted": True, "symbol": symbol, "interval": interval,
            "asset_type": asset_type, "contract": contract}


@router.get("/data-files/export")
async def export_downloaded(
    symbol: str = Query(..., description="品种/股票/期权代码"),
    interval: str = Query("1d", description="K线周期"),
    asset_type: str = Query("futures", description="资产类别 futures/stock/option"),
    contract: Optional[str] = Query(None, description="合约号 (可选)"),
):
    """导出一个已下载缓存文件为 .xlsx。"""
    import io
    import pandas as pd
    from fastapi.responses import StreamingResponse

    market = _market_for(asset_type)
    data = _data_store.load_kline(symbol, interval, market=market, contract=contract)
    if not data or not data.timestamps:
        raise HTTPException(404, f"无数据可导出: {symbol} {interval} {contract or ''}")
    df = pd.DataFrame({
        "datetime": [str(t) for t in data.timestamps],
        "open": data.open, "high": data.high, "low": data.low,
        "close": data.close, "volume": data.volume,
    })
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=f"{symbol}_{interval}"[:31])
    buf.seek(0)
    fname = f"{contract or symbol}_{interval}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/preview")
async def preview_data(
    symbol: str = Query(..., description="品种/股票/期权代码"),
    interval: str = Query("1d", description="K线周期"),
    asset_type: str = Query("futures", description="资产类别 futures/stock/option"),
    contract: Optional[str] = Query(None, description="合约号 (可选)"),
    limit: int = Query(100, le=1000, description="返回行数"),
    offset: int = Query(0, ge=0, description="起始行偏移"),
):
    """预览已下载数据 — 返回分页 OHLCV 行 + 数据质量统计。"""
    market = _market_for(asset_type)
    data = _data_store.load_kline(symbol, interval, market=market, contract=contract)
    if not data or not data.timestamps:
        raise HTTPException(404, f"未找到缓存数据: {symbol} {interval} ({market})")

    ts = [str(t) for t in data.timestamps]
    n = len(ts)

    def _col(v):
        return v if v and len(v) == n else (v or [])

    o, h, l, c, vol = (_col(data.open), _col(data.high), _col(data.low),
                       _col(data.close), _col(data.volume))

    # 质量校验
    def _count(pred, seq):
        return sum(1 for x in seq if pred(x))

    is_num = lambda x: isinstance(x, (int, float))
    nan_close = _count(lambda x: x is None or (is_num(x) and x != x), c)
    zero_close = _count(lambda x: is_num(x) and x == 0, c)
    neg = _count(lambda x: is_num(x) and x < 0, c) + _count(lambda x: is_num(x) and x < 0, l)
    # high<low 异常
    hl_bad = sum(1 for hi, lo in zip(h, l)
                 if is_num(hi) and is_num(lo) and hi < lo)
    dup = n - len(set(ts))

    quality = {
        "rows": n,
        "start": ts[0] if ts else "",
        "end": ts[-1] if ts else "",
        "nan_close": nan_close,
        "zero_close": zero_close,
        "negative_values": neg,
        "high_lt_low": hl_bad,
        "duplicate_timestamps": dup,
        "is_clean": nan_close == 0 and neg == 0 and hl_bad == 0 and dup == 0,
    }

    sl = slice(offset, offset + limit)
    rows = [
        {"datetime": ts[i], "open": o[i] if i < len(o) else None,
         "high": h[i] if i < len(h) else None, "low": l[i] if i < len(l) else None,
         "close": c[i] if i < len(c) else None, "volume": vol[i] if i < len(vol) else None}
        for i in range(*sl.indices(n))
    ]
    return {
        "symbol": symbol, "interval": interval, "asset_type": asset_type,
        "contract": contract, "source": data.source, "total": n,
        "offset": offset, "limit": limit, "rows": rows, "quality": quality,
        "chart": {"datetime": ts, "close": c},
    }


@router.get("/options/codes")
async def list_option_codes(
    underlying: str = Query("510050", description="标的: 510050/510300/510500 (ETF) 或 IO/HO (股指)"),
    option_type: str = Query("看涨期权", description="看涨期权/看跌期权"),
):
    """查询期权合约代码列表 (供下载选择器使用)。"""
    from ..fetchers.options_fetcher import ChinaOptionsFetcher
    opt = ChinaOptionsFetcher()
    u = underlying.upper()
    if u in ("IO", "HO"):
        # 股指期权: 用实时行情接口枚举当前在交易的合约代码
        rt = opt.get_index_option_realtime(u.lower())
        codes = rt["合约代码"].tolist() if (rt is not None and not rt.empty and "合约代码" in rt.columns) else []
        return {"underlying": u, "count": len(codes), "codes": codes}
    df = opt.get_etf_option_codes(option_type=option_type, underlying=underlying)
    if df is None or df.empty:
        return {"underlying": underlying, "count": 0, "codes": []}
    # akshare option_sse_codes_sina 列为 ['序号','期权代码']; 取代码列, 不要序号
    col = next((c for c in ("期权代码", "合约代码", "代码") if c in df.columns), None)
    if col is None:
        col = next((c for c in df.columns if c != "序号"), df.columns[-1])
    codes = [str(x) for x in df[col].tolist()]
    return {"underlying": underlying, "count": len(codes), "codes": codes}


# ========== 辅助 ==========

def _kline_to_response(data) -> Dict[str, Any]:
    """KlineData 转响应"""
    if not data or not data.timestamps:
        return {"symbol": data.symbol if data else "", "interval": data.interval if data else "",
                "bars": 0, "open": [], "high": [], "low": [], "close": [], "volume": [], "timestamps": []}
    return {
        "symbol": data.symbol,
        "interval": data.interval,
        "contract": data.contract,
        "source": data.source,
        "bars": len(data.timestamps),
        "open": data.open,
        "high": data.high,
        "low": data.low,
        "close": data.close,
        "volume": data.volume,
        "timestamps": [str(t) if isinstance(t, datetime) else str(t) for t in data.timestamps],
    }
