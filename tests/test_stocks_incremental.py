"""StocksCollector.incremental_sync — 单测 (内存库, mock 网络)。"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pytest

from data_center.storage.duckdb_store import DuckDBStore
from data_center.db.registry import SymbolRegistry
from data_center.collectors.stocks_collector import StocksCollector


@pytest.fixture
def store(tmp_path):
    s = DuckDBStore(db_path=tmp_path / "stk.duckdb")
    yield s
    s.close()


def _seed_stock(store, reg, code, last_date):
    sid = reg.get_or_create_symbol(code, code, asset_type="stock", name=code)
    store.upsert_df("kline", pd.DataFrame({
        "datetime": [pd.Timestamp(last_date)], "symbol_id": [sid],
        "timeframe": ["D1"], "close": [10.0],
    }), ["datetime", "symbol_id", "timeframe"])


def test_incremental_skips_uptodate_and_syncs_stale(store, monkeypatch):
    reg = SymbolRegistry(store)
    _seed_stock(store, reg, "600000.SH", "2026-06-15")  # 已最新
    _seed_stock(store, reg, "600001.SH", "2026-05-01")  # 落后
    coll = StocksCollector(store=store, registry=reg)

    # 最近交易日 = 2026-06-15
    monkeypatch.setattr(coll, "_latest_trade_date", lambda: pd.Timestamp("2026-06-15"))
    calls = []
    monkeypatch.setattr(coll, "collect_kline",
                        lambda code, start_date=None: calls.append((code, start_date)) or 3)

    stats = coll.incremental_sync(symbols=["600000.SH", "600001.SH", "600002.SH"])

    assert stats["skipped"] == 1          # 600000 已最新
    assert stats["new"] == 1              # 600002 未入库
    assert stats["synced"] == 2           # 600001 补齐 + 600002 全量
    synced_codes = {c for c, _ in calls}
    assert synced_codes == {"600001.SH", "600002.SH"}
    # 落后票从 (最新-buffer) 起, 新票从 full_start 起
    starts = dict(calls)
    assert starts["600002.SH"] == "2015-01-01"
    assert starts["600001.SH"] < "2026-05-01"  # buffer 回退


def test_incremental_all_uptodate(store, monkeypatch):
    reg = SymbolRegistry(store)
    _seed_stock(store, reg, "600000.SH", "2026-06-15")
    coll = StocksCollector(store=store, registry=reg)
    monkeypatch.setattr(coll, "_latest_trade_date", lambda: pd.Timestamp("2026-06-15"))
    monkeypatch.setattr(coll, "collect_kline", lambda *a, **k: 0)
    stats = coll.incremental_sync(symbols=["600000.SH"])
    assert stats["skipped"] == 1 and stats["synced"] == 0
