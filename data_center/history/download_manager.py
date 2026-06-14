"""
历史数据下载管理器。

支持下载周期:
- 日线 / 周线 / 月线
- 分钟线: M5 / M15 / M30 / 1H (近3个月)
- 主力合约 + 具体合约号 (如 M2609)

框架:
1. 创建下载任务
2. 并行下载多个数据源
3. 数据质量校验
4. 存储到本地数据库/文件
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from ..core.base_fetcher import KlineData, KlineInterval
from ..core.data_source import DataSourceManager

logger = logging.getLogger(__name__)


class DownloadStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class DownloadTask:
    """下载任务定义"""
    id: str
    symbol: str                    # 品种代码
    name: str                      # 品种名称
    interval: KlineInterval        # 周期
    start_date: str                # 开始日期 YYYY-MM-DD
    end_date: str                  # 结束日期 YYYY-MM-DD
    contract: Optional[str] = None # 合约号 (None=主力)
    source: str = "auto"           # 数据源
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0          # 0-100
    total_bars: int = 0
    downloaded_bars: int = 0
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    @property
    def display_name(self) -> str:
        name_parts = [self.symbol]
        if self.contract:
            name_parts.append(self.contract)
        name_parts.append(self.interval.value)
        return "-".join(name_parts)


class DownloadManager:
    """
    历史数据下载管理器。
    
    支持:
    - 日/周/月: 全历史数据
    - M5/M15/M30/1H: 近3个月
    - 多数据源校验
    - 断点续传
    - 进度跟踪
    """

    # 各周期可下载的最大时长
    MAX_PERIODS: Dict[str, str] = {
        "1m": "7d",      # 1分钟: 7天
        "5m": "1M",      # 5分钟: 1个月
        "15m": "3M",     # 15分钟: 3个月
        "30m": "3M",     # 30分钟: 3个月
        "60m": "6M",     # 60分钟: 6个月
        "1d": "10y",     # 日线: 10年
        "1w": "10y",     # 周线: 10年
        "1M": "10y",     # 月线: 10年
    }

    def __init__(self, source_manager: DataSourceManager):
        self._source_mgr = source_manager
        self._tasks: Dict[str, DownloadTask] = {}
        self._history: List[DownloadTask] = []
        self._running = set()

    def create_task(self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
                    start_date: Optional[str] = None, end_date: Optional[str] = None,
                    contract: Optional[str] = None, source: str = "auto",
                    name: str = "") -> DownloadTask:
        """创建下载任务"""
        # 默认日期范围
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = self._get_default_start(interval)

        task_id = f"{symbol}_{contract or 'main'}_{interval.value}_{datetime.now().timestamp():.0f}"
        task = DownloadTask(
            id=task_id,
            symbol=symbol.upper(),
            name=name or symbol.upper(),
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            contract=contract,
            source=source,
        )
        self._tasks[task_id] = task
        return task

    async def execute_task(self, task_id: str) -> DownloadTask:
        """执行下载任务"""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task_id in self._running:
            logger.warning(f"Task {task_id} already running")
            return task

        self._running.add(task_id)
        task.status = DownloadStatus.RUNNING

        try:
            # 获取数据
            data = self._source_mgr.get_kline(
                symbol=task.symbol,
                interval=task.interval,
                start_date=task.start_date,
                end_date=task.end_date,
                contract=task.contract,
                source=task.source if task.source != "auto" else None,
            )

            if data and data.timestamps:
                task.downloaded_bars = len(data.timestamps)
                task.total_bars = len(data.timestamps)
                task.progress = 100.0
                task.status = DownloadStatus.COMPLETED
                logger.info(f"Download completed: {task.display_name} ({task.downloaded_bars} bars)")
            else:
                task.status = DownloadStatus.FAILED
                task.errors.append("No data returned")
                logger.warning(f"Download failed: {task.display_name}")

        except Exception as e:
            task.status = DownloadStatus.FAILED
            task.errors.append(str(e))
            logger.error(f"Download error: {task.display_name}: {e}")

        finally:
            task.completed_at = datetime.now()
            self._running.discard(task_id)
            self._history.append(task)

        return task

    async def execute_batch(self, symbols: List[str], interval: KlineInterval = KlineInterval.DAY,
                             contract: Optional[str] = None) -> List[DownloadTask]:
        """批量执行下载任务"""
        tasks = []
        for sym in symbols:
            task = self.create_task(sym, interval, contract=contract)
            tasks.append(task)

        results = await asyncio.gather(
            *[self.execute_task(t.id) for t in tasks],
            return_exceptions=True,
        )

        completed = []
        for r in results:
            if isinstance(r, DownloadTask):
                completed.append(r)
            elif isinstance(r, Exception):
                logger.error(f"Batch task failed: {r}")

        return completed

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        return self._tasks.get(task_id)

    def list_tasks(self, status: Optional[DownloadStatus] = None) -> List[DownloadTask]:
        if status:
            return [t for t in self._tasks.values() if t.status == status]
        return list(self._tasks.values())

    def get_history(self, limit: int = 50) -> List[DownloadTask]:
        return sorted(self._history, key=lambda t: t.created_at, reverse=True)[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """获取下载统计"""
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.status == DownloadStatus.COMPLETED)
        failed = sum(1 for t in self._tasks.values() if t.status == DownloadStatus.FAILED)
        running = sum(1 for t in self._tasks.values() if t.status == DownloadStatus.RUNNING)
        total_bars = sum(t.downloaded_bars for t in self._tasks.values())
        return {
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "total_bars_downloaded": total_bars,
            "unique_symbols": len(set(t.symbol for t in self._tasks.values())),
        }

    def _get_default_start(self, interval: KlineInterval) -> str:
        """根据周期获取默认开始日期"""
        now = datetime.now()
        period_map = {
            KlineInterval.M1: (now - timedelta(days=7)).strftime("%Y-%m-%d"),
            KlineInterval.M5: (now - timedelta(days=30)).strftime("%Y-%m-%d"),
            KlineInterval.M15: (now - timedelta(days=90)).strftime("%Y-%m-%d"),
            KlineInterval.M30: (now - timedelta(days=90)).strftime("%Y-%m-%d"),
            KlineInterval.M60: (now - timedelta(days=180)).strftime("%Y-%m-%d"),
            KlineInterval.DAY: (now - timedelta(days=365)).strftime("%Y-%m-%d"),
            KlineInterval.WEEK: (now - timedelta(days=365 * 3)).strftime("%Y-%m-%d"),
            KlineInterval.MONTH: (now - timedelta(days=365 * 5)).strftime("%Y-%m-%d"),
        }
        return period_map.get(interval, (now - timedelta(days=365)).strftime("%Y-%m-%d"))

    async def execute_batch_multi_interval(
        self,
        symbols: List[str],
        daily_intervals: Optional[List[KlineInterval]] = None,
        minute_intervals: Optional[List[KlineInterval]] = None,
        daily_range_days: int = 365,
        minute_range_days: int = 93,
        contract: Optional[str] = None,
    ) -> Dict[str, List[DownloadTask]]:
        """
        批量多周期下载 — 为多个品种同时下载日周月 + 分钟级数据。
        
        Args:
            symbols: 品种代码列表
            daily_intervals: 日级周期 (默认 [DAY, WEEK, MONTH])
            minute_intervals: 分钟级周期 (默认 [M5, M15, M30, M60])
            daily_range_days: 日级数据天数范围 (默认 1 年)
            minute_range_days: 分钟级数据天数范围 (默认 3 个月)
            contract: 可选合约号
        
        Returns:
            {"daily": [task, ...], "minute": [task, ...]}
        """
        if daily_intervals is None:
            daily_intervals = [KlineInterval.DAY, KlineInterval.WEEK, KlineInterval.MONTH]
        if minute_intervals is None:
            minute_intervals = [KlineInterval.M5, KlineInterval.M15,
                                KlineInterval.M30, KlineInterval.M60]

        now = datetime.now()
        end_date = now.strftime("%Y-%m-%d")
        daily_start = (now - timedelta(days=daily_range_days)).strftime("%Y-%m-%d")
        minute_start = (now - timedelta(days=minute_range_days)).strftime("%Y-%m-%d")

        all_tasks: List[DownloadTask] = []
        for sym in symbols:
            sym = sym.upper()
            # 日级任务
            for interval in daily_intervals:
                task = self.create_task(sym, interval, daily_start, end_date, contract)
                all_tasks.append(task)
            # 分钟级任务
            for interval in minute_intervals:
                task = self.create_task(sym, interval, minute_start, end_date, contract)
                all_tasks.append(task)

        # 并行执行所有任务 (最多同时 10 个)
        sem = asyncio.Semaphore(10)

        async def _run_with_sem(task_id: str) -> DownloadTask:
            async with sem:
                return await self.execute_task(task_id)

        results = await asyncio.gather(
            *[_run_with_sem(t.id) for t in all_tasks],
            return_exceptions=True,
        )

        daily_results, minute_results = [], []
        for r in results:
            if isinstance(r, DownloadTask):
                if r.interval in daily_intervals:
                    daily_results.append(r)
                else:
                    minute_results.append(r)
            elif isinstance(r, Exception):
                logger.error(f"Batch task failed: {r}")

        return {"daily": daily_results, "minute": minute_results}

    def get_batch_intervals_info(self) -> Dict[str, Any]:
        """获取批量下载的周期配置信息"""
        return {
            "daily": {
                "intervals": ["1d", "1w", "1M"],
                "range_days": 365,
                "label": "日周月 (近1年)",
                "description": "日线/周线/月线 — 过去1年",
            },
            "minute": {
                "intervals": ["5m", "15m", "30m", "60m"],
                "range_days": 93,
                "label": "分钟小时 (近3月)",
                "description": "5分钟/15分钟/30分钟/60分钟 — 过去3个月",
            },
        }

    def get_supported_intervals(self) -> List[str]:
        """获取支持的K线周期列表"""
        return [i.value for i in KlineInterval]
