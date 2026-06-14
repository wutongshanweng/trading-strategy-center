"""
实时同步调度器 — 定时同步市场数据。

功能:
- 定时拉取最新 K 线数据
- 主力合约自动切换检测
- 分钟数据同步 (M5/M15/M30/1H)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

from ..core.base_fetcher import KlineInterval
from ..core.data_source import DataSourceManager
from .download_manager import DownloadManager
from .data_store import DataStore

logger = logging.getLogger(__name__)


@dataclass
class SyncConfig:
    """同步配置"""
    symbol: str
    intervals: List[KlineInterval] = field(default_factory=lambda: [
        KlineInterval.DAY, KlineInterval.M5, KlineInterval.M15,
    ])
    enabled: bool = True
    sync_interval_seconds: int = 300  # 5分钟同步一次


class SyncScheduler:
    """
    实时同步调度器。

    支持按品种配置同步周期，自动拉取最新数据并存储。
    """

    def __init__(self, download_mgr: DownloadManager, data_store: DataStore):
        self._dl_mgr = download_mgr
        self._store = data_store
        self._configs: Dict[str, SyncConfig] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def add_symbol(self, symbol: str, intervals: Optional[List[KlineInterval]] = None,
                   sync_seconds: int = 300) -> SyncConfig:
        """添加同步品种"""
        config = SyncConfig(
            symbol=symbol.upper(),
            intervals=intervals or [KlineInterval.DAY, KlineInterval.M5, KlineInterval.M15],
            sync_interval_seconds=sync_seconds,
        )
        self._configs[config.symbol] = config
        return config

    def remove_symbol(self, symbol: str):
        """移除同步品种"""
        self._configs.pop(symbol.upper(), None)

    async def start(self):
        """启动同步调度器"""
        if self._running:
            logger.warning("Sync scheduler already running")
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Sync scheduler started with {len(self._configs)} symbols")

    async def stop(self):
        """停止同步调度器"""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Sync scheduler stopped")

    async def sync_now(self, symbol: str) -> bool:
        """立即同步指定品种"""
        config = self._configs.get(symbol.upper())
        if not config:
            logger.warning(f"No sync config for {symbol}")
            return False
        return await self._sync_symbol(config)

    async def _run_loop(self):
        """主循环"""
        while self._running:
            for config in self._configs.values():
                if not config.enabled:
                    continue
                try:
                    await self._sync_symbol(config)
                except Exception as e:
                    logger.error(f"Sync failed for {config.symbol}: {e}")
            await asyncio.sleep(30)  # 每30秒检查一次

    async def _sync_symbol(self, config: SyncConfig) -> bool:
        """同步单个品种"""
        success = True
        for interval in config.intervals:
            try:
                # 下载最新数据
                end = datetime.now().strftime("%Y-%m-%d")
                if interval in (KlineInterval.M5, KlineInterval.M15,
                                KlineInterval.M30, KlineInterval.M60):
                    start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
                else:
                    start = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

                task = self._dl_mgr.create_task(
                    symbol=config.symbol,
                    interval=interval,
                    start_date=start,
                    end_date=end,
                )
                result = await self._dl_mgr.execute_task(task.id)
                if result.status == "completed":
                    # 存储数据
                    pass  # 由 DownloadManager 处理
            except Exception as e:
                logger.warning(f"Sync {config.symbol} {interval.value}: {e}")
                success = False
        return success

    def get_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        return {
            "running": self._running,
            "symbols": len(self._configs),
            "configs": [
                {"symbol": c.symbol,
                 "intervals": [i.value for i in c.intervals],
                 "enabled": c.enabled}
                for c in self._configs.values()
            ],
        }

    def get_configs(self) -> List[SyncConfig]:
        return list(self._configs.values())
