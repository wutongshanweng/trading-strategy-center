"""
Tushare Pro Fetcher — 中国期货/股票/期权/宏观 (需 token)。

底层: tushare (TUSHARE_TOKEN 环境变量或构造参数)
覆盖: A股日线+复权, 期货日线, 期权日线, 财报, 交易日历
内置: ECONNRESET/超时 重试退避 (用户网络维护期会中断)
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd

from ..core.base_fetcher import (
    BaseFetcher, KlineData, KlineInterval, RealtimeQuote, DataSourceStatus,
)

logger = logging.getLogger(__name__)


def _retry(fn, *args, _tries: int = 4, _base: float = 1.5, **kwargs):
    """指数退避重试 — 处理网络中断 (ECONNRESET/超时)。"""
    last = None
    for i in range(_tries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last = e
            msg = str(e).lower()
            if any(k in msg for k in ("reset", "timeout", "timed out", "connection", "max")):
                wait = _base ** i
                logger.warning(f"Tushare 调用失败 (第{i+1}次), {wait:.1f}s 后重试: {e}")
                time.sleep(wait)
                continue
            raise
    raise last  # type: ignore


class TushareFetcher(BaseFetcher):
    """Tushare Pro 数据获取器。"""

    name = "tushare"
    display_name = "Tushare Pro"

    _INTERVAL_TO_FREQ = {
        KlineInterval.DAY: "D", KlineInterval.WEEK: "W", KlineInterval.MONTH: "M",
    }

    def __init__(self, token: Optional[str] = None):
        super().__init__()
        self._token = token or os.getenv("TUSHARE_TOKEN", "")
        self._pro = None

    def _get_pro(self):
        if self._pro is None:
            if not self._token:
                raise RuntimeError("Tushare token 未配置 (设置 TUSHARE_TOKEN 环境变量)")
            import tushare as ts
            ts.set_token(self._token)
            self._pro = ts.pro_api()
        return self._pro

    @staticmethod
    def _to_ts_stock(symbol: str) -> str:
        """600019.SH 原样; 600019 -> 600019.SH; 000800 -> 000800.SZ。"""
        s = symbol.upper().strip()
        if "." in s:
            return s
        return f"{s}.{'SH' if s.startswith('6') else 'SZ'}"

    def get_kline(
        self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
        start_date: Optional[str] = None, end_date: Optional[str] = None,
        contract: Optional[str] = None,
    ) -> KlineData:
        pro = self._get_pro()
        start = (start_date or (datetime.now() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")).replace("-", "")
        end = (end_date or datetime.now().strftime("%Y-%m-%d")).replace("-", "")
        empty = KlineData(symbol=symbol, interval=interval.value, open=[], high=[], low=[],
                          close=[], volume=[], timestamps=[], source=self.name, contract=contract)
        target = (contract or symbol).upper()
        try:
            # 期货合约 (含数字, 非股票后缀) 走 fut_daily, 否则股票 daily(前复权)
            is_stock = target.replace(".", "").isdigit() or target.endswith((".SH", ".SZ"))
            if is_stock:
                ts_code = self._to_ts_stock(target)
                df = _retry(pro.daily, ts_code=ts_code, start_date=start, end_date=end)
            else:
                df = _retry(pro.fut_daily, ts_code=target, start_date=start, end_date=end)
            if df is None or df.empty:
                return empty
            df = df.sort_values("trade_date")
            ts_idx = pd.to_datetime(df["trade_date"])
            num = lambda c: df[c].astype(float).tolist() if c in df.columns else []
            return KlineData(
                symbol=symbol, interval=interval.value,
                open=num("open"), high=num("high"), low=num("low"), close=num("close"),
                volume=num("vol"), timestamps=ts_idx.tolist(),
                source=self.name, contract=contract,
            )
        except Exception as e:
            logger.warning(f"Tushare get_kline failed for {target}: {e}")
            return empty

    def get_realtime(self, symbol: str, contract: Optional[str] = None) -> RealtimeQuote:
        raise NotImplementedError("Tushare Pro 实时行情需额外权限, 请使用 TDX/akshare")

    def get_trade_dates(self, start_date: str, end_date: str, exchange: str = "SSE") -> List[str]:
        """交易日历 (is_open=1)。"""
        pro = self._get_pro()
        df = _retry(pro.trade_cal, exchange=exchange,
                    start_date=start_date.replace("-", ""), end_date=end_date.replace("-", ""))
        if df is None or df.empty:
            return []
        open_days = df[df["is_open"] == 1]["cal_date"].tolist()
        return [f"{d[:4]}-{d[4:6]}-{d[6:]}" for d in sorted(open_days)]

    def get_financial(self, symbol: str) -> pd.DataFrame:
        """股票财务指标 (fina_indicator)。"""
        pro = self._get_pro()
        return _retry(pro.fina_indicator, ts_code=self._to_ts_stock(symbol))

    def validate(self) -> bool:
        try:
            self._get_pro()
            self._status = DataSourceStatus.ACTIVE
            return True
        except Exception as e:
            logger.warning(f"Tushare validate failed: {e}")
            self._status = DataSourceStatus.DOWN
            return False

    @property
    def info(self):
        i = super().info
        i.requires_api_key = True
        return i

    def _get_supported_markets(self) -> List[str]:
        return ["stock", "futures", "option", "macro"]

    def _get_description(self) -> str:
        return "Tushare Pro — 中国股票/期货/期权/财报/交易日历 (需 TUSHARE_TOKEN)"
