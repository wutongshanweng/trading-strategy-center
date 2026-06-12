import numpy as np
from typing import Dict, Any
from .. import QuantModel


class HurstExponentModel(QuantModel):
    name = "HurstExponent"

    def __init__(self):
        self.hurst = None
        self._fitted = False

    def fit(self, df, **kwargs):
        close = df['close'].dropna().values
        if len(close) < 100:
            raise ValueError("Need at least 100 data points")
        self.hurst = self._compute_hurst(close)
        self._fitted = True

    def _compute_hurst(self, prices):
        log_returns = np.diff(np.log(prices))
        max_lag = min(len(log_returns) // 2, 100)
        if max_lag < 2:
            return 0.5
        lags = np.arange(2, max_lag + 1)
        rs_values = []
        for lag in lags:
            n_seg = len(log_returns) // lag
            if n_seg < 1:
                continue
            rs = []
            for j in range(n_seg):
                seg = log_returns[j * lag:(j + 1) * lag]
                mean_adj = seg - seg.mean()
                cum_dev = np.cumsum(mean_adj)
                S = seg.std(ddof=1)
                if S > 1e-12:
                    rs.append((cum_dev.max() - cum_dev.min()) / S)
            if rs:
                rs_values.append(np.mean(rs))
        if len(rs_values) < 2:
            return 0.5
        coeffs = np.polyfit(np.log2(lags[:len(rs_values)]), np.log2(rs_values), 1)
        return float(coeffs[0])

    def predict(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        return np.array([self.hurst])

    def classify(self) -> str:
        if self.hurst is None:
            return "unknown"
        if self.hurst < 0.45:
            return "mean_reverting"
        if self.hurst > 0.55:
            return "trending"
        return "random_walk"

    def get_params(self) -> Dict[str, Any]:
        return {"hurst": self.hurst, "classification": self.classify()}
