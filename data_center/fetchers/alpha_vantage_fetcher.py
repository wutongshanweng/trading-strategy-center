"""
Alpha Vantage Fetcher — 全球金融数据获取器。

底层: requests (直接调用 Alpha Vantage REST API)
支持: 全球股票/外汇/加密货币/技术指标
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


class AlphaVantageFetcher(BaseFetcher):
    """Alpha Vantage 全球金融数据获取器"""

    name = "alpha_vantage"
    display_name = "Alpha Vantage"
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY", "")

    def _request(self, params: Dict) -> Optional[Dict]:
        """发送 API 请求"""
        if not self.api_key:
            logger.warning("Alpha Vantage API key not set")
            return None
        params["apikey"] = self.api_key
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=15)
            data = resp.json()
            if "Error Message" in data:
                raise RuntimeError(data["Error Message"])
            if "Note" in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
            return data
        except Exception as e:
            logger.warning(f"Alpha Vantage request failed: {e}")
            return None

    def _parse_time_series(self, data: Dict, series_key: str) -> pd.DataFrame:
        """解析时间序列数据为 DataFrame"""
        series = data.get(series_key, {})
        if not series:
            return pd.DataFrame()
        records = []
        for date_str, values in sorted(series.items()):
            record = {"date": date_str}
            for k, v in values.items():
                clean_k = k.replace(" ", "_").replace("(", "").replace(")", "")
                try:
                    record[clean_k] = float(v)
                except (ValueError, TypeError):
                    record[clean_k] = v
            records.append(record)
        return pd.DataFrame(records)

    def get_stock_daily(self, symbol: str, outputsize: str = "compact") -> pd.DataFrame:
        """获取股票日线"""
        data = self._request({
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize,
        })
        return self._parse_time_series(data, "Time Series (Daily)")

    def get_forex_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """获取实时汇率"""
        data = self._request({
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
        })
        if data and "Realtime Currency Exchange Rate" in data:
            rate_data = data["Realtime Currency Exchange Rate"]
            return float(rate_data.get("5. Exchange Rate", 0))
        return None

    def get_forex_daily(self, from_symbol: str, to_symbol: str) -> pd.DataFrame:
        """获取外汇日线"""
        data = self._request({
            "function": "FX_DAILY",
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
        })
        return self._parse_time_series(data, "Time Series FX (Daily)")

    def get_crypto_daily(self, symbol: str, market: str = "USD") -> pd.DataFrame:
        """获取加密货币日线"""
        data = self._request({
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": symbol,
            "market": market,
        })
        return self._parse_time_series(data, "Time Series (Digital Currency Daily)")

    def get_technical_indicator(self, symbol: str, function: str = "SMA",
                                 interval: str = "daily", time_period: int = 20) -> pd.DataFrame:
        """获取技术指标"""
        data = self._request({
            "function": function,
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "series_type": "close",
        })
        key = f"Technical Analysis: {function}"
        return self._parse_time_series(data, key)

    def get_kline(self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
                  start_date: Optional[str] = None, end_date: Optional[str] = None,
                  contract: Optional[str] = None) -> KlineData:
        """获取 K 线 (通过股票日线接口)"""
        df = self.get_stock_daily(symbol)
        if df.empty:
            return KlineData(symbol=symbol, interval=interval.value,
                           open=[], high=[], low=[], close=[],
                           volume=[], timestamps=[], source=self.name)
        return KlineData(
            symbol=symbol, interval=interval.value,
            open=df.get("open", df.get("1_open", [])).tolist() if not df.empty else [],
            high=df.get("high", df.get("2_high", [])).tolist() if not df.empty else [],
            low=df.get("low", df.get("3_low", [])).tolist() if not df.empty else [],
            close=df.get("close", df.get("4_close", [])).tolist() if not df.empty else [],
            volume=df.get("volume", df.get("5_volume", [])).tolist() if not df.empty else [],
            timestamps=pd.to_datetime(df["date"]).tolist() if "date" in df.columns else [],
            source=self.name, contract=contract,
        )

    def get_realtime(self, symbol: str, contract: Optional[str] = None) -> RealtimeQuote:
        return RealtimeQuote(symbol=symbol, last_price=0, open_price=0,
            high_price=0, low_price=0, pre_close=0, volume=0, turnover=0,
            bid_price=0, ask_price=0, bid_volume=0, ask_volume=0,
            timestamp=datetime.now(), source=self.name, contract=contract)

    def validate(self) -> bool:
        if not self.api_key:
            self._status = DataSourceStatus.DOWN
            return False
        try:
            data = self._request({
                "function": "TIME_SERIES_DAILY",
                "symbol": "IBM",
                "outputsize": "compact",
            })
            ok = data is not None and "Time Series (Daily)" in data
            self._status = DataSourceStatus.ACTIVE if ok else DataSourceStatus.DOWN
            return ok
        except Exception:
            self._status = DataSourceStatus.DOWN
            return False

    def _get_supported_markets(self) -> List[str]:
        return ["stock", "forex", "crypto", "index"]

    def _get_description(self) -> str:
        return "Alpha Vantage 全球金融数据接口 (需要 API Key)，提供全球股票/外汇/加密货币/技术指标"
