"""缠论专业版引擎集成 (chan.py vendored) — 单测。

合成合法 OHLC, 不触网/不触库。验证引擎产出 + 策略注册 + 信号。
"""

import numpy as np
import pandas as pd
import pytest


def _synth_ohlc(n=250, seed=7):
    np.random.seed(seed)
    t = np.arange(n)
    base = 3000 + 250 * np.sin(t / 18) + t * 1.5 + np.random.normal(0, 12, n)
    o = base + np.random.normal(0, 5, n)
    c = base + np.random.normal(0, 5, n)
    hi = np.maximum(o, c) + abs(np.random.normal(8, 4, n))
    lo = np.minimum(o, c) - abs(np.random.normal(8, 4, n))
    return pd.DataFrame({"open": o, "high": hi, "low": lo, "close": c},
                        index=pd.date_range("2024-01-01", periods=n, freq="D"))


class TestChanProEngine:
    def test_compute_bsp_structure(self):
        from analysis.chan_pro import get_engine
        res = get_engine().compute_bsp(_synth_ohlc(), "TEST")
        assert res["error"] is None
        assert res["n_bi"] >= 1
        assert isinstance(res["bsp"], list)
        for b in res["bsp"]:
            assert "is_buy" in b and "type_str" in b and "price" in b

    def test_insufficient_data(self):
        from analysis.chan_pro import get_engine
        small = _synth_ohlc(n=20)
        res = get_engine().compute_bsp(small, "T")
        assert res["error"] is not None
        assert res["bsp"] == []

    def test_latest_signal_shape(self):
        from analysis.chan_pro import get_engine
        sig = get_engine().latest_signal(_synth_ohlc(), "T")
        assert sig["direction"] in ("BUY", "SELL", "HOLD")


class TestChanStrategy:
    def test_registered(self):
        import signals.strategies  # noqa: F401
        from signals.registry import list_strategies
        assert "chan_bsp" in list_strategies()

    def test_compute_returns_valid_signal_or_none(self):
        import signals.strategies  # noqa: F401
        from signals.registry import get_strategy
        from signals.base import Direction
        inst = get_strategy("chan_bsp")()
        sig = inst.compute(_synth_ohlc(), "TEST")
        if sig is not None:
            assert sig.direction in (Direction.BUY, Direction.SELL)
            assert 0 <= sig.confidence <= 1
            assert "缠论" in sig.reason

    def test_short_df_returns_none(self):
        import signals.strategies  # noqa: F401
        from signals.registry import get_strategy
        inst = get_strategy("chan_bsp")()
        assert inst.compute(_synth_ohlc(n=30), "T") is None
