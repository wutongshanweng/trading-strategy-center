"""
多周期聚合器 — 从基础周期聚合到更高周期。

设计文档 §六:
- M5 -> M15/M30/H1/H4   (intraday 重采样)
- D1 -> W1/M1           (周线: 周一开盘→周五收盘; 月线: 月首→月末)

聚合结果写回 kline 表 (timeframe 区分), 避免每次查询重算。
"""

from __future__ import annotations

from typing import Dict

import pandas as pd
from loguru import logger

from .storage.duckdb_store import DuckDBStore, get_store

# 目标周期 -> pandas resample 规则 (基于 M5)
_INTRADAY_RULES: Dict[str, str] = {
    "M15": "15min", "M30": "30min", "H1": "60min", "H4": "240min",
}
_DAILY_RULES: Dict[str, str] = {"W1": "W-FRI", "M1": "MS"}

_OHLC = {
    "open": "first", "high": "max", "low": "min", "close": "last",
    "volume": "sum", "amount": "sum", "open_interest": "last",
    "settlement": "last", "pre_settlement": "first",
}


def _resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    df = df.set_index("datetime").sort_index()
    agg = {k: v for k, v in _OHLC.items() if k in df.columns}
    out = df.resample(rule, label="left", closed="left").agg(agg).dropna(subset=["close"])
    return out.reset_index()


def aggregate_symbol(symbol_id: int, store: DuckDBStore | None = None) -> Dict[str, int]:
    """对单个 symbol 聚合所有目标周期。返回各周期写入行数。"""
    store = store or get_store()
    written: Dict[str, int] = {}

    # intraday: 需要 M5 源
    m5 = store.query(
        "SELECT datetime, open, high, low, close, volume, amount, open_interest, "
        "settlement, pre_settlement FROM kline WHERE symbol_id=? AND timeframe='M5' "
        "ORDER BY datetime", [symbol_id],
    )
    if not m5.empty:
        for tf, rule in _INTRADAY_RULES.items():
            out = _resample(m5, rule)
            written[tf] = _write(store, out, symbol_id, tf)

    # daily->weekly/monthly: 需要 D1 源
    d1 = store.query(
        "SELECT datetime, open, high, low, close, volume, amount, open_interest, "
        "settlement, pre_settlement FROM kline WHERE symbol_id=? AND timeframe='D1' "
        "ORDER BY datetime", [symbol_id],
    )
    if not d1.empty:
        for tf, rule in _DAILY_RULES.items():
            out = _resample(d1, rule)
            written[tf] = _write(store, out, symbol_id, tf)

    return written


def _write(store: DuckDBStore, df: pd.DataFrame, symbol_id: int, timeframe: str) -> int:
    if df is None or df.empty:
        return 0
    df = df.copy()
    df["symbol_id"] = symbol_id
    df["timeframe"] = timeframe
    cols = ["datetime", "symbol_id", "timeframe", "open", "high", "low", "close",
            "volume", "amount", "open_interest", "settlement", "pre_settlement"]
    df = df[[c for c in cols if c in df.columns]]
    return store.upsert_df("kline", df, ["datetime", "symbol_id", "timeframe"])


def aggregate_all(store: DuckDBStore | None = None) -> Dict[str, int]:
    """对库内所有有 M5 或 D1 数据的 symbol 执行聚合。"""
    store = store or get_store()
    ids = store.query(
        "SELECT DISTINCT symbol_id FROM kline WHERE timeframe IN ('M5','D1')"
    )["symbol_id"].tolist()
    totals: Dict[str, int] = {}
    for sid in ids:
        for tf, n in aggregate_symbol(int(sid), store).items():
            totals[tf] = totals.get(tf, 0) + n
    logger.info(f"Aggregated {len(ids)} symbols: {totals}")
    return totals
