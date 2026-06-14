"""
EIA/CFTC Fetcher — 美国能源数据 + COT持仓报告。

底层: requests (直接调用 EIA / CFTC REST API)
数据源:
- EIA: 原油/汽油/天然气库存
- CFTC: 期货持仓报告 (COT)
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


class EIAFetcher(BaseFetcher):
    """EIA 能源数据获取器"""

    name = "eia"
    display_name = "EIA (能源信息署)"
    BASE_URL = "https://api.eia.gov/v2"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.environ.get("EIA_API_KEY", "")

    def _request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        if not self.api_key:
            logger.warning("EIA API key not set")
            return None
        url = f"{self.BASE_URL}/{endpoint}"
        p = {"api_key": self.api_key, **(params or {})}
        try:
            resp = requests.get(url, params=p, timeout=15)
            return resp.json()
        except Exception as e:
            logger.warning(f"EIA request failed: {e}")
            return None

    def get_crude_oil_inventories(self, num_periods: int = 20) -> pd.DataFrame:
        """获取原油库存数据"""
        data = self._request("petroleum/stoc/stot/data", {
            "frequency": "weekly",
            "data[0]": "value",
            "facets[duoarea][]": "NUS",
            "facets[product][]": "EPC0",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": num_periods,
        })
        if data and "response" in data:
            return pd.DataFrame(data["response"].get("data", []))
        return pd.DataFrame()

    def get_gasoline_inventories(self, num_periods: int = 20) -> pd.DataFrame:
        """获取汽油库存数据"""
        data = self._request("petroleum/stoc/stot/data", {
            "frequency": "weekly",
            "data[0]": "value",
            "facets[duoarea][]": "NUS",
            "facets[product][]": "EPM0",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": num_periods,
        })
        if data and "response" in data:
            return pd.DataFrame(data["response"].get("data", []))
        return pd.DataFrame()

    def get_natural_gas_storage(self, num_periods: int = 20) -> pd.DataFrame:
        """获取天然气库存数据"""
        data = self._request("natural-gas/stor/stot/data", {
            "frequency": "weekly",
            "data[0]": "value",
            "facets[duoarea][]": "NUS",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": num_periods,
        })
        if data and "response" in data:
            return pd.DataFrame(data["response"].get("data", []))
        return pd.DataFrame()

    def get_kline(self, symbol: str, interval=KlineInterval.DAY, **kwargs) -> KlineData:
        return KlineData(symbol=symbol, interval=interval.value, open=[], high=[], low=[], close=[], volume=[], timestamps=[], source=self.name)

    def get_realtime(self, symbol: str, contract=None) -> RealtimeQuote:
        return RealtimeQuote(symbol=symbol, last_price=0, open_price=0, high_price=0, low_price=0, pre_close=0, volume=0, turnover=0, bid_price=0, ask_price=0, bid_volume=0, ask_volume=0, timestamp=datetime.now(), source=self.name)

    def validate(self) -> bool:
        ok = bool(self.api_key)
        self._status = DataSourceStatus.ACTIVE if ok else DataSourceStatus.DOWN
        return ok

    def _get_supported_markets(self) -> List[str]:
        return ["energy"]

    def _get_description(self) -> str:
        return "美国能源信息署(EIA)数据，提供原油/汽油/天然气库存等能源周度数据"


class CFTCFetcher(BaseFetcher):
    """CFTC 持仓报告获取器 (不需要 API Key)"""

    name = "cftc"
    display_name = "CFTC (持仓报告)"
    BASE_URL = "https://www.cftc.gov/files/dea/history"

    # 常见品种的 CFTC 市场代码
    MARKET_CODES: Dict[str, str] = {
        "CL": "06765",   # WTI原油
        "NG": "06510",   # 天然气
        "HO": "02265",   # 取暖油
        "GC": "08865",   # 黄金
        "SI": "08465",   # 白银
        "PL": "07665",   # 铂金
        "PA": "07565",   # 钯金
        "CU": "08565",   # 铜
        "ZW": "00160",   # 小麦
        "ZC": "00260",   # 玉米
        "ZS": "00560",   # 大豆
        "ZM": "02660",   # 豆粕
        "ZL": "00760",   # 豆油
        "CC": "07373",   # 可可
        "SB": "08073",   # 糖11号
        "CT": "03360",   # 棉花
        "LC": "05764",   # 活牛
        "ES": "13874",   # E-mini S&P 500
        "NQ": "20974",   # Nasdaq 100
        "YM": "12460",   # 道琼斯
        "SI": "09274",   # 美元指数
    }

    def get_cot_report(self, market_code: str, year: Optional[int] = None) -> pd.DataFrame:
        """获取 COT 持仓报告"""
        year = year or datetime.now().year
        url = f"{self.BASE_URL}/dea_com_{year}.zip"
        try:
            resp = requests.get(url, timeout=30)
            import zipfile, io
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                csv_file = [f for f in z.namelist() if f.endswith('.csv')]
                if csv_file:
                    df = pd.read_csv(z.open(csv_file[0]), encoding='latin1')
                    # 过滤特定品种
                    if market_code:
                        df = df[df.iloc[:, 0].astype(str).str.contains(market_code)]
                    return df
        except Exception as e:
            logger.warning(f"CFTC report fetch failed: {e}")
        return pd.DataFrame()

    def get_kline(self, **kwargs) -> KlineData:
        return KlineData(symbol=kwargs.get("symbol", ""), interval="1d", open=[], high=[], low=[], close=[], volume=[], timestamps=[], source=self.name)

    def get_realtime(self, symbol: str, contract=None) -> RealtimeQuote:
        return RealtimeQuote(symbol=symbol, last_price=0, open_price=0, high_price=0, low_price=0, pre_close=0, volume=0, turnover=0, bid_price=0, ask_price=0, bid_volume=0, ask_volume=0, timestamp=datetime.now(), source=self.name)

    def validate(self) -> bool:
        self._status = DataSourceStatus.ACTIVE
        return True

    def _get_supported_markets(self) -> List[str]:
        return ["futures", "commodity"]

    def _get_description(self) -> str:
        return "CFTC 期货持仓报告(COT)，提供各类期货品种的持仓结构数据"
