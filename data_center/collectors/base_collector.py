"""
采集器基类 — 统一 KlineData -> kline 表写入。

职责:
- 解析品种/合约 -> symbol_id (via SymbolRegistry)
- KlineData 标准化为 kline DataFrame
- 写入 DuckDB (upsert, 天然去重)
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from loguru import logger

from ..core.base_fetcher import KlineData, KlineInterval
from ..db.registry import SymbolRegistry
from ..storage.duckdb_store import DuckDBStore, get_store

# KlineInterval -> 统一 timeframe 命名 (设计文档)
_TF_MAP = {
    KlineInterval.M1: "M1_raw", KlineInterval.M5: "M5", KlineInterval.M15: "M15",
    KlineInterval.M30: "M30", KlineInterval.M60: "H1", KlineInterval.DAY: "D1",
    KlineInterval.WEEK: "W1", KlineInterval.MONTH: "M1",
}


class BaseCollector:
    """采集器基类。"""

    asset_type = "futures"

    def __init__(self, store: Optional[DuckDBStore] = None,
                 registry: Optional[SymbolRegistry] = None):
        self.store = store or get_store()
        self.registry = registry or SymbolRegistry(self.store)

    def _kline_to_df(self, data: KlineData, symbol_id: int, timeframe: str) -> pd.DataFrame:
        if not data or not data.timestamps:
            return pd.DataFrame()
        n = len(data.timestamps)
        def col(vals):
            return list(vals) + [None] * (n - len(vals)) if vals and len(vals) < n else (vals or [None] * n)
        df = pd.DataFrame({
            "datetime": pd.to_datetime(data.timestamps),
            "symbol_id": symbol_id,
            "timeframe": timeframe,
            "open": col(data.open), "high": col(data.high),
            "low": col(data.low), "close": col(data.close),
            "volume": col(data.volume),
        })
        return df

    def store_kline(self, data: KlineData, symbol_code: str, product_code: str,
                    interval: KlineInterval, exchange: Optional[str] = None,
                    name: str = "") -> int:
        """标准化并写入一段 KlineData。返回写入行数。"""
        if not data or not data.timestamps:
            return 0
        sid = self.registry.get_or_create_symbol(
            symbol_code, product_code, asset_type=self.asset_type,
            exchange=exchange, name=name,
        )
        tf = _TF_MAP.get(interval, interval.value)
        df = self._kline_to_df(data, sid, tf)
        return self.store.upsert_df("kline", df, ["datetime", "symbol_id", "timeframe"])
