"""商品期权按年逐日采集 — 单测 (内存库, 合成三所格式日线)。"""

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
def coll(tmp_path):
    s = DuckDBStore(db_path=tmp_path / "copt.duckdb")
    yield OptionsCollector(store=s, registry=SymbolRegistry(s))
    s.close()


def test_store_czce_day(coll):
    """CZCE 格式 SR609C4600 + 隐含波动率 + DELTA。"""
    df = pd.DataFrame({
        "合约代码": ["SR609C4600", "SR609P4800"],
        "今收盘": [732.0, 120.0],
        "持仓量": [14.0, 200.0], "成交量(手)": [0.0, 10.0],
        "DELTA": [0.9991, -0.35], "隐含波动率": [15.16, 13.5],
    })
    k, g = coll._store_commodity_day(df, "白糖期权", pd.Timestamp("2026-06-18"))
    assert k == 2 and g == 2
    od = coll.store.query("SELECT * FROM options_daily ORDER BY symbol_id")
    assert (od["iv"] > 0).all()
    # 看涨 delta>0, 看跌 delta<0
    assert od["delta"].max() > 0 and od["delta"].min() < 0


def test_store_shfe_day_no_iv(coll):
    """SHFE 格式 cu2607C76000 + 德尔塔 (无IV列)。"""
    df = pd.DataFrame({
        "合约代码": ["cu2607C76000"],
        "收盘价": [1500.0], "持仓量": [50.0], "成交量": [5.0],
        "德尔塔": [0.55],
    })
    k, g = coll._store_commodity_day(df, "铜期权", pd.Timestamp("2026-06-18"))
    assert k == 1 and g == 1
    od = coll.store.query("SELECT * FROM options_daily").iloc[0]
    assert od["delta"] == 0.55
    assert pd.isna(od["iv"])      # SHFE 无 IV


def test_contract_year_populated(coll):
    """合约入库后 contract_year 正确 (供按年面板统计)。"""
    df = pd.DataFrame({"合约代码": ["SR609C4600"], "今收盘": [732.0],
                       "DELTA": [0.99], "隐含波动率": [15.0]})
    coll._store_commodity_day(df, "白糖期权", pd.Timestamp("2026-06-18"))
    sym = coll.store.query("SELECT code, contract_year, option_type, strike_price FROM symbols").iloc[0]
    assert int(sym["contract_year"]) == 2026
    assert sym["option_type"] == "call"
    assert float(sym["strike_price"]) == 4600.0


def test_skips_non_option_rows(coll):
    df = pd.DataFrame({"合约代码": ["小计", "SR609C4600"], "今收盘": [0.0, 732.0],
                       "DELTA": [0.0, 0.99], "隐含波动率": [0.0, 15.0]})
    k, g = coll._store_commodity_day(df, "白糖期权", pd.Timestamp("2026-06-18"))
    assert k == 1   # 只存 1 个真实合约, "小计" 行跳过
