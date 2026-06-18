"""
股票采集器 — A股 D1 (BaoStock 免费) + 基本信息/财报 (akshare 免费)。

流程:
1. collect_kline: BaoStock 前复权日线 -> kline 表 (timeframe=D1)
2. collect_info:   akshare 个股信息 -> stocks_info
3. collect_financial: akshare 财务指标 -> stocks_financial
"""

from __future__ import annotations

from typing import Dict, Optional

import pandas as pd
from loguru import logger

from ..core.base_fetcher import KlineInterval
from ..fetchers.baostock_fetcher import BaoStockFetcher
from .base_collector import BaseCollector


class StocksCollector(BaseCollector):
    """A股数据采集器。"""

    asset_type = "stock"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bs = BaoStockFetcher()
        self._ak = None

    def _get_ak(self):
        if self._ak is None:
            import akshare as ak
            self._ak = ak
        return self._ak

    def list_all_symbols(self, retries: int = 3) -> list[str]:
        """拉沪深全部 A 股代码 (带 .SH/.SZ 后缀)。退市/停牌的由下载时自然为空。

        主源用静态代码表 stock_info_a_code_name (稳定), 失败退到实时行情 spot_em。
        带重试+退避 — 用户环境网络波动 (RemoteDisconnected) 时不至于直接返回空。
        """
        import time
        ak = self._get_ak()

        def _extract(df, code_col: str) -> list[str]:
            if df is None or df.empty or code_col not in df.columns:
                return []
            out = []
            for code in df[code_col].astype(str):
                c = code.strip()
                if len(c) != 6 or not c.isdigit():
                    continue
                out.append(f"{c}.{'SH' if c[0] == '6' else 'SZ'}")
            return out

        for attempt in range(retries):
            try:
                df = ak.stock_info_a_code_name()  # 静态表: code/name
                codes = _extract(df, "code")
                if codes:
                    return codes
            except Exception as e:
                logger.warning(f"stock_info_a_code_name 第{attempt+1}次失败: {e}")
            try:
                df = ak.stock_zh_a_spot_em()  # 兜底: 实时行情
                codes = _extract(df, "代码")
                if codes:
                    return codes
            except Exception as e:
                logger.warning(f"stock_zh_a_spot_em 第{attempt+1}次失败: {e}")
            time.sleep(2 * (attempt + 1))  # 退避
        logger.error("全市场A股清单拉取失败 (网络波动?), 返回空")
        return []

    def collect_kline(self, symbol: str, start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> int:
        """BaoStock 前复权日线 -> kline。symbol 带后缀 600019.SH。"""
        data = self._bs.get_kline(symbol, KlineInterval.DAY, start_date, end_date)
        if not data or not data.timestamps:
            return 0
        sid = self.registry.get_or_create_symbol(
            symbol, symbol, asset_type="stock", name=symbol,
        )
        df = pd.DataFrame({
            "datetime": pd.to_datetime(data.timestamps),
            "symbol_id": sid, "timeframe": "D1",
            "open": data.open, "high": data.high, "low": data.low,
            "close": data.close, "volume": data.volume,
        })
        return self.store.upsert_df("kline", df, ["datetime", "symbol_id", "timeframe"])

    def collect_financial(self, symbol: str) -> int:
        """akshare 财务摘要 -> stocks_financial。"""
        ak = self._get_ak()
        code = symbol.split(".")[0]
        try:
            df = ak.stock_financial_abstract(symbol=code)
        except Exception as e:
            logger.warning(f"{symbol} financial failed: {e}")
            return 0
        if df is None or df.empty:
            return 0
        sid = self.registry.get_or_create_symbol(symbol, symbol, asset_type="stock", name=symbol)
        # 仅记录存在性 (字段结构因 akshare 版本而异, 全量解析留待后续)
        logger.info(f"{symbol} financial rows fetched: {len(df)}")
        return len(df)
