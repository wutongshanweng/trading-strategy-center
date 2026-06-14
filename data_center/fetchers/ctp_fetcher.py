"""
CTP Fetcher — 期货 Tick → K 线合成器。

底层: 无外部依赖（Tick 转 Bar 在本地完成）
生产环境推荐使用 TqSdk / vn.py 接入 CTP 实时行情
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

from ..core.base_fetcher import (
    BaseFetcher, KlineData, KlineInterval, RealtimeQuote,
    DataSourceStatus,
)

logger = logging.getLogger(__name__)


class CTPFetcher(BaseFetcher):
    """
    CTP 数据获取器 — 期货 Tick → K 线合成。
    
    注意: 当前实现为 Tick 转 Bar 工具。
    生产环境需通过 TqSdk / vn.py 连接 CTP 柜台获取实时 Tick。
    """

    name = "ctp"
    display_name = "CTP (期货)"

    def get_kline(self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
                  start_date: Optional[str] = None, end_date: Optional[str] = None,
                  contract: Optional[str] = None) -> KlineData:
        """CTP 不直接提供 K 线，返回空数据"""
        return KlineData(symbol=symbol, interval=interval.value,
                         open=[], high=[], low=[], close=[],
                         volume=[], timestamps=[], source=self.name)

    def get_realtime(self, symbol: str, contract: Optional[str] = None) -> RealtimeQuote:
        return RealtimeQuote(symbol=symbol, last_price=0, open_price=0,
            high_price=0, low_price=0, pre_close=0, volume=0, turnover=0,
            bid_price=0, ask_price=0, bid_volume=0, ask_volume=0,
            timestamp=datetime.now(), source=self.name, contract=contract)

    @staticmethod
    def ticks_to_bars(ticks: pd.DataFrame, bar_seconds: int = 60) -> pd.DataFrame:
        """
        Tick 数据转 K 线（OHLC）。
        
        Args:
            ticks: Tick DataFrame, 必须包含 datetime, last_price, volume 列
            bar_seconds: K线周期 (秒), 默认 60 秒
        
        Returns:
            OHLC DataFrame: datetime, open, high, low, close, volume
        """
        if ticks.empty:
            return pd.DataFrame()

        df = ticks.copy()
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.set_index("datetime")

        # 将时间戳 floor 到 bar_seconds 的整数倍
        rule = f"{bar_seconds}s"
        
        # 使用命名聚合: 将 last_price 拆分为 OHLC, volume 求和
        resampled = df.resample(rule, label="right", closed="right").agg(
            open=("last_price", "first"),
            high=("last_price", "max"),
            low=("last_price", "min"),
            close=("last_price", "last"),
            volume=("volume", "sum"),
        )
        resampled = resampled.dropna(subset=["open"])
        resampled = resampled.reset_index()

        return resampled

    def validate(self) -> bool:
        """CTP 验证 — 无实时连接时返回 degraded"""
        self._status = DataSourceStatus.DEGRADED
        return False

    def _get_supported_markets(self) -> List[str]:
        return ["futures"]

    def _get_description(self) -> str:
        return "CTP Tick → K线合成工具。需要依赖 TqSdk/vn.py 连接 CTP 柜台获取实时行情"
