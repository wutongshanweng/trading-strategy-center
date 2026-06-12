from typing import Tuple, Dict, List, Optional
import numpy as np
from .regime_detector_v2 import RegimeV2


class EnhancedStateMachine:
    def __init__(self, transition_matrix: Optional[List[List[float]]] = None,
                 min_duration: int = 5, penalty_factor: float = 0.8):
        self.min_duration = min_duration
        self.penalty_factor = penalty_factor
        self.regimes = list(RegimeV2)
        self.n = len(self.regimes)
        self._index = {r: i for i, r in enumerate(self.regimes)}
        
        if transition_matrix is None:
            # Default uniform transitions with high self-transition probability
            default_prob = (1.0 - 0.7) / (self.n - 1) if self.n > 1 else 0.0
            self.transition_matrix = np.full((self.n, self.n), default_prob, dtype=float)
            np.fill_diagonal(self.transition_matrix, 0.7)
        else:
            self.transition_matrix = np.array(transition_matrix, dtype=float)
            if self.transition_matrix.shape != (self.n, self.n):
                raise ValueError(f"Transition matrix must be {self.n}x{self.n}")
        
        self._current_state: Optional[RegimeV2] = None
        self._state_duration: int = 0
        self._step_count: int = 0

    def reset(self) -> None:
        """Reset state machine to initial state."""
        self._current_state = None
        self._state_duration = 0
        self._step_count = 0

    def next_state(self, observation: str, confidence: float) -> Tuple[str, float]:
        """Determine next state based on observation and confidence.
        
        Args:
            observation: regime label (QUIET, TRENDING, VOLATILE, CRISIS)
            confidence: confidence in observation (0-1)
        
        Returns:
            (state, confidence) after applying state machine logic
        """
        try:
            obs_regime = RegimeV2(observation)
        except ValueError:
            raise ValueError(f"Invalid observation: {observation}. Must be one of {[r.value for r in RegimeV2]}")
        
        if self._current_state is None:
            # First step
            self._current_state = obs_regime
            self._state_duration = 1
            self._step_count = 1
            return (obs_regime.value, confidence)
        
        if obs_regime == self._current_state:
            # Same state, increment duration
            self._state_duration += 1
            self._step_count += 1
            return (self._current_state.value, confidence)
        
        # Different state observed
        if self._state_duration < self.min_duration:
            # Not enough time in current state, stay with penalized confidence
            self._step_count += 1
            return (self._current_state.value, confidence * self.penalty_factor)
        
        # Enough time passed, consider transition
        i = self._index[self._current_state]
        j = self._index[obs_regime]
        raw_prob = self.transition_matrix[i, j]
        
        # Apply penalty to off-diagonal transitions
        effective_prob = raw_prob * self.penalty_factor
        
        # Decision: transition if effective probability > 0.5
        if effective_prob > 0.5:
            self._current_state = obs_regime
            self._state_duration = 1
            new_confidence = confidence * effective_prob
        else:
            new_confidence = confidence * self.penalty_factor
        
        self._step_count += 1
        return (self._current_state.value, new_confidence)

    def get_transition_probability(self, from_state: str, to_state: str) -> float:
        """Get transition probability between two states."""
        try:
            from_regime = RegimeV2(from_state)
            to_regime = RegimeV2(to_state)
        except ValueError:
            raise ValueError("Invalid state name")
        i = self._index[from_regime]
        j = self._index[to_regime]
        return float(self.transition_matrix[i, j])

    def get_current_state(self) -> Optional[str]:
        """Get current state label."""
        return self._current_state.value if self._current_state else None

    def get_state_duration(self) -> int:
        """Get duration in current state."""
        return self._state_duration

    def get_transition_matrix(self) -> Dict[str, Dict[str, float]]:
        """Get transition matrix as nested dict."""
        matrix = {}
        for i, from_regime in enumerate(self.regimes):
            matrix[from_regime.value] = {}
            for j, to_regime in enumerate(self.regimes):
                matrix[from_regime.value][to_regime.value] = float(self.transition_matrix[i, j])
        return matrix