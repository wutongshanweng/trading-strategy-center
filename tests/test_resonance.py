import pytest
import pandas as pd
import numpy as np
from market_state.regime_detector import MarketRegimeDetector, MarketRegime, RegimeInfo
from market_state.state_machine import StateMachine
from market_state.entropy_analyzer import EntropyAnalyzer
from resonance.engine import ResonanceEngine, ResonanceOutput
from signals.base import Signal, Direction


@pytest.fixture
def sample_df():
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", periods=300, freq="D")
    price = 100.0
    prices = [price := price * (1 + np.random.normal(0.001, 0.01)) for _ in range(300)]
    return pd.DataFrame({"open": [p * 0.99 for p in prices], "high": [p * 1.015 for p in prices],
                          "low": [p * 0.985 for p in prices], "close": prices, "volume": np.random.randint(1000, 10000, 300)}, index=dates)


class TestRegimeDetector:
    def test_detect(self, sample_df):
        info = MarketRegimeDetector().detect(sample_df)
        assert isinstance(info, RegimeInfo) and isinstance(info.regime, MarketRegime)

    def test_empty(self):
        info = MarketRegimeDetector().detect(pd.DataFrame())
        assert info.regime == MarketRegime.RANGING and info.confidence == 0.0


class TestResonance:
    def test_output_type(self):
        sigs = [Signal(symbol="BTC", direction=Direction.BUY, confidence=0.8)]
        o = ResonanceEngine().calculate("BTC", sigs)
        assert isinstance(o, ResonanceOutput) and o.symbol == "BTC"

    def test_strong_buy(self):
        sigs = [Signal(symbol="BTC", direction=Direction.BUY, confidence=1.0, score=10.0) for _ in range(5)]
        o = ResonanceEngine().calculate("BTC", sigs)
        assert o.direction == Direction.BUY and o.final_score > 2.0

    def test_empty_hold(self):
        o = ResonanceEngine().calculate("BTC", [])
        assert o.direction == Direction.HOLD

    def test_weights_adjust_bull(self):
        w = ResonanceEngine().adjust_weights_for_regime({"G": 0.33, "C": 0.33, "T": 0.34}, MarketRegime.BULL)
        assert abs(sum(w.values()) - 1.0) < 0.01 and w["G"] > 0.33

    def test_weights_adjust_bear(self):
        w = ResonanceEngine().adjust_weights_for_regime({"G": 0.33, "C": 0.33, "T": 0.34}, MarketRegime.BEAR)
        assert abs(sum(w.values()) - 1.0) < 0.01 and w["C"] > 0.33


class TestStateMachine:
    def test_predict(self):
        sm = StateMachine()
        sm.update(MarketRegime.BULL)
        assert isinstance(sm.predict_next(MarketRegime.BULL), MarketRegime)

    def test_probs_sum(self):
        sm = StateMachine(); sm.update(MarketRegime.BULL); sm.update(MarketRegime.BEAR)
        assert abs(sum(sm.transition_probs(MarketRegime.BULL).values()) - 1.0) < 0.01


class TestEntropy:
    def test_entropy_bounds(self):
        e = EntropyAnalyzer().compute_entropy(pd.Series(np.random.randn(200)))
        assert 0.0 <= e <= 1.0

    def test_empty(self):
        assert EntropyAnalyzer().compute_market_efficiency(pd.DataFrame())["shannon_entropy"] == 0.0
