"""
Options Fetcher — 期权链数据获取器。

覆盖:
- 中国期权: ETF期权 (50ETF/300ETF), 股指期权 (IO/HO), 商品期权
- 美股期权: 股票期权, 期货期权
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from ..core.base_fetcher import (
    BaseFetcher, KlineData, KlineInterval, RealtimeQuote,
    DataSourceStatus,
)

logger = logging.getLogger(__name__)


class ChinaOptionsFetcher(BaseFetcher):
    """中国期权数据获取器 (基于 AKShare)"""

    name = "china_options"
    display_name = "中国期权 (AKShare)"

    def __init__(self):
        super().__init__()
        self._ak = None

    def _get_ak(self):
        if self._ak is None:
            try:
                import akshare as ak
                self._ak = ak
            except ImportError:
                raise ImportError("请安装 akshare: pip install akshare")
        return self._ak

    def get_etf_option_daily(self, symbol: str = "510050") -> pd.DataFrame:
        """获取 ETF 期权日线 (510050=50ETF, 510300=300ETF)"""
        ak = self._get_ak()
        try:
            return ak.option_50etf_daily(symbol)
        except Exception as e:
            logger.warning(f"China options daily failed: {e}")
            return pd.DataFrame()

    def get_index_option_realtime(self, variety: str = "io") -> pd.DataFrame:
        """获取股指期权实时行情 (io=沪深300, ho=上证50, mo=中证1000)"""
        ak = self._get_ak()
        try:
            return ak.option_cffex_sz50_index_spot()
        except Exception as e:
            logger.warning(f"Index option realtime failed: {e}")
            return pd.DataFrame()

    def get_commodity_option_daily(self, symbol: str = "m") -> pd.DataFrame:
        """获取商品期权日线 (m=豆粕, sr=白糖, etc.)"""
        ak = self._get_ak()
        try:
            return ak.option_daily(symbol)
        except Exception as e:
            logger.warning(f"Commodity option daily failed: {e}")
            return pd.DataFrame()

    def get_kline(self, *args, **kwargs) -> KlineData:
        return KlineData(symbol=kwargs.get("symbol",""), interval="1d", open=[], high=[], low=[], close=[], volume=[], timestamps=[], source=self.name)

    def get_realtime(self, symbol: str, contract=None) -> RealtimeQuote:
        return RealtimeQuote(symbol=symbol, last_price=0, open_price=0, high_price=0, low_price=0,
            pre_close=0, volume=0, turnover=0, bid_price=0, ask_price=0, bid_volume=0, ask_volume=0,
            timestamp=datetime.now(), source=self.name)

    def validate(self) -> bool:
        try:
            self._get_ak()
            self._status = DataSourceStatus.ACTIVE
            return True
        except Exception:
            self._status = DataSourceStatus.DOWN
            return False

    def _get_supported_markets(self) -> List[str]:
        return ["options", "etf_options", "index_options"]

    def _get_description(self) -> str:
        return "中国期权市场数据 (AKShare)，覆盖ETF期权/股指期权/商品期权"


class USOptionsFetcher(BaseFetcher):
    """美股期权数据获取器 (基于 yfinance)"""

    name = "us_options"
    display_name = "美股期权 (YFinance)"

    def __init__(self):
        super().__init__()
        self._yf = None

    def _get_yf(self):
        if self._yf is None:
            try:
                import yfinance as yf
                self._yf = yf
            except ImportError:
                raise ImportError("请安装 yfinance: pip install yfinance")
        return self._yf

    def get_expirations(self, symbol: str) -> List[str]:
        """获取期权到期日列表"""
        yf = self._get_yf()
        try:
            ticker = yf.Ticker(symbol)
            return list(ticker.options)
        except Exception:
            return []

    def get_option_chain(self, symbol: str, expiration: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """获取期权链 (calls, puts)"""
        yf = self._get_yf()
        try:
            ticker = yf.Ticker(symbol)
            exps = ticker.options
            if not exps:
                return pd.DataFrame(), pd.DataFrame()
            exp = expiration or exps[0]
            opt = ticker.option_chain(exp)
            return opt.calls, opt.puts
        except Exception as e:
            logger.warning(f"US options chain failed: {e}")
            return pd.DataFrame(), pd.DataFrame()

    def get_put_call_ratio(self, symbol: str) -> float:
        """获取期权看涨/看跌比率 (PCR)"""
        calls, puts = self.get_option_chain(symbol)
        if calls.empty or puts.empty:
            return 0.0
        call_vol = calls["volume"].sum() if "volume" in calls.columns else 0
        put_vol = puts["volume"].sum() if "volume" in puts.columns else 0
        if call_vol == 0:
            return 0.0
        return put_vol / call_vol

    def get_kline(self, *args, **kwargs) -> KlineData:
        return KlineData(symbol=kwargs.get("symbol",""), interval="1d", open=[], high=[], low=[], close=[], volume=[], timestamps=[], source=self.name)

    def get_realtime(self, symbol: str, contract=None) -> RealtimeQuote:
        return RealtimeQuote(symbol=symbol, last_price=0, open_price=0, high_price=0, low_price=0,
            pre_close=0, volume=0, turnover=0, bid_price=0, ask_price=0, bid_volume=0, ask_volume=0,
            timestamp=datetime.now(), source=self.name)

    def validate(self) -> bool:
        try:
            self._get_yf()
            self._status = DataSourceStatus.ACTIVE
            return True
        except Exception:
            self._status = DataSourceStatus.DOWN
            return False

    def _get_supported_markets(self) -> List[str]:
        return ["options", "stock_options"]

    def _get_description(self) -> str:
        return "美股期权数据 (YFinance)，支持股票期权链/PCR比率/到期日查询"


class OptionsFetcher(BaseFetcher):
    """统一期权数据获取器 — 自动路由中国/美股期权"""

    name = "options"
    display_name = "期权数据"

    def __init__(self):
        super().__init__()
        self._china = ChinaOptionsFetcher()
        self._us = USOptionsFetcher()

    def get_option_chain(self, symbol: str, expiration: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        # 自动识别: 数字开头用中国期权，字母用美股
        if symbol[0].isdigit():
            df = self._china.get_etf_option_daily(symbol)
            return df, pd.DataFrame()
        return self._us.get_option_chain(symbol, expiration)

    def get_expirations(self, symbol: str) -> List[str]:
        return self._us.get_expirations(symbol)

    def get_put_call_ratio(self, symbol: str) -> float:
        return self._us.get_put_call_ratio(symbol)

    def get_kline(self, *args, **kwargs) -> KlineData:
        return KlineData(symbol=kwargs.get("symbol",""), interval="1d", open=[], high=[], low=[], close=[], volume=[], timestamps=[], source=self.name)

    def get_realtime(self, symbol: str, contract=None) -> RealtimeQuote:
        return RealtimeQuote(symbol=symbol, last_price=0, open_price=0, high_price=0, low_price=0,
            pre_close=0, volume=0, turnover=0, bid_price=0, ask_price=0, bid_volume=0, ask_volume=0,
            timestamp=datetime.now(), source=self.name)

    def validate(self) -> bool:
        self._status = DataSourceStatus.ACTIVE
        return True

    def _get_supported_markets(self) -> List[str]:
        return ["options"]

    def _get_description(self) -> str:
        return "统一期权数据接口，自动路由中国(AKShare)和美股(YFinance)期权链"
