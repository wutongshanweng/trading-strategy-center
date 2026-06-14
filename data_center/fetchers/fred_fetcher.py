"""
FRED Fetcher — 美国宏观经济数据获取器。

底层: fredapi / requests
数据源: FRED (Federal Reserve Economic Data)
支持: GDP/CPI/失业率/利率/国债收益率等
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.base_fetcher import (
    BaseFetcher, KlineData, KlineInterval, RealtimeQuote,
    DataSourceStatus,
)

logger = logging.getLogger(__name__)


class FREDFetcher(BaseFetcher):
    """FRED 美国经济数据获取器"""

    name = "fred"
    display_name = "FRED (美联储经济数据)"
    BASE_URL = "https://api.stlouisfed.org/fred"

    ECONOMIC_SERIES: Dict[str, str] = {
        "GDP": "GDP",           # 国内生产总值
        "UNRATE": "UNRATE",    # 失业率
        "CPIAUCSL": "CPIAUCSL", # CPI
        "FEDFUNDS": "FEDFUNDS", # 联邦基金利率
        "DGS10": "DGS10",      # 10年期国债收益率
        "DGS2": "DGS2",        # 2年期国债收益率
        "DGS1MO": "DGS1MO",    # 1月期国债收益率
        "DTB3": "DTB3",        # 3月期国债收益率
        "T10Y2Y": "T10Y2Y",    # 10-2年期利差
        "SP500": "SP500",      # S&P 500
        "VIXCLS": "VIXCLS",    # VIX
        "DEXUSEU": "DEXUSEU",  # 欧元/美元
        "DEXJPUS": "DEXJPUS",  # 美元/日元
        "M2SL": "M2SL",        # M2货币供应
        "TOTALSL": "TOTALSL",  # 商业银行总资产
        "INDPRO": "INDPRO",    # 工业生产指数
        "HOUST": "HOUST",      # 新屋开工
    }

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.environ.get("FRED_API_KEY", "")

    def get_series(self, series_id: str, start: str = "", end: str = "") -> pd.Series:
        """获取单个 FRED 序列数据"""
        try:
            from fredapi import Fred
            fred = Fred(api_key=self.api_key)
            return fred.get_series(series_id,
                observation_start=start or None,
                observation_end=end or None)
        except ImportError:
            logger.warning("fredapi 未安装: pip install fredapi")
            return pd.Series()
        except Exception as e:
            logger.warning(f"FRED get_series failed for {series_id}: {e}")
            return pd.Series()

    def get_series_df(self, series_id: str, start: str = "", end: str = "") -> pd.DataFrame:
        """获取 FRED 序列并转为 DataFrame"""
        s = self.get_series(series_id, start, end)
        if s.empty:
            return pd.DataFrame()
        df = s.reset_index()
        df.columns = ["date", "value"]
        df["series_id"] = series_id
        df["series_name"] = self.ECONOMIC_SERIES.get(series_id, series_id)
        return df

    def get_multiple_series(self, series_ids: List[str]) -> pd.DataFrame:
        """获取多个 FRED 序列并合并"""
        dfs = []
        for sid in series_ids:
            df = self.get_series_df(sid)
            if not df.empty:
                dfs.append(df)
        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            return combined.pivot_table(index="date", columns="series_id",
                                         values="value", aggfunc="first").reset_index()
        return pd.DataFrame()

    def get_gdp(self) -> pd.DataFrame:
        """获取 GDP 数据"""
        return self.get_series_df("GDP")

    def get_cpi(self) -> pd.DataFrame:
        """获取 CPI 数据"""
        return self.get_series_df("CPIAUCSL")

    def get_unemployment_rate(self) -> pd.DataFrame:
        """获取失业率"""
        return self.get_series_df("UNRATE")

    def get_fed_rate(self) -> pd.DataFrame:
        """获取联邦基金利率"""
        return self.get_series_df("FEDFUNDS")

    def get_treasury_yield(self, maturity: str = "10") -> pd.DataFrame:
        """获取国债收益率"""
        series_map = {"10": "DGS10", "2": "DGS2", "1": "DGS1MO", "3m": "DTB3"}
        series_id = series_map.get(maturity, "DGS10")
        return self.get_series_df(series_id)

    def get_kline(self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
                  **kwargs) -> KlineData:
        df = self.get_series_df(symbol)
        if df.empty:
            return KlineData(symbol=symbol, interval=interval.value,
                           open=[], high=[], low=[], close=[], volume=[], timestamps=[], source=self.name)
        return KlineData(
            symbol=symbol, interval=interval.value,
            open=df["value"].tolist(), high=[], low=[], close=df["value"].tolist(),
            volume=[], timestamps=pd.to_datetime(df["date"]).tolist() if "date" in df.columns else [],
            source=self.name,
        )

    def get_realtime(self, symbol: str, contract=None) -> RealtimeQuote:
        return RealtimeQuote(symbol=symbol, last_price=0, open_price=0, high_price=0, low_price=0,
            pre_close=0, volume=0, turnover=0, bid_price=0, ask_price=0, bid_volume=0, ask_volume=0,
            timestamp=datetime.now(), source=self.name)

    def list_available_series(self) -> Dict[str, str]:
        return dict(self.ECONOMIC_SERIES)

    def validate(self) -> bool:
        ok = bool(self.api_key)
        self._status = DataSourceStatus.ACTIVE if ok else DataSourceStatus.DOWN
        return ok

    def _get_supported_markets(self) -> List[str]:
        return ["macro", "economics"]

    def _get_description(self) -> str:
        return "FRED 美联储经济数据库 (需要 API Key)，提供 GDP/CPI/利率/国债收益率等美国核心经济指标"
