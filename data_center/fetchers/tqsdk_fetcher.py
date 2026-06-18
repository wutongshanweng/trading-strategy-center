"""
TqSdk Fetcher — 天勤 中国期货 K线/Tick/主力连续 (需账户)。

底层: tqsdk (TQ_ACCOUNT / TQ_PASSWORD 环境变量或构造参数)
覆盖: 期货 1m/5m/15m/30m/1h/1d K线, Tick, 主力连续合约 (KQ.m@)
注意: 免费账户仅近期数据; 深度历史用 Tushare/akshare 回补。
合约格式: SHFE.rb2510, DCE.m2509, CZCE.SR509, CFFEX.IF2509, INE.sc2509
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import List, Optional

import pandas as pd

from ..core.base_fetcher import (
    BaseFetcher, KlineData, KlineInterval, RealtimeQuote, DataSourceStatus,
)

logger = logging.getLogger(__name__)

# 品种 -> 交易所前缀 (TqSdk 合约需带交易所)
_EXCHANGE_PREFIX = {
    # SHFE
    "CU": "SHFE", "AL": "SHFE", "ZN": "SHFE", "PB": "SHFE", "NI": "SHFE", "SN": "SHFE",
    "AU": "SHFE", "AG": "SHFE", "RB": "SHFE", "HC": "SHFE", "SS": "SHFE", "RU": "SHFE",
    "BU": "SHFE", "FU": "SHFE", "SP": "SHFE",
    # DCE
    "M": "DCE", "Y": "DCE", "A": "DCE", "B": "DCE", "P": "DCE", "C": "DCE", "CS": "DCE",
    "JD": "DCE", "LH": "DCE", "I": "DCE", "J": "DCE", "JM": "DCE", "L": "DCE", "PP": "DCE",
    "V": "DCE", "EG": "DCE", "EB": "DCE", "PG": "DCE",
    # CZCE
    "SR": "CZCE", "CF": "CZCE", "CY": "CZCE", "TA": "CZCE", "MA": "CZCE", "FG": "CZCE",
    "SA": "CZCE", "RM": "CZCE", "OI": "CZCE", "ZC": "CZCE", "UR": "CZCE", "AP": "CZCE",
    "CJ": "CZCE", "SF": "CZCE", "SM": "CZCE", "PF": "CZCE", "PK": "CZCE",
    # CFFEX
    "IF": "CFFEX", "IH": "CFFEX", "IC": "CFFEX", "IM": "CFFEX",
    "TS": "CFFEX", "TF": "CFFEX", "T": "CFFEX", "TL": "CFFEX",
    # INE
    "SC": "INE", "NR": "INE", "LU": "INE", "BC": "INE",
    # GFEX
    "SI": "GFEX", "LC": "GFEX",
}

_DURATION = {
    KlineInterval.M1: 60, KlineInterval.M5: 300, KlineInterval.M15: 900,
    KlineInterval.M30: 1800, KlineInterval.M60: 3600, KlineInterval.DAY: 86400,
}


class TqSdkFetcher(BaseFetcher):
    """天勤 TqSdk 期货数据获取器。"""

    name = "tqsdk"
    display_name = "TqSdk 天勤"

    def __init__(self, account: Optional[str] = None, password: Optional[str] = None):
        super().__init__()
        self._account = account or os.getenv("TQ_ACCOUNT", "")
        self._password = password or os.getenv("TQ_PASSWORD", "")
        self._api = None

    def _get_api(self):
        if self._api is None:
            if not (self._account and self._password):
                raise RuntimeError("TqSdk 账户未配置 (设置 TQ_ACCOUNT / TQ_PASSWORD)")
            from tqsdk import TqApi, TqAuth
            self._api = TqApi(auth=TqAuth(self._account, self._password))
        return self._api

    def _full_symbol(self, symbol: str, contract: Optional[str], main: bool = False) -> str:
        """品种/合约 -> TqSdk 全代码。main=True 返回主力连续 KQ.m@EXCH.code。"""
        prod = symbol.upper()
        exch = _EXCHANGE_PREFIX.get(prod)
        if main and exch:
            return f"KQ.m@{exch}.{prod.lower() if exch != 'CZCE' else prod}"
        code = (contract or symbol).upper()
        # 已带交易所前缀
        if "." in code:
            return code
        prod_letters = "".join(c for c in code if c.isalpha())
        exch = _EXCHANGE_PREFIX.get(prod_letters, exch)
        if not exch:
            raise ValueError(f"未知品种交易所: {symbol}")
        # CZCE 大写, 其余小写
        norm = code if exch == "CZCE" else code.lower()
        return f"{exch}.{norm}"

    def get_kline(
        self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
        start_date: Optional[str] = None, end_date: Optional[str] = None,
        contract: Optional[str] = None,
    ) -> KlineData:
        empty = KlineData(symbol=symbol, interval=interval.value, open=[], high=[], low=[],
                          close=[], volume=[], timestamps=[], source=self.name, contract=contract)
        dur = _DURATION.get(interval)
        if dur is None:
            logger.warning(f"TqSdk 不支持周期 {interval.value}")
            return empty
        try:
            api = self._get_api()
            full = self._full_symbol(symbol, contract, main=(contract is None))
            df = api.get_kline_serial(full, duration_seconds=dur, data_length=8000)
            if df is None or df.empty:
                return empty
            df = df.dropna(subset=["close"])
            ts = pd.to_datetime(df["datetime"], unit="ns")
            return KlineData(
                symbol=symbol, interval=interval.value,
                open=df["open"].tolist(), high=df["high"].tolist(),
                low=df["low"].tolist(), close=df["close"].tolist(),
                volume=df["volume"].tolist(), timestamps=ts.tolist(),
                source=self.name, contract=contract,
            )
        except Exception as e:
            logger.warning(f"TqSdk get_kline failed for {symbol}: {e}")
            return empty

    def get_realtime(self, symbol: str, contract: Optional[str] = None) -> RealtimeQuote:
        try:
            api = self._get_api()
            full = self._full_symbol(symbol, contract, main=(contract is None))
            q = api.get_quote(full)
            return RealtimeQuote(
                symbol=symbol, last_price=float(q.last_price or 0),
                open_price=float(q.open or 0), high_price=float(q.highest or 0),
                low_price=float(q.lowest or 0), pre_close=float(q.pre_close or 0),
                volume=int(q.volume or 0), turnover=float(q.amount or 0),
                bid_price=float(q.bid_price1 or 0), ask_price=float(q.ask_price1 or 0),
                bid_volume=int(q.bid_volume1 or 0), ask_volume=int(q.ask_volume1 or 0),
                timestamp=datetime.now(), source=self.name, contract=contract,
            )
        except Exception as e:
            logger.warning(f"TqSdk get_realtime failed for {symbol}: {e}")
            raise

    def close(self):
        if self._api is not None:
            try:
                self._api.close()
            finally:
                self._api = None

    def validate(self) -> bool:
        try:
            self._get_api()
            self._status = DataSourceStatus.ACTIVE
            return True
        except Exception as e:
            logger.warning(f"TqSdk validate failed: {e}")
            self._status = DataSourceStatus.DOWN
            return False

    @property
    def info(self):
        i = super().info
        i.requires_api_key = True
        return i

    def _get_supported_markets(self) -> List[str]:
        return ["futures"]

    def _get_description(self) -> str:
        return "TqSdk 天勤 — 期货K线/Tick/主力连续 (需 TQ_ACCOUNT/TQ_PASSWORD)"
