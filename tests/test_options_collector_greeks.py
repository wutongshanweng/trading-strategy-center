"""OptionsCollector 商品期权 Greeks 编排 — 集成测试 (内存库, 注入合成数据)。"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pytest

from data_center.storage.duckdb_store import DuckDBStore
from data_center.db.registry import SymbolRegistry
from data_center.collectors.options_collector import OptionsCollector


@pytest.fixture
def store(tmp_path):
    s = DuckDBStore(db_path=tmp_path / "opt.duckdb")
    yield s
    s.close()


def _seed_underlying(store, registry, code="M2608", close=2800.0, on="2026-06-15"):
    sid = registry.get_or_create_symbol(code, "M", asset_type="futures", name=code)
    store.upsert_df("kline", pd.DataFrame({
        "datetime": [pd.Timestamp(on)], "symbol_id": [sid], "timeframe": ["D1"],
        "close": [close], "settlement": [close],
    }), ["datetime", "symbol_id", "timeframe"])
    return sid


def test_commodity_greeks_end_to_end(store, monkeypatch):
    reg = SymbolRegistry(store)
    _seed_underlying(store, reg, "M2608", 2800.0, "2026-06-15")
    coll = OptionsCollector(store=store, registry=reg)

    # 注入合成商品期权日线 (绕过网络)
    fake = pd.DataFrame({
        "合约代码": ["m2608-C-2700", "m2608-P-2900"],
        "收盘价": [130.0, 140.0],
    })
    monkeypatch.setattr(coll._opt, "get_commodity_option_daily",
                        lambda *a, **k: fake)

    n = coll.collect_commodity_greeks("大商所", "豆粕期权", trade_date="2026-06-15")
    assert n == 2

    rows = store.query("SELECT * FROM options_daily ORDER BY symbol_id")
    assert len(rows) == 2
    # IV 应为正、Delta 在合理区间、标的价回填
    assert (rows["iv"] > 0).all()
    assert rows["underlying_close"].iloc[0] == 2800.0
    call = rows[rows["delta"] > 0]   # 看涨 delta>0
    put = rows[rows["delta"] < 0]    # 看跌 delta<0
    assert len(call) == 1 and len(put) == 1


def test_commodity_greeks_skips_when_no_underlying(store, monkeypatch):
    """标的期货不在库 -> 跳过该合约, 不报错。"""
    reg = SymbolRegistry(store)
    coll = OptionsCollector(store=store, registry=reg)
    fake = pd.DataFrame({"合约代码": ["m2608-C-2700"], "收盘价": [130.0]})
    monkeypatch.setattr(coll._opt, "get_commodity_option_daily", lambda *a, **k: fake)
    n = coll.collect_commodity_greeks("大商所", "豆粕期权", trade_date="2026-06-15")
    assert n == 0


def test_resolve_expiry_fallback(store):
    """无 expire_date 时回退到交割月前一月月末。"""
    reg = SymbolRegistry(store)
    coll = OptionsCollector(store=store, registry=reg)
    exp = coll._resolve_expiry("M2608-C-2700", 2026, "08")
    assert exp.year == 2026 and exp.month == 7  # 8月交割 -> 7月末到期
