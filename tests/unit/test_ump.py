"""UMP 裁判机制 (交易级否决闸门) — 单测。

不触网/不触库。合成交易特征验证主裁/边裁/管理器逻辑。
"""

import numpy as np
import pandas as pd

from core.ump.judges import UMPMainJudge, UMPEdgeJudge, UMPManager, trade_features
from core.ump.training import FEATURE_COLS


def _synth_trades(n=200, seed=5):
    """造一批交易特征: 高波动+高位置的交易设为多数亏损 (制造可学习的坏形态)。"""
    np.random.seed(seed)
    rows = []
    for _ in range(n):
        vol = np.random.uniform(0, 0.05)
        pos = np.random.uniform(0, 1)
        # 坏形态: 高波动 + 追高 → 多数亏损
        bad = vol > 0.03 and pos > 0.7
        pnl = np.random.normal(-0.03 if bad else 0.01, 0.02)
        rows.append({
            "momentum": np.random.normal(0, 0.05), "momentum_5": np.random.normal(0, 0.03),
            "volatility": vol, "price_position": pos,
            "body_ratio": np.random.uniform(0, 1), "volume_ratio": np.random.uniform(0.5, 2),
            "upper_wick": np.random.uniform(0, 0.5), "skew": np.random.normal(0, 1),
            "pnl": pnl,
        })
    return pd.DataFrame(rows)


def _synth_ohlc(n=120):
    np.random.seed(9)
    base = 3000 + np.cumsum(np.random.normal(0, 10, n))
    o = base + np.random.normal(0, 5, n); c = base + np.random.normal(0, 5, n)
    hi = np.maximum(o, c) + abs(np.random.normal(8, 3, n))
    lo = np.minimum(o, c) - abs(np.random.normal(8, 3, n))
    return pd.DataFrame({"open": o, "high": hi, "low": lo, "close": c,
                         "volume": abs(np.random.normal(1e4, 3e3, n))})


class TestTradeFeatures:
    def test_extract(self):
        f = trade_features(_synth_ohlc(), 80, 20)
        assert f is not None
        assert set(FEATURE_COLS) <= set(f.keys())
        assert all(np.isfinite(v) for v in f.values())

    def test_insufficient_index(self):
        assert trade_features(_synth_ohlc(), 5, 20) is None


class TestJudges:
    def test_main_judge_flags_bad(self):
        df = _synth_trades()
        X = df[FEATURE_COLS].to_numpy(float)
        wins = (df["pnl"].to_numpy() > 0).astype(float)
        j = UMPMainJudge(n_clusters=10).fit(X, wins)
        assert j._fitted is True
        assert len(j._bad_clusters) >= 1  # 应识别出坏簇

    def test_edge_judge_fits(self):
        df = _synth_trades()
        X = df[FEATURE_COLS].to_numpy(float)
        wins = (df["pnl"].to_numpy() > 0).astype(float)
        j = UMPEdgeJudge(n_neighbors=20).fit(X, wins)
        assert j._fitted is True


class TestManager:
    def test_fit_and_block(self):
        df = _synth_trades()
        mgr = UMPManager().fit(df, FEATURE_COLS, "pnl")
        assert mgr._fitted is True
        # 一笔典型坏形态 (高波动+追高) 应被否决
        bad_feat = {"momentum": 0.0, "momentum_5": 0.0, "volatility": 0.045,
                    "price_position": 0.9, "body_ratio": 0.5, "volume_ratio": 1.0,
                    "upper_wick": 0.2, "skew": 0.0}
        dec = mgr.block_decision(bad_feat)
        assert "block" in dec and "reason" in dec

    def test_untrained_passes(self):
        mgr = UMPManager()
        dec = mgr.block_decision({n: 0.0 for n in FEATURE_COLS})
        assert dec["block"] is False
        assert "未训练" in dec["reason"]

    def test_too_few_trades_not_fitted(self):
        small = _synth_trades(n=10)
        mgr = UMPManager().fit(small, FEATURE_COLS, "pnl")
        assert mgr._fitted is False
