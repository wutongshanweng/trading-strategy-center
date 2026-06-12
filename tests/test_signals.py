import pytest
import pandas as pd
import numpy as np
from signals.base import Signal, Direction, BaseStrategy
from signals.indicators import (
    SMA, RSI, MACD, ATR, BB, KDJ, AROON, CCI, OBV, VWAP, DONCHIAN, ADX,
    SUPERTREND, WILLIAMS_R, MFI, TRIX, AROON_OSCILLATOR,
)
from signals.registry import register, get_strategy, list_strategies, get_all_strategies
from signals.engine import StrategyEngine


@pytest.fixture
def ohlcv_df():
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    price = 100.0
    prices = []
    for _ in range(100):
        price *= 1 + np.random.normal(0.0005, 0.015)
        prices.append(price)
    return pd.DataFrame({"open": [p * 0.99 for p in prices], "high": [p * 1.02 for p in prices],
                          "low": [p * 0.98 for p in prices], "close": prices, "volume": np.random.randint(1000, 10000, 100)}, index=dates)


class TestIndicators:
    def test_sma_shape(self, ohlcv_df):
        r = SMA(ohlcv_df["close"], 5)
        assert len(r) == 100 and r.iloc[:4].isna().all() and not r.iloc[4:].isna().any()

    def test_rsi_bounds(self, ohlcv_df):
        r = RSI(ohlcv_df["close"], 14).dropna()
        assert r.between(0, 100).all()

    def test_macd_three_series(self, ohlcv_df):
        a, b, c = MACD(ohlcv_df["close"])
        assert all(isinstance(x, pd.Series) for x in (a, b, c))

    def test_atr_positive(self, ohlcv_df):
        assert (ATR(ohlcv_df, 14).dropna() > 0).all()

    def test_supertrend(self, ohlcv_df):
        st, direction = SUPERTREND(ohlcv_df, period=10, multiplier=3.0)
        assert isinstance(st, pd.Series)
        assert isinstance(direction, pd.Series)
        assert len(st) == len(ohlcv_df)
        assert set(direction.dropna().unique()).issubset({-1, 1})

    def test_williams_r_bounds(self, ohlcv_df):
        wr = WILLIAMS_R(ohlcv_df, 14).dropna()
        assert wr.between(-100, 0).all()

    def test_mfi_bounds(self, ohlcv_df):
        mfi = MFI(ohlcv_df, 14).dropna()
        assert mfi.between(0, 100).all()

    def test_trix(self, ohlcv_df):
        result = TRIX(ohlcv_df["close"], 15)
        assert isinstance(result, pd.Series)
        assert len(result) == len(ohlcv_df)

    def test_aroon_oscillator(self, ohlcv_df):
        result = AROON_OSCILLATOR(ohlcv_df, 14)
        assert isinstance(result, pd.Series)
        assert len(result) == len(ohlcv_df)
        assert result.dropna().between(-100, 100).all()


class TestSignal:
    def test_create(self):
        s = Signal(symbol="BTC", direction=Direction.BUY, confidence=0.85)
        assert s.symbol == "BTC" and s.confidence == 0.85

    def test_defaults(self):
        s = Signal(symbol="ETH", direction=Direction.HOLD, confidence=0.0)
        assert s.timeframe == "1d" and s.reason == ""

    def test_score_default(self):
        s = Signal(symbol="BTC", direction=Direction.BUY, confidence=0.85)
        assert s.score == 0.0

    def test_score_with_value(self):
        s = Signal(symbol="BTC", direction=Direction.BUY, confidence=0.85, score=7.5)
        assert s.score == 7.5

    def test_new_fields_defaults(self):
        s = Signal(symbol="BTC", direction=Direction.BUY, confidence=0.85)
        assert s.score == 0.0
        assert s.source_system == ""
        assert s.resonance_layer == ""
        assert s.metadata == {}

    def test_new_fields_with_values(self):
        s = Signal(
            symbol="BTC",
            direction=Direction.BUY,
            confidence=0.85,
            source_system="momentum_engine",
            resonance_layer="primary",
            metadata={"key": "value", "score": 0.9}
        )
        assert s.source_system == "momentum_engine"
        assert s.resonance_layer == "primary"
        assert s.metadata == {"key": "value", "score": 0.9}

    def test_extra_field_backward_compatible(self):
        s = Signal(
            symbol="BTC",
            direction=Direction.BUY,
            confidence=0.85,
            extra={"old_key": "old_value"}
        )
        assert s.extra == {"old_key": "old_value"}
        assert s.metadata == {}

    def test_optional_price_and_timestamp(self):
        s = Signal(symbol="BTC", direction=Direction.BUY, confidence=0.85)
        assert s.price is None
        assert s.timestamp is not None


class TestRegistry:
    def test_register_and_get(self):
        @register
        class T(BaseStrategy):
            name = "_test_reg"
            description = ""
            def compute(self, df, symbol=""): pass
        assert get_strategy("_test_reg") is T

    def test_list(self):
        assert isinstance(list_strategies(), list)

    def test_unknown(self):
        assert get_strategy("_nonexistent_xyz") is None


class TestEngine:
    def test_load_compute(self, ohlcv_df):
        e = StrategyEngine(); e.load_all()
        assert e.count > 0
        r = e.compute_all(ohlcv_df, "TEST")
        assert isinstance(r, list) and all(isinstance(x, Signal) for x in r)

    def test_named_unknown(self, ohlcv_df):
        assert StrategyEngine().compute_named("_no_exist", ohlcv_df) is None
