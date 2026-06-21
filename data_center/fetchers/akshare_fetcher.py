"""
AKShare Fetcher — 中国市场全品类数据获取器。

支持: 期货/股票/期权/基金/宏观经济
底层: akshare 库
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from ..core.base_fetcher import (
    BaseFetcher, KlineData, KlineInterval, RealtimeQuote,
    DataSourceInfo, DataSourceStatus,
)

logger = logging.getLogger(__name__)


class AKShareFetcher(BaseFetcher):
    """AKShare 数据获取器 — 中国期货/股票/期权/基金"""

    name = "akshare"
    display_name = "AKShare"

    # 品种 → AKShare 代码映射
    FUTURES_SYMBOL_MAP: Dict[str, Dict[str, str]] = {
        # 上海期货交易所 (SHFE)
        "CU": {"exchange": "SHFE", "name": "沪铜", "ak_code": "CU"},
        "AL": {"exchange": "SHFE", "name": "沪铝", "ak_code": "AL"},
        "ZN": {"exchange": "SHFE", "name": "沪锌", "ak_code": "ZN"},
        "PB": {"exchange": "SHFE", "name": "沪铅", "ak_code": "PB"},
        "NI": {"exchange": "SHFE", "name": "沪镍", "ak_code": "NI"},
        "SN": {"exchange": "SHFE", "name": "沪锡", "ak_code": "SN"},
        "AU": {"exchange": "SHFE", "name": "黄金", "ak_code": "AU"},
        "AG": {"exchange": "SHFE", "name": "白银", "ak_code": "AG"},
        "RB": {"exchange": "SHFE", "name": "螺纹钢", "ak_code": "RB"},
        "HC": {"exchange": "SHFE", "name": "热轧卷板", "ak_code": "HC"},
        "RU": {"exchange": "SHFE", "name": "天然橡胶", "ak_code": "RU"},
        "BU": {"exchange": "SHFE", "name": "石油沥青", "ak_code": "BU"},
        # 大连商品交易所 (DCE)
        "M":  {"exchange": "DCE", "name": "豆粕", "ak_code": "M"},
        "Y":  {"exchange": "DCE", "name": "豆油", "ak_code": "Y"},
        "A":  {"exchange": "DCE", "name": "豆一", "ak_code": "A"},
        "B":  {"exchange": "DCE", "name": "豆二", "ak_code": "B"},
        "P":  {"exchange": "DCE", "name": "棕榈油", "ak_code": "P"},
        "C":  {"exchange": "DCE", "name": "玉米", "ak_code": "C"},
        "I":  {"exchange": "DCE", "name": "铁矿石", "ak_code": "I"},
        "J":  {"exchange": "DCE", "name": "焦炭", "ak_code": "J"},
        "JM": {"exchange": "DCE", "name": "焦煤", "ak_code": "JM"},
        "L":  {"exchange": "DCE", "name": "LLDPE", "ak_code": "L"},
        "PP": {"exchange": "DCE", "name": "聚丙烯", "ak_code": "PP"},
        "V":  {"exchange": "DCE", "name": "PVC", "ak_code": "V"},
        "EG": {"exchange": "DCE", "name": "乙二醇", "ak_code": "EG"},
        "PG": {"exchange": "DCE", "name": "液化石油气", "ak_code": "PG"},
        # 郑州商品交易所 (CZCE)
        "SR": {"exchange": "CZCE", "name": "白糖", "ak_code": "SR"},
        "CF": {"exchange": "CZCE", "name": "棉花", "ak_code": "CF"},
        "TA": {"exchange": "CZCE", "name": "PTA", "ak_code": "TA"},
        "MA": {"exchange": "CZCE", "name": "甲醇", "ak_code": "MA"},
        "FG": {"exchange": "CZCE", "name": "玻璃", "ak_code": "FG"},
        "RM": {"exchange": "CZCE", "name": "菜籽粕", "ak_code": "RM"},
        "OI": {"exchange": "CZCE", "name": "菜籽油", "ak_code": "OI"},
        "ZC": {"exchange": "CZCE", "name": "动力煤", "ak_code": "ZC"},
        "SA": {"exchange": "CZCE", "name": "纯碱", "ak_code": "SA"},
        # 中国金融期货交易所 (CFFEX)
        "IF": {"exchange": "CFFEX", "name": "沪深300", "ak_code": "IF"},
        "IH": {"exchange": "CFFEX", "name": "上证50", "ak_code": "IH"},
        "IC": {"exchange": "CFFEX", "name": "中证500", "ak_code": "IC"},
        "IM": {"exchange": "CFFEX", "name": "中证1000", "ak_code": "IM"},
        # 上海国际能源交易中心 (INE)
        "SC": {"exchange": "INE", "name": "原油", "ak_code": "SC"},
        "NR": {"exchange": "INE", "name": "20号胶", "ak_code": "NR"},
        "LU": {"exchange": "INE", "name": "低硫燃料油", "ak_code": "LU"},
        "BC": {"exchange": "INE", "name": "国际铜", "ak_code": "BC"},
        # 广州期货交易所 (GFEX)
        "SI": {"exchange": "GFEX", "name": "工业硅", "ak_code": "SI"},
        "LC": {"exchange": "GFEX", "name": "碳酸锂", "ak_code": "LC"},
    }

    _ak = None

    def _get_ak(self):
        """懒加载 akshare"""
        if self._ak is None:
            try:
                import akshare as ak
                self._ak = ak
            except ImportError:
                raise ImportError("请安装 akshare: pip install akshare")
        return self._ak

    def _clean_futures_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """统一期货数据列名"""
        if df.empty:
            return df
        col_map = {
            "日期": "date", "开盘": "open", "最高": "high", "最低": "low",
            "收盘": "close", "成交量": "volume", "持仓量": "open_interest",
            "date": "date", "open": "open", "high": "high", "low": "low",
            "close": "close", "volume": "volume",
            "hold": "open_interest", "settle": "settlement",
        }
        df = df.rename(columns={c: col_map.get(c, c) for c in df.columns})
        # 只保留标准列
        keep = ["date", "datetime", "open", "high", "low", "close", "volume", "open_interest", "settlement"]
        return df[[c for c in keep if c in df.columns]]

    def _to_sina_continuous(self, symbol: str) -> str:
        """裸品种代码 → 新浪主力连续代码 (RB → RB0)。已带数字的合约号原样返回。"""
        s = symbol.upper()
        if any(ch.isdigit() for ch in s):
            return s
        return f"{s}0"

    def get_futures_daily(self, symbol: str) -> pd.DataFrame:
        """获取期货主力连续日线"""
        ak = self._get_ak()
        sina_symbol = self._to_sina_continuous(symbol)
        try:
            df = ak.futures_zh_daily_sina(symbol=sina_symbol)
            return self._clean_futures_df(df)
        except Exception as e:
            logger.warning(f"AKShare futures_daily_sina failed for {sina_symbol}: {e}")
            return pd.DataFrame()

    def get_futures_hist_em(self, symbol: str, contract: str = "",
                            start_date: str = "", end_date: str = "") -> pd.DataFrame:
        """获取期货历史数据 (东财)"""
        ak = self._get_ak()
        try:
            df = ak.futures_hist_em(symbol=symbol, period="daily",
                                     start_date=start_date, end_date=end_date,
                                     adjust="")
            return self._clean_futures_df(df)
        except Exception as e:
            logger.warning(f"AKShare futures_hist_em failed for {symbol}: {e}")
            return pd.DataFrame()

    def get_kline(self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
                  start_date: Optional[str] = None, end_date: Optional[str] = None,
                  contract: Optional[str] = None) -> KlineData:
        """获取 K 线数据。A股代码 (600019.SH / 6位数字) 走个股日线, 其余走期货。"""
        bare = symbol.split(".")[0]
        is_stock = ("." in symbol) or (bare.isdigit() and len(bare) == 6)
        df = self.get_stock_daily(bare) if is_stock else self.get_futures_daily(symbol)
        if df.empty:
            return KlineData(
                symbol=symbol, interval=interval.value,
                open=[], high=[], low=[], close=[], volume=[], timestamps=[],
                source=self.name, contract=contract,
            )

        # 统一处理
        dates = pd.to_datetime(df["date"]) if "date" in df.columns else []
        return KlineData(
            symbol=symbol,
            interval=interval.value,
            open=df["open"].tolist() if "open" in df.columns else [],
            high=df["high"].tolist() if "high" in df.columns else [],
            low=df["low"].tolist() if "low" in df.columns else [],
            close=df["close"].tolist() if "close" in df.columns else [],
            volume=df["volume"].tolist() if "volume" in df.columns else [],
            timestamps=dates.tolist() if not dates.empty else [],
            source=self.name,
            contract=contract,
        )

    def get_futures_minute(self, symbol: str, period: str = "1") -> pd.DataFrame:
        """获取期货分钟数据 (period: 1/5/15/30/60)"""
        ak = self._get_ak()
        try:
            df = ak.futures_zh_minute_sina(symbol=symbol, period=period)
            return self._clean_futures_df(df)
        except Exception as e:
            logger.warning(f"AKShare minute failed for {symbol}: {e}")
            return pd.DataFrame()

    def get_realtime(self, symbol: str, contract: Optional[str] = None) -> RealtimeQuote:
        """获取实时行情"""
        ak = self._get_ak()
        try:
            df = ak.futures_zh_realtime(symbol=symbol)
            if not df.empty:
                row = df.iloc[-1]
                return RealtimeQuote(
                    symbol=symbol, last_price=float(row.get("current_price", 0)),
                    open_price=float(row.get("open", 0)),
                    high_price=float(row.get("high", 0)),
                    low_price=float(row.get("low", 0)),
                    pre_close=float(row.get("pre_close", 0)),
                    volume=int(row.get("volume", 0)),
                    turnover=float(row.get("turnover", 0)),
                    bid_price=float(row.get("bid1", 0)),
                    ask_price=float(row.get("ask1", 0)),
                    bid_volume=int(row.get("bid_vol1", 0)),
                    ask_volume=int(row.get("ask_vol1", 0)),
                    timestamp=datetime.now(),
                    source=self.name, contract=contract,
                )
        except Exception as e:
            logger.warning(f"AKShare realtime failed for {symbol}: {e}")

        return RealtimeQuote(
            symbol=symbol, last_price=0, open_price=0, high_price=0, low_price=0,
            pre_close=0, volume=0, turnover=0, bid_price=0, ask_price=0,
            bid_volume=0, ask_volume=0, timestamp=datetime.now(),
            source=self.name, contract=contract,
        )

    def get_stock_daily(self, symbol: str, adjust: str = "qfq") -> pd.DataFrame:
        """获取 A 股日线"""
        ak = self._get_ak()
        try:
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                                     start_date="19000101", end_date="20991231",
                                     adjust=adjust)
            return self._clean_futures_df(df)
        except Exception as e:
            logger.warning(f"AKShare stock_daily failed for {symbol}: {e}")
            return pd.DataFrame()

    def get_stock_daily_sina(self, symbol: str, adjust: str = "qfq") -> pd.DataFrame:
        """A 股日线 (新浪源, 本环境比东财稳定)。symbol 接受 600019/600019.SH/sh600019。"""
        ak = self._get_ak()
        code = symbol.split(".")[0]
        prefix = "sh" if code[0] == "6" else "sz"
        sina_sym = code if symbol[:2].lower() in ("sh", "sz") else f"{prefix}{code}"
        try:
            df = ak.stock_zh_a_daily(symbol=sina_sym, adjust=adjust)
            return self._clean_futures_df(df)
        except Exception as e:
            logger.warning(f"AKShare stock_daily_sina failed for {symbol}: {e}")
            return pd.DataFrame()

    def list_available_symbols(self) -> List[str]:
        """列出支持的品种"""
        return list(self.FUTURES_SYMBOL_MAP.keys())

    def validate(self) -> bool:
        try:
            ak = self._get_ak()
            df = ak.futures_zh_daily_sina(symbol="RB")
            return not df.empty
        except Exception:
            self._status = DataSourceStatus.DOWN
            return False

    def _get_supported_markets(self) -> List[str]:
        return ["futures", "stock", "fund", "index"]

    def _get_description(self) -> str:
        return "AKShare 开源数据接口，覆盖中国期货/股票/期权/基金/宏观经济等全品类数据"
