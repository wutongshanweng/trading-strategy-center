"""合约生命周期 — 单测 (纯函数, 合成数据)。"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date

import pandas as pd

from data_center.knowledge.contract_lifecycle import (
    parse_expiry, status, lifecycle_window, lifecycle_guard,
)


def test_parse_expiry_futures():
    # M2609 = 2026年9月交割 -> 到期 2026-09-30
    assert parse_expiry("M2609") == date(2026, 9, 30)
    assert parse_expiry("RB2510") == date(2025, 10, 31)


def test_parse_expiry_continuous_none():
    assert parse_expiry("M") is None       # 纯品种
    assert parse_expiry("RB") is None


def test_status():
    # today 固定为 2026-06-19
    t = date(2026, 6, 19)
    assert status("M2609", t) == "在挂"      # 9月还没到
    assert status("RB2505", t) == "已到期"   # 2025年5月已过
    assert status("M", t) == "连续"          # 纯品种


def test_lifecycle_window():
    win = lifecycle_window("M2609")
    assert win is not None
    earliest, exp = win
    assert exp == date(2026, 9, 30)
    assert earliest == date(2023, 9, 30)     # 到期 - 3年


def test_guard_clips_continuous_data_mislabeled_as_contract():
    """M2609 误存了 2005 年起的连续数据 -> 守卫裁掉生命周期外的行。"""
    df = pd.DataFrame({
        "datetime": pd.to_datetime(["2005-01-04", "2020-06-01", "2025-09-15", "2026-06-18"]),
        "close": [2000, 2500, 2919, 2900],
    })
    out = lifecycle_guard(df, "M2609", "datetime")
    kept = [str(d.date()) for d in pd.to_datetime(out["datetime"])]
    assert "2005-01-04" not in kept          # 生命周期外, 裁掉
    assert "2020-06-01" not in kept          # 仍在窗口外 (>3年)
    assert "2025-09-15" in kept              # 真实生命周期内, 保留
    assert "2026-06-18" in kept


def test_guard_leaves_continuous_untouched():
    """纯品种/连续合约无固定到期 -> 不裁剪。"""
    df = pd.DataFrame({
        "datetime": pd.to_datetime(["2005-01-04", "2026-06-18"]),
        "close": [2000, 2900],
    })
    out = lifecycle_guard(df, "M", "datetime")
    assert len(out) == 2
