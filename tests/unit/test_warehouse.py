"""
统一数据仓库 (DuckDB) — 单元测试。

覆盖:
- DuckDBStore: schema 初始化 / upsert 去重 / 查询
- SymbolRegistry: 合约解析 / 幂等建档
- aggregator: D1->W1, M5->M15 聚合
- MacroCollector._parse_date: 中文日期/季度解析
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import tempfile

import pandas as pd
import pytest

from data_center.storage.duckdb_store import DuckDBStore
from data_center.db.registry import SymbolRegistry, _split_yearmonth
from data_center.collectors.macro_collector import MacroCollector


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "test.duckdb"
    s = DuckDBStore(db_path=db)
    yield s
    s.close()


# ---- DuckDBStore -----------------------------------------------------------

class TestDuckDBStore:
    def test_schema_tables_created(self, store):
        tabs = store.query(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        )["table_name"].tolist()
        for t in ["products", "symbols", "kline", "options_daily", "macro_data",
                  "cross_market_mapping", "stocks_info", "stocks_financial",
                  "futures_main_switches"]:
            assert t in tabs

    def test_upsert_dedup(self, store):
        store.execute(
            "INSERT INTO products (code,name,asset_type) VALUES ('RB','螺纹钢','futures')"
        )
        sid_df = store.query("SELECT product_id FROM products WHERE code='RB'")
        pid = int(sid_df.iloc[0]["product_id"])
        store.execute(
            "INSERT INTO symbols (product_id,code) VALUES (?, 'RB2510')", [pid]
        )
        sid = int(store.query("SELECT symbol_id FROM symbols WHERE code='RB2510'").iloc[0]["symbol_id"])
        df = pd.DataFrame({
            "datetime": pd.to_datetime(["2026-01-01", "2026-01-02"]),
            "symbol_id": sid, "timeframe": "D1",
            "open": [1.0, 2.0], "high": [1, 2], "low": [1, 2],
            "close": [1.5, 2.5], "volume": [10, 20],
        })
        assert store.upsert_df("kline", df, ["datetime", "symbol_id", "timeframe"]) == 2
        # re-upsert same keys -> no duplicates
        store.upsert_df("kline", df, ["datetime", "symbol_id", "timeframe"])
        assert int(store.query("SELECT count(*) n FROM kline").iloc[0]["n"]) == 2

    def test_upsert_empty_df(self, store):
        assert store.upsert_df("kline", pd.DataFrame(), ["datetime"]) == 0


# ---- SymbolRegistry --------------------------------------------------------

class TestSymbolRegistry:
    def test_parse_futures(self, store):
        r = SymbolRegistry(store)
        assert r.parse_contract("RB2509") == {"contract_year": 2025, "contract_month": "09"}

    def test_parse_option(self, store):
        r = SymbolRegistry(store)
        meta = r.parse_contract("IO2509-C-3700")
        assert meta["option_type"] == "call"
        assert meta["strike_price"] == 3700.0
        assert meta["contract_month"] == "09"

    def test_parse_stock_empty(self, store):
        r = SymbolRegistry(store)
        assert r.parse_contract("600019") == {}

    def test_get_or_create_idempotent(self, store):
        r = SymbolRegistry(store)
        a = r.get_or_create_symbol("RB2510", "RB", asset_type="futures", exchange="SHFE")
        b = r.get_or_create_symbol("RB2510", "RB")
        assert a == b

    def test_split_yearmonth(self):
        assert _split_yearmonth("2509") == (2025, "09")
        assert _split_yearmonth("2601")[1] == "01"


# ---- aggregator ------------------------------------------------------------

class TestAggregator:
    def test_d1_to_w1(self, store):
        from data_center.aggregator import aggregate_symbol
        store.execute("INSERT INTO products (code,name,asset_type) VALUES ('RB','螺纹钢','futures')")
        pid = int(store.query("SELECT product_id FROM products WHERE code='RB'").iloc[0]["product_id"])
        store.execute("INSERT INTO symbols (product_id,code) VALUES (?, 'RB2510')", [pid])
        sid = int(store.query("SELECT symbol_id FROM symbols WHERE code='RB2510'").iloc[0]["symbol_id"])
        # 10 consecutive business days
        days = pd.bdate_range("2026-01-05", periods=10)
        df = pd.DataFrame({
            "datetime": days, "symbol_id": sid, "timeframe": "D1",
            "open": range(10), "high": range(1, 11), "low": range(10),
            "close": range(10), "volume": [100] * 10,
        })
        store.upsert_df("kline", df, ["datetime", "symbol_id", "timeframe"])
        res = aggregate_symbol(sid, store)
        assert res.get("W1", 0) >= 2  # 10 bdays span 2-3 weeks
        w1 = store.query("SELECT count(*) n FROM kline WHERE symbol_id=? AND timeframe='W1'", [sid])
        assert int(w1.iloc[0]["n"]) >= 2


# ---- MacroCollector date parsing ------------------------------------------

class TestMacroDateParse:
    def test_month_format(self):
        s = pd.Series(["2026年05月份", "2025年12月份"])
        out = MacroCollector._parse_date(s)
        assert str(out.iloc[0])[:7] == "2026-05"
        assert str(out.iloc[1])[:7] == "2025-12"

    def test_quarter_format(self):
        s = pd.Series(["2026年第1季度", "2025年第1-4季度", "2024年第3季度"])
        out = MacroCollector._parse_date(s)
        assert str(out.iloc[0])[:7] == "2026-03"
        assert str(out.iloc[1])[:7] == "2025-12"  # full year -> Q4
        assert str(out.iloc[2])[:7] == "2024-09"
