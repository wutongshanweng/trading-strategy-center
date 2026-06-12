import pytest
from datetime import datetime
from signals.base import Signal, Direction
from resonance.engine import ResonanceEngine
from market_state.regime_detector import MarketRegime


def test_resonance_engine_groups_by_source_system():
    engine = ResonanceEngine()

    signals = [
        Signal(symbol="RB", direction=Direction.BUY, confidence=0.8, score=5.0, price=3850,
               timestamp=datetime.now(), reason="test", strategy_name="s1", source_system="guanshan"),
        Signal(symbol="RB", direction=Direction.BUY, confidence=0.8, score=5.0, price=3850,
               timestamp=datetime.now(), reason="test", strategy_name="s2", source_system="guanshan"),
        Signal(symbol="RB", direction=Direction.BUY, confidence=0.8, score=5.0, price=3850,
               timestamp=datetime.now(), reason="test", strategy_name="s3", source_system="guanshan"),
    ]

    result = engine.calculate("RB", signals, MarketRegime.RANGING)

    assert result.score_G != 0.0
    assert result.score_C == 0.0
    assert result.score_T == 0.0


def test_signal_without_source_system_gets_inferred():
    engine = ResonanceEngine()

    signals = [
        Signal(symbol="RB", direction=Direction.BUY, confidence=0.8, score=5.0, price=3850,
               timestamp=datetime.now(), reason="test", strategy_name="trend_ma_cross"),
        Signal(symbol="RB", direction=Direction.BUY, confidence=0.8, score=5.0, price=3850,
               timestamp=datetime.now(), reason="test", strategy_name="reversal_rsi"),
    ]

    result = engine.calculate("RB", signals, MarketRegime.RANGING)

    assert result.score_C != 0
    assert result.score_G == 0.0
    assert result.score_T == 0.0


def test_empty_signals():
    engine = ResonanceEngine()
    result = engine.calculate("RB", [], MarketRegime.RANGING)
    assert result.score_G == 0.0
    assert result.score_C == 0.0
    assert result.score_T == 0.0


def test_confidence_weighted_scoring():
    engine = ResonanceEngine()

    signals = [
        Signal(symbol="RB", direction=Direction.BUY, confidence=1.0, score=10.0, price=3850,
               timestamp=datetime.now(), reason="test", strategy_name="TT7_abc", source_system="guanshan"),
    ]

    result = engine.calculate("RB", signals, MarketRegime.RANGING)
    assert result.score_G > 0
