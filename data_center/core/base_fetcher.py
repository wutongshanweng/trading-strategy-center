"""
Base fetcher — 所有数据获取器的基类。

所有数据源获取器统一继承 BaseFetcher，实现标准接口:
- get_kline: 获取 K 线数据 (支持日/周/月/分钟)
- get_realtime: 获取实时行情
- get_contract_info: 获取合约信息
- validate: 数据源验证
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class KlineInterval(Enum):
    """K线周期枚举"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    M60 = "60m"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1M"


class DataSourceStatus(Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class DataSourceInfo:
    """数据源信息"""
    name: str
    display_name: str
    version: str
    status: DataSourceStatus = DataSourceStatus.UNKNOWN
    last_check: Optional[datetime] = None
    supported_markets: List[str] = field(default_factory=list)
    requires_api_key: bool = False
    rate_limit: Optional[str] = None
    description: str = ""


@dataclass
class KlineData:
    """统一 K 线数据格式"""
    symbol: str
    interval: str
    open: List[float]
    high: List[float]
    low: List[float]
    close: List[float]
    volume: List[float]
    timestamps: List[datetime]
    source: str
    contract: Optional[str] = None  # 具体合约号，如 M2609


@dataclass
class RealtimeQuote:
    """统一实时行情格式"""
    symbol: str
    last_price: float
    open_price: float
    high_price: float
    low_price: float
    pre_close: float
    volume: int
    turnover: float
    bid_price: float
    ask_price: float
    bid_volume: int
    ask_volume: int
    timestamp: datetime
    source: str
    contract: Optional[str] = None


@dataclass
class ContractInfo:
    """合约信息"""
    symbol: str           # 品种代码，如 M, RB, CU
    exchange: str         # 交易所
    name_cn: str          # 中文名称
    name_en: str          # 英文名称
    contract_multiplier: int     # 合约乘数
    min_tick: float       # 最小变动价位
    trading_hours: str    # 交易时间
    margin_rate: float    # 保证金比例
    commission_open: float      # 开仓手续费
    commission_close: float     # 平仓手续费
    commission_close_today: float  # 平今手续费
    listed_date: Optional[str] = None
    delivery_month: List[int] = field(default_factory=list)  # 交割月份
    price_limit: float = 0.0    # 涨跌停板
    category: str = ""          # 分类: 农产品/金属/能源/化工/金融


class BaseFetcher(ABC):
    """所有数据获取器的抽象基类"""

    def __init__(self):
        self._name = self.__class__.__name__
        self._status = DataSourceStatus.UNKNOWN
        logger.info(f"Initialized fetcher: {self._name}")

    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """显示名称"""
        pass

    @property
    def info(self) -> DataSourceInfo:
        """获取数据源信息"""
        return DataSourceInfo(
            name=self.name,
            display_name=self.display_name,
            version="1.0.0",
            status=self._status,
            last_check=datetime.now(),
            supported_markets=self._get_supported_markets(),
            description=self._get_description(),
        )

    @abstractmethod
    def get_kline(
        self,
        symbol: str,
        interval: KlineInterval = KlineInterval.DAY,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        contract: Optional[str] = None,
    ) -> KlineData:
        """
        获取 K 线数据。
        
        Args:
            symbol: 品种代码 (如 'M', 'RB', 'CU')
            interval: K 线周期
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            contract: 具体合约号 (如 'M2609')，None 则获取主力连续
        
        Returns:
            标准化的 K 线数据
        """
        pass

    @abstractmethod
    def get_realtime(self, symbol: str, contract: Optional[str] = None) -> RealtimeQuote:
        """
        获取实时行情。
        
        Args:
            symbol: 品种代码
            contract: 合约号，None 则获取主力合约
        
        Returns:
            标准化实时行情
        """
        pass

    def get_contract_info(self, symbol: str) -> Optional[ContractInfo]:
        """获取合约品种基本信息"""
        return None

    def validate(self) -> bool:
        """验证数据源是否可用"""
        try:
            self._status = DataSourceStatus.ACTIVE
            return True
        except Exception:
            self._status = DataSourceStatus.DOWN
            return False

    def _get_supported_markets(self) -> List[str]:
        """获取支持的市场列表"""
        return []

    def _get_description(self) -> str:
        """获取描述信息"""
        return ""
