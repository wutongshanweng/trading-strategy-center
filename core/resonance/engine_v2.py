from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np
from signals.base import Signal, Direction
from .voter import VoterEngine
from .matrix import MatrixEngine
from .scanner import ScannerEngine


@dataclass
class ResonanceOutputV2:
    symbol: str
    score_G: float = 0.0
    score_C: float = 0.0
    score_T: float = 0.0
    final_score: float = 0.0
    direction: str = "HOLD"
    confidence: float = 0.0
    regime: str = "RANGING"
    weight_G: float = 0.33
    weight_C: float = 0.33
    weight_T: float = 0.34


class ResonanceEngineV2:
    def __init__(self):
        self.voter = VoterEngine()
        self.matrix = MatrixEngine()
        self.scanner = ScannerEngine(threshold=2.0)
        self.base_weights = {"G": 0.33, "C": 0.33, "T": 0.34}

    def _group_signals_by_source(self, signals: List[Signal]) -> Dict[str, List[Signal]]:
        groups: Dict[str, List[Signal]] = {"G": [], "C": [], "T": []}
        source_map = {"guanshan": "G", "chufeng": "C", "tinghai": "T"}

        for signal in signals:
            source = getattr(signal, "source_system", None)
            if source and source in source_map:
                groups[source_map[source]].append(signal)
            else:
                inferred = self._infer_source(signal.strategy_name)
                groups[inferred].append(signal)

        return groups

    def _infer_source(self, strategy_name: str) -> str:
        guanshan_prefixes = ["TT7_", "OI_", "Enhanced_"]
        chufeng_prefixes = ["trend_", "reversal_", "breakout_", "momentum_"]
        tinghai_prefixes = ["filter_", "layer_", "chan_", "ml_"]

        for prefix in guanshan_prefixes:
            if strategy_name.startswith(prefix):
                return "G"
        for prefix in chufeng_prefixes:
            if strategy_name.startswith(prefix):
                return "C"
        for prefix in tinghai_prefixes:
            if strategy_name.startswith(prefix):
                return "T"
        return "C"

    def _get_adjusted_weights(self, regime: str) -> Dict[str, float]:
        w = dict(self.base_weights)
        adjustments = {
            "BULL": {"G": 0.15, "C": -0.10, "T": -0.05},
            "BEAR": {"C": 0.15, "G": -0.10, "T": -0.05},
            "RANGING": {"T": 0.15, "G": -0.10, "C": -0.05},
            "CRASH": {"C": 0.10, "T": 0.05, "G": -0.15},
            "RECOVERY": {"G": 0.10, "T": 0.05, "C": -0.15},
        }

        if regime in adjustments:
            for k, v in adjustments[regime].items():
                w[k] = w.get(k, 0) + v

        total = sum(w.values())
        return {k: v / total for k, v in w.items()} if total > 0 else w

    def calculate(
        self,
        symbol: str,
        signals: List[Signal],
        regime: str = "RANGING",
    ) -> ResonanceOutputV2:
        groups = self._group_signals_by_source(signals) if signals else {"G": [], "C": [], "T": []}

        score_G = self.voter.calculate(groups.get("G", []))
        score_C = self.matrix.calculate(groups.get("C", []))
        score_T = self.scanner.calculate(groups.get("T", []))

        weights = self._get_adjusted_weights(regime)
        final_score = weights["G"] * score_G + weights["C"] * score_C + weights["T"] * score_T

        if final_score > 2.0:
            direction = "BUY"
        elif final_score < -2.0:
            direction = "SELL"
        else:
            direction = "HOLD"

        confidence = min(1.0, abs(final_score) / 10.0)

        return ResonanceOutputV2(
            symbol=symbol,
            score_G=round(score_G, 4),
            score_C=round(score_C, 4),
            score_T=round(score_T, 4),
            final_score=round(final_score, 4),
            direction=direction,
            confidence=round(confidence, 4),
            regime=regime,
            weight_G=round(weights["G"], 4),
            weight_C=round(weights["C"], 4),
            weight_T=round(weights["T"], 4),
        )
