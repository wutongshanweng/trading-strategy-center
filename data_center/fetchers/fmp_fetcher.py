"""
FMP Fetcher — 公司基本面数据获取器。

底层: requests (直接调用 Financial Modeling Prep API)
支持: 公司概况/财务报表/估值指标
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from ..core.base_fetcher import (
    BaseFetcher, KlineData, KlineInterval, RealtimeQuote,
    DataSourceStatus,
)

logger = logging.getLogger(__name__)


class FMPFetcher(BaseFetcher):
    """Financial Modeling Prep 基本面数据获取器"""

    name = "fmp"
    display_name = "FMP (财务报表)"
    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.environ.get("FMP_API_KEY", "")

    def _request(self, path: str, params: Dict = None) -> Optional[Dict]:
        if not self.api_key:
            logger.warning("FMP API key not set")
            return None
        url = f"{self.BASE_URL}/{path}"
        p = {"apikey": self.api_key, **(params or {})}
        try:
            resp = requests.get(url, params=p, timeout=15)
            data = resp.json()
            return data
        except Exception as e:
            logger.warning(f"FMP request failed: {e}")
            return None

    def get_company_profile(self, symbol: str) -> Dict:
        """获取公司概况"""
        data = self._request(f"profile/{symbol}")
        if isinstance(data, list) and data:
            return data[0]
        return {}

    def get_income_statement(self, symbol: str, period: str = "annual", limit: int = 5) -> pd.DataFrame:
        """获取利润表"""
        data = self._request(f"income-statement/{symbol}", {"period": period, "limit": limit})
        return pd.DataFrame(data) if data else pd.DataFrame()

    def get_balance_sheet(self, symbol: str, period: str = "annual", limit: int = 5) -> pd.DataFrame:
        """获取资产负债表"""
        data = self._request(f"balance-sheet-statement/{symbol}", {"period": period, "limit": limit})
        return pd.DataFrame(data) if data else pd.DataFrame()

    def get_cash_flow(self, symbol: str, period: str = "annual", limit: int = 5) -> pd.DataFrame:
        """获取现金流量表"""
        data = self._request(f"cash-flow-statement/{symbol}", {"period": period, "limit": limit})
        return pd.DataFrame(data) if data else pd.DataFrame()

    def get_ratios(self, symbol: str, period: str = "annual", limit: int = 5) -> pd.DataFrame:
        """获取财务比率"""
        data = self._request(f"ratios/{symbol}", {"period": period, "limit": limit})
        return pd.DataFrame(data) if data else pd.DataFrame()

    def get_stock_daily(self, symbol: str) -> pd.DataFrame:
        """获取日线数据"""
        data = self._request(f"historical-price-full/{symbol}")
        if data and "historical" in data:
            return pd.DataFrame(data["historical"])
        return pd.DataFrame()

    def get_kline(self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
                  start_date: Optional[str] = None, end_date: Optional[str] = None,
                  contract: Optional[str] = None) -> KlineData:
        df = self.get_stock_daily(symbol)
        if df.empty:
            return KlineData(symbol=symbol, interval=interval.value,
                           open=[], high=[], low=[], close=[], volume=[], timestamps=[], source=self.name)
        return KlineData(
            symbol=symbol, interval=interval.value,
            open=df.get("open", []).tolist() if "open" in df.columns else [],
            high=df.get("high", []).tolist() if "high" in df.columns else [],
            low=df.get("low", []).tolist() if "low" in df.columns else [],
            close=df.get("close", []).tolist() if "close" in df.columns else [],
            volume=df.get("volume", []).tolist() if "volume" in df.columns else [],
            timestamps=pd.to_datetime(df["date"]).tolist() if "date" in df.columns else [],
            source=self.name, contract=contract,
        )

    def get_realtime(self, symbol: str, contract: Optional[str] = None) -> RealtimeQuote:
        return RealtimeQuote(symbol=symbol, last_price=0, open_price=0, high_price=0, low_price=0, pre_close=0, volume=0, turnover=0, bid_price=0, ask_price=0, bid_volume=0, ask_volume=0, timestamp=datetime.now(), source=self.name)

    def validate(self) -> bool:
        ok = bool(self.api_key)
        self._status = DataSourceStatus.ACTIVE if ok else DataSourceStatus.DOWN
        return ok

    def _get_supported_markets(self) -> List[str]:
        return ["stock"]

    def _get_description(self) -> str:
        return "Financial Modeling Prep 基本面数据接口 (需要 API Key)，提供公司概况/财务报表/估值指标"
