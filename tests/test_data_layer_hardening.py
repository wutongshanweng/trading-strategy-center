"""数据层加固 — H1 upsert原子性 / H4 夜盘聚合 单测。"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pytest

from data_center.storage.duckdb_store import DuckDBStore
from data_center.db.registry import SymbolRegistry
from data_center.aggregator import _resample, _trading_date
from data_center.core.retry import retry_sync, _is_transient


# ---- H1: upsert 原子性 ----
@pytest.fixture
def store(tmp_path):
    s = DuckDBStore(db_path=tmp_path / "atomic.duckdb")
    yield s
    s.close()


def _seed_kline(store, reg, code, dt, close):
    sid = reg.get_or_create_symbol(code, code, asset_type="stock", name=code)
    store.upsert_df("kline", pd.DataFrame({
        "datetime": [pd.Timestamp(dt)], "symbol_id": [sid], "timeframe": ["D1"], "close": [close],
    }), ["datetime", "symbol_id", "timeframe"])
    return sid


def test_upsert_normal_replaces(store):
    reg = SymbolRegistry(store)
    sid = _seed_kline(store, reg, "600000.SH", "2026-06-01", 10.0)
    # 重拉同主键 -> 替换
    store.upsert_df("kline", pd.DataFrame({
        "datetime": [pd.Timestamp("2026-06-01")], "symbol_id": [sid],
        "timeframe": ["D1"], "close": [11.0],
    }), ["datetime", "symbol_id", "timeframe"])
    rows = store.query("SELECT close FROM kline WHERE symbol_id=?", [sid])
    assert len(rows) == 1 and float(rows.iloc[0]["close"]) == 11.0


def test_upsert_rollback_keeps_old_on_insert_failure(store):
    """INSERT 阶段失败 -> 事务回滚, 旧数据不丢 (H1 核心)。"""
    reg = SymbolRegistry(store)
    sid = _seed_kline(store, reg, "600000.SH", "2026-06-01", 10.0)
    # 构造会令 INSERT 失败的 df: 含 kline 不存在的列, DELETE 能匹配但 INSERT 报错
    bad = pd.DataFrame({
        "datetime": [pd.Timestamp("2026-06-01")], "symbol_id": [sid],
        "timeframe": ["D1"], "close": [99.0], "nonexistent_col": [1],
    })
    with pytest.raises(Exception):
        store.upsert_df("kline", bad, ["datetime", "symbol_id", "timeframe"])
    # 旧数据应仍在 (10.0), 没被 DELETE 删空
    rows = store.query("SELECT close FROM kline WHERE symbol_id=?", [sid])
    assert len(rows) == 1 and float(rows.iloc[0]["close"]) == 10.0


# ---- H4: 夜盘聚合按交易日, 不跨日 ----
def test_trading_date_night_belongs_next_day():
    idx = pd.to_datetime(["2026-06-01 21:00", "2026-06-01 22:30", "2026-06-02 09:00"])
    td = _trading_date(pd.DatetimeIndex(idx))
    # 夜盘 21:00/22:30 归 6-02, 白天 09:00 归 6-02 (同一交易日)
    assert td.iloc[0].date().isoformat() == "2026-06-02"
    assert td.iloc[1].date().isoformat() == "2026-06-02"
    assert td.iloc[2].date().isoformat() == "2026-06-02"


def test_h4_does_not_span_trading_days():
    """两个交易日的 M5 聚合 H4, 不应把跨日数据混进同一 bar。"""
    # 交易日A: 6-01 白天 9:00-9:10; 交易日B(含6-01夜盘): 6-01 21:00 + 6-02 9:00
    rows = []
    for t, c in [("2026-06-01 09:00", 100), ("2026-06-01 09:05", 101),
                 ("2026-06-01 21:00", 110), ("2026-06-02 09:00", 120)]:
        rows.append({"datetime": pd.Timestamp(t), "open": c, "high": c, "low": c, "close": c})
    df = pd.DataFrame(rows)
    out = _resample(df, "240min")
    # 6-01 白天独立成 bar(交易日6-01); 6-01夜盘+6-02白天属交易日6-02
    # 关键: 不应出现把 6-01 白天(100) 与 6-02(120) 混进同一 H4 bar
    assert len(out) >= 2
    # 6-01 白天 bar 的 high 不应包含夜盘/次日的 110/120
    day1 = out[out["datetime"] < pd.Timestamp("2026-06-01 20:00")]
    assert day1["high"].max() <= 101


# ---- H2: 重试瞬时判定 ----
def test_retry_only_transient():
    calls = {"n": 0}
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionResetError("Connection reset by peer")
        return "ok"
    assert retry_sync(flaky, attempts=3, delay=0.01) == "ok"
    assert calls["n"] == 3


def test_retry_no_retry_on_value_error():
    calls = {"n": 0}
    def bad():
        calls["n"] += 1
        raise ValueError("bad param")
    with pytest.raises(ValueError):
        retry_sync(bad, attempts=3, delay=0.01)
    assert calls["n"] == 1   # 非网络错误不重试
