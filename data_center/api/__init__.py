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
):
    """创建指定日期范围的数据下载任务（分钟级支持近3个月）"""
    # 验证日期
    try:
        s = datetime.strptime(start_date, "%Y-%m-%d")
        e = datetime.strptime(end_date, "%Y-%m-%d")
        if s > e:
            raise HTTPException(400, "开始日期不能晚于结束日期")
        if (e - s).days > 365 * 3:
            raise HTTPException(400, "日期范围最大3年")
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

    # 直接执行下载
    data = _source_mgr.get_kline(symbol, kline_interval, start_date, end_date, contract)
    if data and data.timestamps:
        _data_store.save_kline(data)
        return {"symbol": symbol, "interval": interval,
                "bars": len(data.timestamps), "source": data.source,
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
    """获取存储使用统计"""
    usage = _data_store.get_storage_usage()
    available = _data_store.list_available()
    return {"usage": usage, "available": available}


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
