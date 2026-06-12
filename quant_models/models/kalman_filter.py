import numpy as np
from typing import Dict, Any
from pykalman import KalmanFilter as PyKalman
from .. import QuantModel


class KalmanFilterModel(QuantModel):
    name = "KalmanFilter"

    def __init__(self, obs_cov: float = 1.0, trans_cov: float = 0.01):
        self.obs_cov = obs_cov
        self.trans_cov = trans_cov
        self._filtered_states = None
        self._fitted = False

    def fit(self, df, **kwargs):
        close = df['close'].dropna().values
        if len(close) < 5:
            raise ValueError("Need at least 5 data points")
        kf = PyKalman(n_dim_obs=1, n_dim_state=2,
                      initial_state_mean=np.array([close[0], 0.0]),
                      initial_state_covariance=np.eye(2) * 100.0,
                      transition_matrices=np.array([[1, 1], [0, 1]]),
                      observation_matrices=np.array([[1, 0]]),
                      observation_covariance=self.obs_cov,
                      transition_covariance=np.eye(2) * self.trans_cov)
        self._filtered_states, _ = kf.filter(close)
        self._fitted = True

    def predict(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        close = df['close'].dropna().values
        if len(close) == 0:
            return np.array([], dtype=float)
        n = min(len(close), len(self._filtered_states))
        return self._filtered_states[:n, 0]

    def get_params(self) -> Dict[str, Any]:
        if not self._fitted:
            return {"obs_cov": self.obs_cov, "trans_cov": self.trans_cov}
        return {"obs_cov": self.obs_cov, "trans_cov": self.trans_cov,
                "final_level": float(self._filtered_states[-1, 0]),
                "final_slope": float(self._filtered_states[-1, 1])}
