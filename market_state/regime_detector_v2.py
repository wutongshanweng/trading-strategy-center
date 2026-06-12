from enum import Enum
from typing import List, Tuple, Dict, Any
import pandas as pd
import numpy as np
from hmmlearn import hmm


class RegimeV2(Enum):
    QUIET = "QUIET"
    TRENDING = "TRENDING"
    VOLATILE = "VOLATILE"
    CRISIS = "CRISIS"


class HMMDetector:
    def __init__(self, n_regimes: int = 4, covariance_type: str = 'full', n_iter: int = 100):
        self.n_regimes = n_regimes
        self.covariance_type = covariance_type
        self.n_iter = n_iter
        self.model = None
        self._fitted = False
        self._state_to_regime: Dict[int, RegimeV2] = {}

    def _map_states_to_regimes(self) -> Dict[int, RegimeV2]:
        """Map HMM states to regimes based on mean and variance."""
        means = self.model.means_.flatten()
        covars = self.model.covars_
        if covars.ndim == 3:
            # (n_states, n_features, n_features)
            variances = covars[:, 0, 0]
        else:
            # (n_states, n_features, n_features) but maybe 2D if n_features=1
            variances = np.diag(covars)
        
        # Sort states by volatility (ascending) and mean absolute value (descending)
        vol = np.sqrt(variances)
        abs_mean = np.abs(means)
        
        # Create list of tuples (state_idx, vol, abs_mean)
        stats = [(i, vol[i], abs_mean[i]) for i in range(self.n_regimes)]
        # Sort by vol ascending, then by abs_mean descending
        stats.sort(key=lambda x: (x[1], -x[2]))
        
        mapping = {}
        # Lowest volatility -> QUIET
        mapping[stats[0][0]] = RegimeV2.QUIET
        # Highest volatility -> CRISIS
        mapping[stats[-1][0]] = RegimeV2.CRISIS
        
        # For the middle two, assign TRENDING if abs_mean higher, else VOLATILE
        middle = stats[1:-1]
        if len(middle) == 2:
            if middle[0][2] > middle[1][2]:
                mapping[middle[0][0]] = RegimeV2.TRENDING
                mapping[middle[1][0]] = RegimeV2.VOLATILE
            else:
                mapping[middle[0][0]] = RegimeV2.VOLATILE
                mapping[middle[1][0]] = RegimeV2.TRENDING
        elif len(middle) == 1:
            # Only one middle state, assign based on abs_mean
            if middle[0][2] > 0.001:  # arbitrary threshold
                mapping[middle[0][0]] = RegimeV2.TRENDING
            else:
                mapping[middle[0][0]] = RegimeV2.VOLATILE
        
        return mapping

    def fit(self, returns: pd.Series) -> None:
        """Fit HMM to returns series."""
        returns = returns.dropna()
        if len(returns) < 20:
            raise ValueError("Need at least 20 data points")
        X = returns.values.reshape(-1, 1)
        self.model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type=self.covariance_type,
            n_iter=self.n_iter,
            random_state=42
        )
        self.model.fit(X)
        self._fitted = True
        self._state_to_regime = self._map_states_to_regimes()

    def predict(self, returns: pd.Series) -> List[str]:
        """Predict regime labels for each time step."""
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        returns = returns.dropna()
        if len(returns) == 0:
            return []
        X = returns.values.reshape(-1, 1)
        states = self.model.predict(X)
        regimes = [self._state_to_regime[state].value for state in states]
        return regimes

    def predict_proba(self, returns: pd.Series) -> pd.DataFrame:
        """Predict regime probabilities for each time step."""
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        returns = returns.dropna()
        if len(returns) == 0:
            return pd.DataFrame()
        X = returns.values.reshape(-1, 1)
        proba = self.model.predict_proba(X)
        # Create DataFrame with regime columns
        regime_columns = [regime.value for regime in RegimeV2]
        # Reorder columns according to regimes
        col_order = [self._state_to_regime[i].value for i in range(self.n_regimes)]
        proba_df = pd.DataFrame(proba, columns=col_order)
        return proba_df

    def detect_change_point(self, returns: pd.Series, threshold: float = 0.3) -> List[int]:
        """Detect indices where regime change probability exceeds threshold."""
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        proba = self.predict_proba(returns)
        if proba.empty:
            return []
        # Compute max change in probability between consecutive steps
        diff = proba.diff().abs().max(axis=1)
        change_points = diff[diff > threshold].index.tolist()
        return change_points