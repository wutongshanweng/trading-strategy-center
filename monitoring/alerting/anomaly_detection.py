"""Anomaly detection: zscore, IQR."""

from __future__ import annotations

from typing import List

import numpy as np


class AnomalyDetection:
    """Detect anomalies in metric time series."""

    def __init__(self, method: str = "zscore", threshold: float = 3.0):
        self.method = method
        self.threshold = threshold

    def detect(self, data: np.ndarray) -> List[int]:
        if self.method == "zscore":
            return self._zscore(data)
        if self.method == "iqr":
            return self._iqr(data)
        return []

    def _zscore(self, data: np.ndarray) -> List[int]:
        mu, sig = np.mean(data), np.std(data)
        if sig == 0:
            return []
        z = np.abs((data - mu) / sig)
        return np.where(z > self.threshold)[0].tolist()

    def _iqr(self, data: np.ndarray) -> List[int]:
        q1, q3 = np.percentile(data, [25, 75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        return np.where((data < lo) | (data > hi))[0].tolist()
