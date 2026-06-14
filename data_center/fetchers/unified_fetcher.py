"""
Unified Fetcher — 统一路由接口。

根据品种自动选择最优数据源:
- 中国期货 (字母代码): AKShare → TDX
- A股 (6位数字): AKShare
- 国际期货 (代码+F): YFinance
- 美股 (字母): YFinance → Tiingo
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.base_fetcher import (
    BaseFetcher, KlineData, KlineInterval, RealtimeQuote,
    DataSourceStatus, DataSourceInfo,
)

logger = logging.getLogger(__name__)


class UnifiedFetcher(BaseFetcher):
    """
    统一数据获取器 — 自动路由到最佳数据源。
    
    无需手动选择数据源，根据品种代码自动路由。
    """

    name = "unified"
    display_name = "智能数据路由"

    # 中国期货品种代码列表 (用于识别)
    CHINA_FUTURES_CODES = {
        "CU","AL","ZN","PB","NI","SN","AU","AG","RB","WR","HC","SS",
        "FU","BU","RU","SP","M","Y","A","B","P","C","CS","JD","L",
        "PP","V","J","JM","I","EG","EB","PG","LH","SR","CF","TA",
        "MA","ZC","FG","RM","OI","AP","PK","UR","SA","SF","SM","CJ",
        "IF","IH","IC","IM","T","TF","TS","SC","NR","LU","BC","SI","LC",
    }

    def __init__(self):
        super().__init__()
        self._fetchers: Dict[str, BaseFetcher] = {}
        self._initialized = False

    def _init_fetchers(self):
        if self._initialized:
            return
        try:
            from .akshare_fetcher import AKShareFetcher
            from .yfinance_fetcher import YFinanceFetcher
            self._fetchers["akshare"] = AKShareFetcher()
            self._fetchers["yfinance"] = YFinanceFetcher()
        except Exception as e:
            logger.warning(f"Fetcher init warning: {e}")
        self._initialized = True

    def _identify_symbol(self, symbol: str) -> str:
        """识别品种类型"""
        sym = symbol.upper().split(".")[0]
        # 国际期货 (包含 =F)
        if "=F" in symbol.upper() or "=X" in symbol.upper():
            return "international_futures"
        # A股 (6位纯数字)
        if sym.isdigit() and len(sym) == 6:
            return "china_stock"
        # 中国期货
        base = sym.rstrip("0123456789")
        if base in self.CHINA_FUTURES_CODES:
            return "china_futures"
        # 美股 (字母 ≤ 8)
        if sym.isalpha() and len(sym) <= 8:
            return "us_stock"
        # 默认
        return "unknown"

    def _get_fetcher(self, symbol: str) -> BaseFetcher:
        """根据品种获取最佳数据源"""
        self._init_fetchers()
        category = self._identify_symbol(symbol)
        
        if category in ("china_futures", "china_stock"):
            return self._fetchers.get("akshare", list(self._fetchers.values())[0] if self._fetchers else self)
        elif category in ("international_futures", "us_stock"):
            return self._fetchers.get("yfinance", list(self._fetchers.values())[0] if self._fetchers else self)
        else:
            return list(self._fetchers.values())[0] if self._fetchers else self

    def get_kline(self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
                  start_date: Optional[str] = None, end_date: Optional[str] = None,
                  contract: Optional[str] = None) -> KlineData:
        fetcher = self._get_fetcher(symbol)
        if fetcher and fetcher is not self:
            return fetcher.get_kline(symbol, interval, start_date, end_date, contract)
        return KlineData(symbol=symbol, interval=interval.value,
                        open=[], high=[], low=[], close=[], volume=[], timestamps=[], source=self.name)

    def get_realtime(self, symbol: str, contract: Optional[str] = None) -> RealtimeQuote:
        fetcher = self._get_fetcher(symbol)
        if fetcher and fetcher is not self:
            return fetcher.get_realtime(symbol, contract)
        return RealtimeQuote(symbol=symbol, last_price=0, open_price=0, high_price=0, low_price=0,
            pre_close=0, volume=0, turnover=0, bid_price=0, ask_price=0, bid_volume=0, ask_volume=0,
            timestamp=datetime.now(), source=self.name)

    def get_source_name(self, symbol: str) -> str:
        """获取将用于指定品种的数据源名称"""
        fetcher = self._get_fetcher(symbol)
        return fetcher.name if fetcher and fetcher is not self else "none"

    def validate(self) -> bool:
        self._init_fetchers()
        any_ok = False
        for f in self._fetchers.values():
            if f.validate():
                any_ok = True
        self._status = DataSourceStatus.ACTIVE if any_ok else DataSourceStatus.DEGRADED
        return any_ok

    @staticmethod
    def get_data_source_info() -> Dict[str, Dict]:
        """获取数据源概述信息"""
        return {
            "akshare": {"name": "AKShare", "description": "中国市场 (期货/股票/期权)", "free": True, "api_key": False},
            "yfinance": {"name": "Yahoo Finance", "description": "国际市场 (期货/股票/ETF)", "free": True, "api_key": False},
            "tdx": {"name": "TDX (通达信)", "description": "中国实时行情 (期货/股票)", "free": True, "api_key": False},
            "alpha_vantage": {"name": "Alpha Vantage", "description": "全球金融数据", "free": True, "api_key": True},
            "fmp": {"name": "FMP", "description": "公司基本面数据", "free": False, "api_key": True},
            "fred": {"name": "FRED", "description": "美国经济数据", "free": True, "api_key": True},
            "eia": {"name": "EIA", "description": "美国能源数据", "free": True, "api_key": True},
            "cftc": {"name": "CFTC", "description": "持仓报告(COT)", "free": True, "api_key": False},
            "tiingo": {"name": "Tiingo", "description": "美股高精度数据", "free": False, "api_key": True},
        }

    def _get_supported_markets(self) -> List[str]:
        return ["futures", "stock", "options", "forex", "crypto", "index"]

    def _get_description(self) -> str:
        return "智能数据路由接口，自动识别品种类型并路由到最优数据源"
