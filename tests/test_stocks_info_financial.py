"""StocksCollector 信息/财务落库 — 单测 (内存库, 合成 akshare 格式)。"""

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
def coll(tmp_path):
    s = DuckDBStore(db_path=tmp_path / "info.duckdb")
    yield StocksCollector(store=s, registry=SymbolRegistry(s))
    s.close()


def test_store_info(coll):
    # stock_individual_info_em 格式: item/value 两列
    df = pd.DataFrame({
        "item": ["股票简称", "行业", "上市时间", "总股本", "流通股", "总市值"],
        "value": ["宝钢股份", "钢铁", "20001212", "22282347500", "22282347500", "150000000000"],
    })
    n = coll._store_info(df, "600019.SH")
    assert n == 1
    row = coll.store.query("SELECT * FROM stocks_info").iloc[0]
    assert row["company_name"] == "宝钢股份"
    assert row["industry"] == "钢铁"
    assert str(row["listing_date"]).startswith("2000-12-12")
    assert int(row["total_shares"]) == 22282347500


def test_store_financial(coll):
    # stock_financial_abstract 格式: 指标行 × 报告期列
    df = pd.DataFrame({
        "选项": ["盈利能力", "盈利能力", "每股", "每股", "盈利能力"],
        "指标": ["营业总收入", "净利润", "基本每股收益", "每股净资产", "净资产收益率(ROE)"],
        "20240930": ["1000", "80", "0.36", "8.5", "12.5"],
        "20240630": ["650", "50", "0.22", "8.2", "8.0"],
    })
    n = coll._store_financial(df, "600019.SH")
    assert n == 2
    rows = coll.store.query("SELECT * FROM stocks_financial ORDER BY report_date").reset_index(drop=True)
    assert len(rows) == 2
    q3 = rows[rows["report_date"].astype(str) == "2024-09-30"].iloc[0]
    assert float(q3["revenue"]) == 1000.0
    assert float(q3["net_profit"]) == 80.0
    assert float(q3["eps"]) == 0.36
    assert float(q3["roe"]) == 12.5
    assert q3["report_type"] == "Q3"


def test_store_financial_no_date_cols(coll):
    df = pd.DataFrame({"选项": ["x"], "指标": ["营业收入"]})
    assert coll._store_financial(df, "600019.SH") == 0
