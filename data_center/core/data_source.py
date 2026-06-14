"""
数据源管理器 — 统一管理多个数据获取器。

支持:
- 自动路由到最佳数据源
- 多数据源优先级
- 数据源健康检查
- 数据源切换
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type, Tuple
from datetime import datetime

from .base_fetcher import (
    BaseFetcher, DataSourceInfo, DataSourceStatus,
    KlineData, KlineInterval, RealtimeQuote,
)

logger = logging.getLogger(__name__)


class DataSourceManager:
    """
    数据源管理器 — 统一接入所有数据获取器。
    
    支持 11 个数据源:
    - AKShare: 中国全品类 (期货/股票/期权/基金)
    - TDX (通达信): 中国市场实时行情
    - YFinance: 国际股票/期货
    - CTP: 期货深度数据
    - Alpha Vantage: 全球金融数据
    - FMP: 财务报表数据
    - FRED: 美国经济数据
    - EIA/CFTC: 能源/持仓报告
    - Tiingo: 美股高精度数据
    - Options: 期权链数据
    """

    def __init__(self):
        self._fetchers: Dict[str, BaseFetcher] = {}
        self._priority: Dict[str, int] = {}
        self._auto_route = True
        self._futures_markets = self._init_futures_market_map()

    def register(self, fetcher: BaseFetcher, priority: int = 100) -> str:
        """
        注册数据获取器。
        
        Args:
            fetcher: 数据获取器实例
            priority: 优先级 (越小越优先)
        
        Returns:
            数据源名称
        """
        name = fetcher.name
        self._fetchers[name] = fetcher
        self._priority[name] = priority
        self._fetchers = dict(sorted(
            self._fetchers.items(),
            key=lambda x: self._priority.get(x[0], 999)
        ))
        logger.info(f"Registered data source: {name} (priority={priority})")
        return name

    def unregister(self, name: str):
        """注销数据源"""
        self._fetchers.pop(name, None)
        self._priority.pop(name, None)

    def list_sources(self) -> List[DataSourceInfo]:
        """列出所有已注册数据源"""
        return [f.info for f in self._fetchers.values()]

    def get_source(self, name: str) -> Optional[BaseFetcher]:
        """获取指定数据源"""
        return self._fetchers.get(name)

    def get_best_source(self, symbol: str, market_type: str = "futures") -> BaseFetcher:
        """
        获取最适合指定品种的数据源。
        
        Args:
            symbol: 品种代码
            market_type: 市场类型 (futures/stock/option)
        
        Returns:
            最优数据源
        """
        # 中国期货优先: AKShare > TDX > YFinance
        if market_type == "futures":
            if "akshare" in self._fetchers:
                return self._fetchers["akshare"]
            if "tdx" in self._fetchers:
                return self._fetchers["tdx"]
        
        # 中国股票: AKShare > TDX
        if market_type == "stock":
            if symbol.replace(".", "").isdigit():
                if "akshare" in self._fetchers:
                    return self._fetchers["akshare"]
        
        # 国际: YFinance > Alpha Vantage
        if "yfinance" in self._fetchers:
            return self._fetchers["yfinance"]
        
        # 默认返回第一个
        if self._fetchers:
            return list(self._fetchers.values())[0]
        
        raise ValueError(f"No data source available for {symbol}")

    def get_kline(
        self,
        symbol: str,
        interval: KlineInterval = KlineInterval.DAY,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        contract: Optional[str] = None,
        source: Optional[str] = None,
    ) -> KlineData:
        """
        获取 K 线数据，自动路由到最佳数据源。
        
        支持多数据源校验:
        如果指定了 source，使用指定数据源。
        否则自动选择最优数据源。
        """
        if source:
            fetcher = self._fetchers.get(source)
            if not fetcher:
                raise ValueError(f"Data source '{source}' not found")
            return fetcher.get_kline(symbol, interval, start_date, end_date, contract)
        
        fetcher = self.get_best_source(symbol)
        return fetcher.get_kline(symbol, interval, start_date, end_date, contract)

    def get_kline_multi_source(
        self,
        symbol: str,
        interval: KlineInterval = KlineInterval.DAY,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        contract: Optional[str] = None,
    ) -> Dict[str, KlineData]:
        """
        从多个数据源获取 K 线数据（用于交叉验证）。
        
        Returns:
            {数据源名称: K线数据}
        """
        results = {}
        for name, fetcher in self._fetchers.items():
            try:
                data = fetcher.get_kline(symbol, interval, start_date, end_date, contract)
                results[name] = data
            except Exception as e:
                logger.warning(f"Source '{name}' failed for {symbol}: {e}")
        return results

    def get_realtime(
        self,
        symbol: str,
        contract: Optional[str] = None,
        source: Optional[str] = None,
    ) -> RealtimeQuote:
        """获取实时行情"""
        if source:
            fetcher = self._fetchers.get(source)
            if not fetcher:
                raise ValueError(f"Data source '{source}' not found")
            return fetcher.get_realtime(symbol, contract)
        
        fetcher = self.get_best_source(symbol, "futures")
        return fetcher.get_realtime(symbol, contract)

    def validate_all(self) -> Dict[str, bool]:
        """验证所有数据源状态"""
        results = {}
        for name, fetcher in self._fetchers.items():
            results[name] = fetcher.validate()
        return results

    def check_health(self) -> Dict[str, str]:
        """检查所有数据源健康状态"""
        status = {}
        for name, fetcher in self._fetchers.items():
            try:
                ok = fetcher.validate()
                status[name] = "healthy" if ok else "degraded"
            except Exception:
                status[name] = "down"
        return status

    def _init_futures_market_map(self) -> Dict[str, Dict]:
        """初始化期货市场映射"""
        return {
            # 上海期货交易所 (SHFE)
            "CU": {"exchange": "SHFE", "name": "沪铜", "category": "金属"},
            "AL": {"exchange": "SHFE", "name": "沪铝", "category": "金属"},
            "ZN": {"exchange": "SHFE", "name": "沪锌", "category": "金属"},
            "PB": {"exchange": "SHFE", "name": "沪铅", "category": "金属"},
            "NI": {"exchange": "SHFE", "name": "沪镍", "category": "金属"},
            "SN": {"exchange": "SHFE", "name": "沪锡", "category": "金属"},
            "AU": {"exchange": "SHFE", "name": "黄金", "category": "贵金属"},
            "AG": {"exchange": "SHFE", "name": "白银", "category": "贵金属"},
            "RB": {"exchange": "SHFE", "name": "螺纹钢", "category": "钢铁"},
            "WR": {"exchange": "SHFE", "name": "线材", "category": "钢铁"},
            "HC": {"exchange": "SHFE", "name": "热轧卷板", "category": "钢铁"},
            "SS": {"exchange": "SHFE", "name": "不锈钢", "category": "钢铁"},
            "FU": {"exchange": "SHFE", "name": "燃料油", "category": "能源"},
            "BU": {"exchange": "SHFE", "name": "石油沥青", "category": "能源"},
            "RU": {"exchange": "SHFE", "name": "天然橡胶", "category": "化工"},
            "SP": {"exchange": "SHFE", "name": "纸浆", "category": "造纸"},
            # 大连商品交易所 (DCE)
            "M":  {"exchange": "DCE", "name": "豆粕", "category": "农产品"},
            "Y":  {"exchange": "DCE", "name": "豆油", "category": "农产品"},
            "A":  {"exchange": "DCE", "name": "豆一", "category": "农产品"},
            "B":  {"exchange": "DCE", "name": "豆二", "category": "农产品"},
            "P":  {"exchange": "DCE", "name": "棕榈油", "category": "农产品"},
            "C":  {"exchange": "DCE", "name": "玉米", "category": "农产品"},
            "CS": {"exchange": "DCE", "name": "玉米淀粉", "category": "农产品"},
            "JD": {"exchange": "DCE", "name": "鸡蛋", "category": "农产品"},
            "L":  {"exchange": "DCE", "name": "LLDPE", "category": "化工"},
            "PP": {"exchange": "DCE", "name": "聚丙烯", "category": "化工"},
            "V":  {"exchange": "DCE", "name": "PVC", "category": "化工"},
            "J":  {"exchange": "DCE", "name": "焦炭", "category": "能源"},
            "JM": {"exchange": "DCE", "name": "焦煤", "category": "能源"},
            "I":  {"exchange": "DCE", "name": "铁矿石", "category": "钢铁"},
            "EG": {"exchange": "DCE", "name": "乙二醇", "category": "化工"},
            "EB": {"exchange": "DCE", "name": "苯乙烯", "category": "化工"},
            "PG": {"exchange": "DCE", "name": "液化石油气", "category": "能源"},
            "LH": {"exchange": "DCE", "name": "生猪", "category": "农产品"},
            # 郑州商品交易所 (CZCE)
            "SR": {"exchange": "CZCE", "name": "白糖", "category": "农产品"},
            "CF": {"exchange": "CZCE", "name": "棉花", "category": "农产品"},
            "TA": {"exchange": "CZCE", "name": "PTA", "category": "化工"},
            "MA": {"exchange": "CZCE", "name": "甲醇", "category": "化工"},
            "ZC": {"exchange": "CZCE", "name": "动力煤", "category": "能源"},
            "FG": {"exchange": "CZCE", "name": "玻璃", "category": "建材"},
            "RM": {"exchange": "CZCE", "name": "菜籽粕", "category": "农产品"},
            "OI": {"exchange": "CZCE", "name": "菜籽油", "category": "农产品"},
            "AP": {"exchange": "CZCE", "name": "苹果", "category": "农产品"},
            "PK": {"exchange": "CZCE", "name": "花生", "category": "农产品"},
            "UR": {"exchange": "CZCE", "name": "尿素", "category": "化工"},
            "SA": {"exchange": "CZCE", "name": "纯碱", "category": "化工"},
            "SF": {"exchange": "CZCE", "name": "硅铁", "category": "钢铁"},
            "SM": {"exchange": "CZCE", "name": "锰硅", "category": "钢铁"},
            "CJ": {"exchange": "CZCE", "name": "红枣", "category": "农产品"},
            # 中国金融期货交易所 (CFFEX)
            "IF": {"exchange": "CFFEX", "name": "沪深300", "category": "金融"},
            "IH": {"exchange": "CFFEX", "name": "上证50", "category": "金融"},
            "IC": {"exchange": "CFFEX", "name": "中证500", "category": "金融"},
            "IM": {"exchange": "CFFEX", "name": "中证1000", "category": "金融"},
            "T":  {"exchange": "CFFEX", "name": "10年期国债", "category": "金融"},
            "TF": {"exchange": "CFFEX", "name": "5年期国债", "category": "金融"},
            "TS": {"exchange": "CFFEX", "name": "2年期国债", "category": "金融"},
            # 上海国际能源交易中心 (INE)
            "SC": {"exchange": "INE", "name": "原油", "category": "能源"},
            "NR": {"exchange": "INE", "name": "20号胶", "category": "化工"},
            "LU": {"exchange": "INE", "name": "低硫燃料油", "category": "能源"},
            "BC": {"exchange": "INE", "name": "国际铜", "category": "金属"},
    # 广州期货交易所 (GFEX)
            "SI": {"exchange": "GFEX", "name": "工业硅", "category": "金属"},
            "LC": {"exchange": "GFEX", "name": "碳酸锂", "category": "金属"},
        }

    def get_futures_info(self, symbol: str) -> Optional[Dict]:
        """获取期货品种基本信息"""
        return self._futures_markets.get(symbol.upper())
