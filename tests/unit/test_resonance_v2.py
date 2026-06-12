import pytest
from datetime import datetime
from signals.base import Signal, Direction
from core.resonance.voter import VoterEngine
from core.resonance.matrix import MatrixEngine
from core.resonance.scanner import ScannerEngine
from core.resonance.engine_v2 import ResonanceEngineV2, ResonanceOutputV2


def _make_signal(source_system="", strategy_name="", score=5.0, confidence=0.8, direction=Direction.BUY):
    return Signal(
        symbol="BTC",
        direction=direction,
        confidence=confidence,
        score=score,
        price=100.0,
        timestamp=datetime.now(),
        reason="test",
        strategy_name=strategy_name,
        source_system=source_system,
    )


class TestVoterEngine:
    def test_empty_signals(self):
        assert VoterEngine().calculate([]) == 0.0

    def test_single_signal(self):
        sig = _make_signal(score=5.0)
        result = VoterEngine().calculate([sig])
        assert result == pytest.approx(5.0)

    def test_multiple_signals_same_direction(self):
        sigs = [_make_signal(score=10.0, confidence=0.8) for _ in range(3)]
        result = VoterEngine().calculate(sigs)
        assert result == pytest.approx(10.0)

    def test_sell_direction_inverts(self):
        sig = _make_signal(score=8.0, direction=Direction.SELL)
        result = VoterEngine().calculate([sig])
        assert result == pytest.approx(-8.0)

    def test_weighted_average(self):
        sig1 = _make_signal(score=10.0, confidence=1.0)
        sig2 = _make_signal(score=0.0, confidence=0.0)
        result = VoterEngine().calculate([sig1, sig2])
        assert result == pytest.approx(10.0)

    def test_score_clamp(self):
        sig = _make_signal(score=20.0, confidence=1.0)
        result = VoterEngine().calculate([sig])
        assert result == pytest.approx(10.0)


class TestMatrixEngine:
    def test_empty_signals(self):
        assert MatrixEngine().calculate([]) == 0.0

    def test_single_signal(self):
        sig = _make_signal(score=5.0)
        result = MatrixEngine().calculate([sig])
        assert result == pytest.approx(5.0)

    def test_consistent_signals_high_score(self):
        sigs = [_make_signal(score=8.0, confidence=0.9) for _ in range(3)]
        result = MatrixEngine().calculate(sigs)
        assert result > 5.0

    def test_inconsistent_signals_lower_score(self):
        sig1 = _make_signal(score=10.0, confidence=0.9)
        sig2 = _make_signal(score=-5.0, confidence=0.9)
        sig3 = _make_signal(score=8.0, confidence=0.9)
        result = MatrixEngine().calculate([sig1, sig2, sig3])
        assert result < 10.0


class TestScannerEngine:
    def test_empty_signals(self):
        assert ScannerEngine().calculate([]) == 0.0

    def test_below_threshold_filtered(self):
        sig = _make_signal(score=1.0)
        result = ScannerEngine(threshold=2.0).calculate([sig])
        assert result == 0.0

    def test_above_threshold_included(self):
        sig = _make_signal(score=5.0)
        result = ScannerEngine(threshold=2.0).calculate([sig])
        assert result == pytest.approx(5.0)

    def test_mixed_signals(self):
        sig1 = _make_signal(score=1.0)
        sig2 = _make_signal(score=8.0)
        result = ScannerEngine(threshold=2.0).calculate([sig1, sig2])
        assert result == pytest.approx(8.0)

    def test_custom_threshold(self):
        sig = _make_signal(score=3.0)
        result = ScannerEngine(threshold=4.0).calculate([sig])
        assert result == 0.0


class TestResonanceEngineV2:
    def test_output_type(self):
        sigs = [_make_signal(source_system="guanshan")]
        result = ResonanceEngineV2().calculate("BTC", sigs)
        assert isinstance(result, ResonanceOutputV2)
        assert result.symbol == "BTC"

    def test_empty_signals(self):
        result = ResonanceEngineV2().calculate("BTC", [])
        assert result.direction == "HOLD"
        assert result.final_score == pytest.approx(0.0)

    def test_group_by_source_guanshan(self):
        sigs = [_make_signal(source_system="guanshan", score=5.0) for _ in range(3)]
        result = ResonanceEngineV2().calculate("BTC", sigs)
        assert result.score_G != 0.0
        assert result.score_C == 0.0
        assert result.score_T == 0.0

    def test_group_by_source_chufeng(self):
        sigs = [_make_signal(source_system="chufeng", score=5.0) for _ in range(3)]
        result = ResonanceEngineV2().calculate("BTC", sigs)
        assert result.score_G == 0.0
        assert result.score_C != 0.0
        assert result.score_T == 0.0

    def test_group_by_source_tinghai(self):
        sigs = [_make_signal(source_system="tinghai", score=5.0) for _ in range(3)]
        result = ResonanceEngineV2().calculate("BTC", sigs)
        assert result.score_G == 0.0
        assert result.score_C == 0.0
        assert result.score_T != 0.0

    def test_infer_source_from_strategy_name(self):
        sigs = [_make_signal(strategy_name="trend_ma_cross", score=5.0)]
        result = ResonanceEngineV2().calculate("BTC", sigs)
        assert result.score_C != 0.0

    def test_weights_sum_to_one(self):
        result = ResonanceEngineV2().calculate("BTC", [], "BULL")
        total = result.weight_G + result.weight_C + result.weight_T
        assert total == pytest.approx(1.0, abs=0.01)

    def test_regime_bull_adjusts_weights(self):
        result = ResonanceEngineV2().calculate("BTC", [], "BULL")
        assert result.weight_G > 0.33

    def test_regime_bear_adjusts_weights(self):
        result = ResonanceEngineV2().calculate("BTC", [], "BEAR")
        assert result.weight_C > 0.33

    def test_regime_ranging_adjusts_weights(self):
        result = ResonanceEngineV2().calculate("BTC", [], "RANGING")
        assert result.weight_T > 0.34

    def test_strong_buy_direction(self):
        sigs = [_make_signal(source_system="guanshan", score=10.0, confidence=1.0) for _ in range(5)]
        result = ResonanceEngineV2().calculate("BTC", sigs, "BULL")
        assert result.direction == "BUY"

    def test_strong_sell_direction(self):
        sigs = [_make_signal(source_system="guanshan", score=10.0, confidence=1.0, direction=Direction.SELL) for _ in range(5)]
        result = ResonanceEngineV2().calculate("BTC", sigs, "BEAR")
        assert result.direction == "SELL"

    def test_confidence_range(self):
        sigs = [_make_signal(source_system="guanshan", score=5.0)]
        result = ResonanceEngineV2().calculate("BTC", sigs)
        assert 0.0 <= result.confidence <= 1.0
