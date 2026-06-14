"""
Tiingo Fetcher — 美股高精度数据获取器。

底层: requests (直接调用 Tiingo REST API)
支持: 美股日线/外汇/加密货币
特点: 除权除息调整、合并/分红信息
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from ..core.base_fetcher import (
    BaseFetcher, KlineData, KlineInterval, RealtimeQuote,
    DataSourceStatus,
)

logger = logging.getLogger(__name__)


class TiingoFetcher(BaseFetcher):
    """Tiingo 美股高精度数据获取器"""

    name = "tiingo"
    display_name = "Tiingo (美股数据)"
    BASE_URL = "https://api.tiingo.com/tiingo"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.environ.get("TIINGO_API_KEY", "")
        self._session = requests.Session()
        if self.api_key:
            self._session.headers.update({"Authorization": f"Token {self.api_key}"})

    def _request(self, path: str, params: Dict = None) -> Optional[Dict]:
        if not self.api_key:
            logger.warning("Tiingo API key not set")
            return None
        url = f"{self.BASE_URL}/{path}"
        try:
            resp = self._session.get(url, params=params, timeout=15)
            return resp.json()
        except Exception as e:
            logger.warning(f"Tiingo request failed: {e}")
            return None

    def get_stock_daily(self, symbol: str, start: str = "", end: str = "") -> pd.DataFrame:
        """获取美股日线数据（已调整）"""
        data = self._request(f"daily/{symbol}/prices", {
            "startDate": start or None,
            "endDate": end or None,
        })
        if isinstance(data, list):
            df = pd.DataFrame(data)
            if not df.empty:
                col_map = {"date": "date", "open": "open", "high": "high",
                           "low": "low", "close": "close", "volume": "volume",
                           "divCash": "dividend", "splitFactor": "split_factor"}
                df = df.rename(columns={c: col_map.get(c, c) for c in df.columns})
            return df
        return pd.DataFrame()

    def get_forex_prices(self, pair: str, start: str = "", end: str = "") -> pd.DataFrame:
        """获取外汇数据"""
        data = self._request(f"fx/{pair}/prices", {
            "startDate": start or None,
            "endDate": end or None,
        })
        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame()

    def get_crypto_prices(self, symbol: str, start: str = "", end: str = "",
                           resample_freq: str = "1day") -> pd.DataFrame:
        """获取加密货币数据"""
        data = self._request(f"crypto/prices", {
            "tickers": symbol,
            "startDate": start or None,
            "endDate": end or None,
            "resampleFreq": resample_freq,
        })
        if isinstance(data, list) and data:
            prices = data[0].get("priceData", [])
            return pd.DataFrame(prices)
        return pd.DataFrame()

    def get_ticker_metadata(self, symbol: str) -> Dict:
        """获取标的信息"""
        data = self._request(f"daily/{symbol}")
        if isinstance(data, list) and data:
            return data[0]
        return {}

    def get_kline(self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
                  start_date: Optional[str] = None, end_date: Optional[str] = None,
                  contract: Optional[str] = None) -> KlineData:
        df = self.get_stock_daily(symbol, start=start_date or "", end=end_date or "")
        if df.empty:
            return KlineData(symbol=symbol, interval=interval.value,
                           open=[], high=[], low=[], close=[], volume=[], timestamps=[], source=self.name)
        return KlineData(
            symbol=symbol, interval=interval.value,
            open=df["open"].tolist() if "open" in df.columns else [],
            high=df["high"].tolist() if "high" in df.columns else [],
            low=df["low"].tolist() if "low" in df.columns else [],
            close=df["close"].tolist() if "close" in df.columns else [],
            volume=df["volume"].tolist() if "volume" in df.columns else [],
            timestamps=pd.to_datetime(df["date"]).tolist() if "date" in df.columns else [],
            source=self.name, contract=contract,
        )

    def get_realtime(self, symbol: str, contract=None) -> RealtimeQuote:
        return RealtimeQuote(symbol=symbol, last_price=0, open_price=0, high_price=0, low_price=0,
            pre_close=0, volume=0, turnover=0, bid_price=0, ask_price=0, bid_volume=0, ask_volume=0,
            timestamp=datetime.now(), source=self.name)

    def validate(self) -> bool:
        ok = bool(self.api_key)
        self._status = DataSourceStatus.ACTIVE if ok else DataSourceStatus.DOWN
        return ok

    def _get_supported_markets(self) -> List[str]:
        return ["stock", "forex", "crypto"]

    def _get_description(self) -> str:
        return "Tiingo 美股高精度数据接口 (需要 API Key)，提供除权调整后的日线/外汇/加密货币数据"
