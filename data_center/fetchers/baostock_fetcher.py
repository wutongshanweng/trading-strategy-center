"""
BaoStock Fetcher — 中国 A 股历史数据 (免费, 无需密钥)。

底层: baostock
覆盖: A股日/周/月/分钟K线 (前复权/后复权/不复权) + 交易日历
代码格式: 600019.SH -> sh.600019;  000800.SZ -> sz.000800
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd

from ..core.base_fetcher import (
    BaseFetcher, KlineData, KlineInterval, RealtimeQuote,
    DataSourceStatus,
)

logger = logging.getLogger(__name__)

# baostock 单进程全局登录, 用锁保护
_bs_lock = threading.Lock()


class BaoStockFetcher(BaseFetcher):
    """BaoStock A股数据获取器。"""

    name = "baostock"
    display_name = "BaoStock"

    _INTERVAL_MAP = {
        KlineInterval.DAY: "d", KlineInterval.WEEK: "w", KlineInterval.MONTH: "m",
        KlineInterval.M5: "5", KlineInterval.M15: "15",
        KlineInterval.M30: "30", KlineInterval.M60: "60",
    }
    _bs = None
    _logged_in = False

    def _get_bs(self):
        if self._bs is None:
            import baostock as bs
            self._bs = bs
        if not BaoStockFetcher._logged_in:
            with _bs_lock:
                if not BaoStockFetcher._logged_in:
                    res = self._bs.login()
                    if res.error_code != "0":
                        raise RuntimeError(f"baostock 登录失败: {res.error_msg}")
                    BaoStockFetcher._logged_in = True
        return self._bs

    @staticmethod
    def _to_bs_code(symbol: str) -> str:
        """600019.SH -> sh.600019;  000800.SZ -> sz.000800;  600019 -> 自动判market。"""
        s = symbol.upper().strip()
        if "." in s:
            code, mkt = s.split(".")
            return f"{mkt.lower()}.{code}"
        # 无后缀: 6 开头沪市, 其余深市
        return f"{'sh' if s.startswith('6') else 'sz'}.{s}"

    def get_kline(
        self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
        start_date: Optional[str] = None, end_date: Optional[str] = None,
        contract: Optional[str] = None,
    ) -> KlineData:
        bs = self._get_bs()
        code = self._to_bs_code(symbol)
        freq = self._INTERVAL_MAP.get(interval, "d")
        start = start_date or (datetime.now() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")
        end = end_date or datetime.now().strftime("%Y-%m-%d")

        if freq in ("d", "w", "m"):
            fields = "date,open,high,low,close,volume,amount"
        else:
            fields = "time,open,high,low,close,volume,amount"

        empty = KlineData(symbol=symbol, interval=interval.value, open=[], high=[],
                          low=[], close=[], volume=[], timestamps=[], source=self.name,
                          contract=contract)
        try:
            with _bs_lock:
                rs = bs.query_history_k_data_plus(
                    code, fields, start_date=start, end_date=end,
                    frequency=freq, adjustflag="2",  # 前复权
                )
                rows = []
                while rs.error_code == "0" and rs.next():
                    rows.append(rs.get_row_data())
            if not rows:
                return empty
            df = pd.DataFrame(rows, columns=rs.fields)
            tcol = "date" if "date" in df.columns else "time"
            ts = pd.to_datetime(df[tcol].str.slice(0, 14) if tcol == "time" else df[tcol])
            num = lambda c: pd.to_numeric(df[c], errors="coerce").fillna(0).tolist()
            return KlineData(
                symbol=symbol, interval=interval.value,
                open=num("open"), high=num("high"), low=num("low"),
                close=num("close"), volume=num("volume"),
                timestamps=ts.tolist(), source=self.name, contract=contract,
            )
        except Exception as e:
            logger.warning(f"BaoStock get_kline failed for {code}: {e}")
            return empty

    def get_realtime(self, symbol: str, contract: Optional[str] = None) -> RealtimeQuote:
        # baostock 不提供实时行情, 返回最近日线收盘
        raise NotImplementedError("BaoStock 不支持实时行情, 请使用 TDX/akshare")

    def get_trade_dates(self, start_date: str, end_date: str) -> List[str]:
        """交易日历: 返回 is_trading=1 的日期列表。"""
        bs = self._get_bs()
        with _bs_lock:
            rs = bs.query_trade_dates(start_date=start_date, end_date=end_date)
            out = []
            while rs.error_code == "0" and rs.next():
                d, is_trade = rs.get_row_data()
                if is_trade == "1":
                    out.append(d)
        return out

    def validate(self) -> bool:
        try:
            self._get_bs()
            self._status = DataSourceStatus.ACTIVE
            return True
        except Exception as e:
            logger.warning(f"BaoStock validate failed: {e}")
            self._status = DataSourceStatus.DOWN
            return False

    def _get_supported_markets(self) -> List[str]:
        return ["stock"]

    def _get_description(self) -> str:
        return "BaoStock — 中国A股历史K线(复权)+交易日历, 免费无需密钥"
