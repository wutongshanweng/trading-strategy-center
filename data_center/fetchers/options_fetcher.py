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

    # 商品期权交易所映射
    COMMODITY_EXCHANGES = {"大商所": "dce", "郑商所": "czce", "上期所": "shfe"}
    COMMODITY_OPTION_SYMBOLS = {
        "大商所": ["豆粕期权", "玉米期权", "豆油期权", "棕榈油期权", "铁矿石期权",
                   "聚丙烯期权", "聚氯乙烯期权", "线型低密度聚乙烯期权"],
        "郑商所": ["白糖期权", "棉花期权", "PTA期权", "甲醇期权", "菜籽粕期权",
                   "菜籽油期权", "动力煤期权", "纯碱期权", "尿素期权", "短纤期权"],
        "上期所": ["铜期权", "黄金期权", "铝期权", "锌期权", "橡胶期权",
                   "螺纹钢期权", "白银期权"],
    }

    # ─── 上交所 ETF 期权 ───────────────────────────────
    def get_etf_option_daily(self, symbol: str) -> pd.DataFrame:
        """ETF期权日线 (合约代码如 10003889)，新浪源。"""
        ak = self._get_ak()
        try:
            return ak.option_sse_daily_sina(symbol=symbol)
        except Exception as e:
            logger.warning(f"ETF option daily failed [{symbol}]: {e}")
            return pd.DataFrame()

    def get_etf_option_realtime(self, symbol: str) -> pd.DataFrame:
        ak = self._get_ak()
        try:
            return ak.option_sse_spot_price_sina(symbol=symbol)
        except Exception as e:
            logger.warning(f"ETF option realtime failed [{symbol}]: {e}")
            return pd.DataFrame()

    def get_etf_option_codes(self, option_type: str = "看涨期权",
                             trade_date: str = "", underlying: str = "510050") -> pd.DataFrame:
        """查询ETF期权合约代码列表 (underlying: 510050/510300/510500)。"""
        ak = self._get_ak()
        try:
            if not trade_date:
                trade_date = datetime.now().strftime("%Y%m")
            return ak.option_sse_codes_sina(symbol=option_type, trade_date=trade_date,
                                            underlying=underlying)
        except Exception as e:
            logger.warning(f"ETF option codes failed: {e}")
            return pd.DataFrame()

    # ─── 中金所股指期权 ────────────────────────────────
    def get_index_option_daily(self, symbol: str) -> pd.DataFrame:
        """股指期权日线 (IO=沪深300, HO=上证50)，如 io2202P4350。"""
        ak = self._get_ak()
        symbol = symbol.upper()
        try:
            if symbol.startswith("IO"):
                return ak.option_cffex_hs300_daily_sina(symbol=symbol)
            if symbol.startswith("HO"):
                return ak.option_cffex_sz50_daily_sina(symbol=symbol)
            logger.warning(f"不支持的股指期权: {symbol[:2]}")
            return pd.DataFrame()
        except Exception as e:
            logger.warning(f"Index option daily failed [{symbol}]: {e}")
            return pd.DataFrame()

    def get_index_option_realtime(self, variety: str = "io") -> pd.DataFrame:
        """股指期权实时 (io=沪深300, ho=上证50)。"""
        ak = self._get_ak()
        v = variety.lower()
        try:
            if v == "io":
                return ak.option_cffex_hs300_spot_sina(symbol="io")
            if v == "ho":
                return ak.option_cffex_sz50_spot_sina(symbol="ho")
            return pd.DataFrame()
        except Exception as e:
            logger.warning(f"Index option realtime failed [{variety}]: {e}")
            return pd.DataFrame()

    # ─── 商品期权 ──────────────────────────────────────
    def get_commodity_option_daily(self, exchange: str = "大商所",
                                   symbol: str = "豆粕期权", trade_date: str = "") -> pd.DataFrame:
        """商品期权某交易日全合约 (含隐含波动率)。exchange: 大商所/郑商所/上期所。"""
        ak = self._get_ak()
        try:
            if not trade_date:
                trade_date = datetime.now().strftime("%Y%m%d")
            ex = self.COMMODITY_EXCHANGES.get(exchange, exchange)
            if ex == "dce":
                return ak.option_hist_dce(symbol=symbol, trade_date=trade_date)
            if ex == "czce":
                return ak.option_hist_czce(symbol=symbol, trade_date=trade_date)
            if ex == "shfe":
                return ak.option_hist_shfe(symbol=symbol, trade_date=trade_date)
            return pd.DataFrame()
        except Exception as e:
            logger.warning(f"Commodity option daily failed [{exchange}/{symbol}]: {e}")
            return pd.DataFrame()

    # ─── 波动率指数 (QVIX) ─────────────────────────────
    def get_50etf_volatility_index(self) -> pd.DataFrame:
        ak = self._get_ak()
        try:
            return ak.index_option_50etf_qvix()
        except Exception as e:
            logger.warning(f"50ETF QVIX failed: {e}")
            return pd.DataFrame()

    def get_300etf_volatility_index(self) -> pd.DataFrame:
        ak = self._get_ak()
        try:
            return ak.index_option_300etf_qvix()
        except Exception as e:
            logger.warning(f"300ETF QVIX failed: {e}")
            return pd.DataFrame()

    # ─── 希腊值 / 风险分析 (东方财富) ──────────────────
    def get_option_risk_analysis(self) -> pd.DataFrame:
        """各期权合约 Delta/Gamma/Vega/Theta/Rho 希腊值。"""
        ak = self._get_ak()
        try:
            return ak.option_risk_analysis_em()
        except Exception as e:
            logger.warning(f"Option risk analysis failed: {e}")
            return pd.DataFrame()

    def get_option_premium_analysis(self) -> pd.DataFrame:
        """各期权合约 溢价率/时间价值/内在价值。"""
        ak = self._get_ak()
        try:
            return ak.option_premium_analysis_em()
        except Exception as e:
            logger.warning(f"Option premium analysis failed: {e}")
            return pd.DataFrame()

    def get_option_value_analysis(self) -> pd.DataFrame:
        """各期权合约 内在价值/时间价值/杠杆率。"""
        ak = self._get_ak()
        try:
            return ak.option_value_analysis_em()
        except Exception as e:
            logger.warning(f"Option value analysis failed: {e}")
            return pd.DataFrame()

    def get_kline(self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
                  start_date: Optional[str] = None, end_date: Optional[str] = None,
                  contract: Optional[str] = None) -> KlineData:
        """期权合约日线 -> KlineData。按代码前缀路由:
        IO* -> 沪深300股指期权; HO* -> 上证50股指期权; 纯数字 -> 上交所ETF期权。"""
        code = (contract or symbol).strip()
        empty = KlineData(symbol=symbol, interval=interval.value, open=[], high=[],
                          low=[], close=[], volume=[], timestamps=[], source=self.name,
                          contract=contract)
        up = code.upper()
        if up.startswith("IO") or up.startswith("HO"):
            df = self.get_index_option_daily(code)
        elif code.isdigit():
            df = self.get_etf_option_daily(code)
        else:
            logger.warning(f"无法识别的期权合约代码: {code}")
            return empty
        if df is None or df.empty:
            return empty

        rename = {"日期": "date", "开盘": "open", "最高": "high", "最低": "low",
                  "收盘": "close", "成交量": "volume", "持仓量": "open_interest"}
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        tcol = "date" if "date" in df.columns else ("datetime" if "datetime" in df.columns else None)
        if tcol is None or "close" not in df.columns:
            logger.warning(f"{code} 期权日线缺少时间/收盘列: {list(df.columns)}")
            return empty
        num = lambda c: pd.to_numeric(df[c], errors="coerce").fillna(0).tolist() if c in df.columns else []
        return KlineData(
            symbol=symbol, interval=interval.value,
            open=num("open"), high=num("high"), low=num("low"),
            close=num("close"), volume=num("volume"),
            timestamps=pd.to_datetime(df[tcol]).tolist(),
            source=self.name, contract=contract,
        )

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
