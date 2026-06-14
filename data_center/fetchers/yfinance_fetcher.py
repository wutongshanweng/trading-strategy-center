"""
YFinance Fetcher — 国际市场数据获取器。

底层: yfinance 库
支持: 国际期货/股票/ETF/加密货币
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.base_fetcher import (
    BaseFetcher, KlineData, KlineInterval, RealtimeQuote,
    DataSourceStatus,
)

logger = logging.getLogger(__name__)


class YFinanceFetcher(BaseFetcher):
    """Yahoo Finance 国际数据获取器"""

    name = "yfinance"
    display_name = "Yahoo Finance"

    # 国际期货符号映射 (yfinance 格式)
    FUTURES_SYMBOLS: Dict[str, str] = {
        "GC": "GC=F",      # 黄金
        "SI": "SI=F",      # 白银
        "PL": "PL=F",      # 铂金
        "PA": "PA=F",      # 钯金
        "CL": "CL=F",      # WTI原油
        "HO": "HO=F",      # 取暖油
        "RB": "RB=F",      # RBOB汽油
        "NG": "NG=F",      # 天然气
        "ZC": "ZC=F",      # 玉米
        "ZW": "ZW=F",      # 小麦
        "ZS": "ZS=F",      # 大豆
        "ZL": "ZL=F",      # 豆油
        "ZM": "ZM=F",      # 豆粕
        "CC": "CC=F",      # 可可
        "KC": "KC=F",      # 咖啡
        "SB": "SB=F",      # 糖
        "CT": "CT=F",      # 棉花
        "LB": "LB=F",      # 木材
        "OJ": "OJ=F",      # 橙汁
        "ES": "ES=F",      # E-mini S&P 500
        "NQ": "NQ=F",      # Nasdaq 100
        "YM": "YM=F",      # Dow Jones
        "RTY": "RTY=F",    # Russell 2000
        "FDAX": "FDAX=F",  # DAX
        "STXE": "STXE=F",  # Euro Stoxx 50
        "DX-Y": "DX-Y.NYB",# 美元指数
        "EUR": "EURUSD=X", # 欧元/美元
        "GBP": "GBPUSD=X", # 英镑/美元
        "JPY": "USDJPY=X", # 美元/日元
        "AUD": "AUDUSD=X", # 澳元/美元
        "BTC": "BTC-USD",  # 比特币
        "ETH": "ETH-USD",  # 以太坊
    }

    _yf = None

    def _get_yf(self):
        if self._yf is None:
            try:
                import yfinance as yf
                self._yf = yf
            except ImportError:
                raise ImportError("yfinance 未安装: pip install yfinance")
        return self._yf

    def _resolve_symbol(self, symbol: str) -> str:
        """解析为 yfinance 可识别的符号"""
        return self.FUTURES_SYMBOLS.get(symbol.upper(), symbol)

    def get_kline(self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
                  start_date: Optional[str] = None, end_date: Optional[str] = None,
                  contract: Optional[str] = None) -> KlineData:
        """获取 K 线数据"""
        yf = self._get_yf()
        yf_symbol = self._resolve_symbol(symbol)

        # 周期映射
        period_map = {
            "5m": "5m", "15m": "15m", "30m": "30m", "60m": "60m",
            "1d": "1d", "1w": "1wk", "1M": "1mo",
        }
        yf_interval = period_map.get(interval.value, "1d")

        try:
            ticker = yf.Ticker(yf_symbol)

            if start_date and end_date:
                df = ticker.history(start=start_date, end=end_date, interval=yf_interval)
            else:
                df = ticker.history(period="2y", interval=yf_interval)

            if df.empty:
                return KlineData(symbol=symbol, interval=interval.value,
                                 open=[], high=[], low=[], close=[],
                                 volume=[], timestamps=[], source=self.name)

            return KlineData(
                symbol=symbol, interval=interval.value,
                open=df["Open"].tolist(),
                high=df["High"].tolist(),
                low=df["Low"].tolist(),
                close=df["Close"].tolist(),
                volume=df["Volume"].tolist(),
                timestamps=df.index.tolist(),
                source=self.name, contract=contract,
            )
        except Exception as e:
            logger.warning(f"YFinance kline failed for {symbol}: {e}")
            return KlineData(symbol=symbol, interval=interval.value,
                             open=[], high=[], low=[], close=[],
                             volume=[], timestamps=[], source=self.name)

    def get_realtime(self, symbol: str, contract: Optional[str] = None) -> RealtimeQuote:
        """获取实时行情"""
        yf = self._get_yf()
        yf_symbol = self._resolve_symbol(symbol)

        try:
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info or {}
            fast_info = ticker.fast_info if hasattr(ticker, 'fast_info') else None

            last_price = fast_info.last_price if fast_info and hasattr(fast_info, 'last_price') else info.get("regularMarketPrice", 0)
            prev_close = fast_info.previous_close if fast_info and hasattr(fast_info, 'previous_close') else info.get("regularMarketPreviousClose", 0)
            volume = fast_info.volume if fast_info and hasattr(fast_info, 'volume') else info.get("regularMarketVolume", 0)

            return RealtimeQuote(
                symbol=symbol,
                last_price=float(last_price or 0),
                open_price=float(info.get("regularMarketOpen", 0)),
                high_price=float(info.get("regularMarketDayHigh", 0)),
                low_price=float(info.get("regularMarketDayLow", 0)),
                pre_close=float(prev_close or 0),
                volume=int(volume or 0),
                turnover=float(last_price or 0) * int(volume or 0),
                bid_price=float(info.get("bid", 0)),
                ask_price=float(info.get("ask", 0)),
                bid_volume=int(info.get("bidSize", 0)),
                ask_volume=int(info.get("askSize", 0)),
                timestamp=datetime.now(),
                source=self.name, contract=contract,
            )
        except Exception as e:
            logger.warning(f"YFinance realtime failed for {symbol}: {e}")
            return RealtimeQuote(symbol=symbol, last_price=0, open_price=0,
                high_price=0, low_price=0, pre_close=0, volume=0, turnover=0,
                bid_price=0, ask_price=0, bid_volume=0, ask_volume=0,
                timestamp=datetime.now(), source=self.name, contract=contract)

    def get_info(self, symbol: str) -> Dict:
        """获取标的信息"""
        yf = self._get_yf()
        try:
            ticker = yf.Ticker(self._resolve_symbol(symbol))
            return ticker.info or {}
        except Exception:
            return {}

    def validate(self) -> bool:
        try:
            yf = self._get_yf()
            ticker = yf.Ticker("GC=F")
            info = ticker.info
            return bool(info and info.get("regularMarketPrice"))
        except Exception:
            self._status = DataSourceStatus.DOWN
            return False

    def list_futures_symbols(self) -> Dict[str, str]:
        return dict(self.FUTURES_SYMBOLS)

    def _get_supported_markets(self) -> List[str]:
        return ["futures", "stock", "etf", "crypto", "forex", "index"]

    def _get_description(self) -> str:
        return "Yahoo Finance 数据接口，提供国际期货/股票/ETF/加密货币/外汇等全球市场数据"
