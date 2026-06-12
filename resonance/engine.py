from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np
from signals.base import Signal, Direction
from market_state.regime_detector import MarketRegime


@dataclass
class ResonanceOutput:
    symbol: str
    score_G: float = 0.0
    score_C: float = 0.0
    score_T: float = 0.0
    final_score: float = 0.0
    direction: Direction = Direction.HOLD
    confidence: float = 0.0
    regime: Optional[MarketRegime] = None
    weights: Dict[str, float] = field(default_factory=lambda: {"G": 0.33, "C": 0.33, "T": 0.34})
    signals_used: int = 0


class ResonanceEngine:
    def __init__(self, weight_learner=None):
        self.base_weights = {"G": 0.33, "C": 0.33, "T": 0.34}
        self.weight_learner = weight_learner

    def _score_signals(self, signals: List[Signal]) -> float:
        if not signals:
            return 0.0
        total_score = 0.0
        total_weight = 0.0
        for signal in signals:
            weight = signal.confidence
            total_score += signal.score * weight
            total_weight += weight
        return float(np.clip(total_score / (total_weight + 1e-8), -10.0, 10.0)) if total_weight > 0 else 0.0

    def _group_signals_by_source(self, signals: List[Signal]) -> Dict[str, List[Signal]]:
        groups: Dict[str, List[Signal]] = {"G": [], "C": [], "T": []}
        source_to_group = {"guanshan": "G", "chufeng": "C", "tinghai": "T"}
        for signal in signals:
            source = getattr(signal, 'source_system', None)
            if source and source in source_to_group:
                groups[source_to_group[source]].append(signal)
            else:
                inferred = self._infer_source(signal.strategy_name)
                groups[source_to_group[inferred]].append(signal)
        return groups

    def _infer_source(self, strategy_name: str) -> str:
        guanshan_prefixes = ['TT7_', 'OI_', 'Enhanced_']
        chufeng_prefixes = ['trend_', 'reversal_', 'breakout_', 'momentum_']
        tinghai_prefixes = ['filter_', 'layer_', 'chan_', 'ml_']

        for prefix in guanshan_prefixes:
            if strategy_name.startswith(prefix):
                return "guanshan"
        for prefix in chufeng_prefixes:
            if strategy_name.startswith(prefix):
                return "chufeng"
        for prefix in tinghai_prefixes:
            if strategy_name.startswith(prefix):
                return "tinghai"
        return "chufeng"

    def adjust_weights_for_regime(self, base_weights: Dict[str, float], regime: MarketRegime) -> Dict[str, float]:
        w = dict(base_weights)
        adjustments = {
            MarketRegime.BULL: {"G": 0.15, "C": -0.10, "T": -0.05},
            MarketRegime.BEAR: {"C": 0.15, "G": -0.10, "T": -0.05},
            MarketRegime.RANGING: {"T": 0.15, "G": -0.10, "C": -0.05},
            MarketRegime.CRASH: {"C": 0.10, "T": 0.05, "G": -0.15},
            MarketRegime.RECOVERY: {"G": 0.10, "T": 0.05, "C": -0.15},
        }
        if regime in adjustments:
            for k, v in adjustments[regime].items():
                w[k] = w.get(k, 0) + v
        total = sum(w.values())
        return {k: v / total for k, v in w.items()} if total > 0 else w

    def calculate(self, symbol: str, signals: List[Signal],
                  regime: Optional[MarketRegime] = None,
                  weighted_signals: Optional[Dict[str, List[Signal]]] = None) -> ResonanceOutput:
        if weighted_signals is None:
            weighted_signals = self._group_signals_by_source(signals) if signals else {"G": [], "C": [], "T": []}
        score_G = self._score_signals(weighted_signals.get("G", []))
        score_C = self._score_signals(weighted_signals.get("C", []))
        score_T = self._score_signals(weighted_signals.get("T", []))
        total_signals = sum(len(v) for v in weighted_signals.values())
        weights = self.adjust_weights_for_regime(self.base_weights, regime) if regime else dict(self.base_weights)
        final_score = weights["G"] * score_G + weights["C"] * score_C + weights["T"] * score_T
        direction = Direction.BUY if final_score > 2.0 else Direction.SELL if final_score < -2.0 else Direction.HOLD
        return ResonanceOutput(symbol=symbol, score_G=round(score_G, 4), score_C=round(score_C, 4),
                               score_T=round(score_T, 4), final_score=round(final_score, 4),
                               direction=direction, confidence=round(min(1.0, abs(final_score) / 10.0), 4),
                               regime=regime, weights=weights, signals_used=total_signals)

    def set_weights(self, G: float, C: float, T: float):
        total = G + C + T
        if total > 0:
            self.base_weights = {"G": G / total, "C": C / total, "T": T / total}
