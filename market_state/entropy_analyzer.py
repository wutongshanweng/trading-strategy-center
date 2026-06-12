from typing import Dict
import pandas as pd
import numpy as np


class EntropyAnalyzer:
    def compute_entropy(self, series: pd.Series, bins: int = 50) -> float:
        series = series.dropna()
        if len(series) < 2:
            return 0.0
        returns = series.pct_change().dropna()
        if len(returns) < 2:
            return 0.0
        counts, _ = np.histogram(returns, bins=bins)
        probs = counts / counts.sum()
        probs = probs[probs > 0]
        if len(probs) == 0:
            return 0.0
        H = -np.sum(probs * np.log2(probs))
        max_H = np.log2(bins)
        return float(H / max_H) if max_H > 0 else 0.0

    def approximate_entropy(self, series: pd.Series, m: int = 2, r_factor: float = 0.2) -> float:
        series = series.dropna()
        if len(series) < m + 2:
            return 0.0
        std = series.std()
        if std == 0 or pd.isna(std):
            return 0.0
        r = r_factor * std
        data = series.values

        def _phi(length: int) -> float:
            n = len(data) - length + 1
            if n < 1:
                return 0.0
            templates = np.array([data[i:i + length] for i in range(n)])
            count = np.sum(np.max(np.abs(templates[:, np.newaxis] - templates), axis=2) < r, axis=1)
            C = count / n
            C = C[C > 0]
            return float(np.mean(np.log(C))) if len(C) > 0 else 0.0

        phi_m = _phi(m)
        phi_m1 = _phi(m + 1)
        return phi_m - phi_m1

    def compute_market_efficiency(self, df: pd.DataFrame, column: str = "close") -> Dict:
        if df.empty or column not in df:
            return {"shannon_entropy": 0.0, "approximate_entropy": 0.0, "efficiency_ratio": 0.0}
        series = df[column].dropna()
        if len(series) < 10:
            return {"shannon_entropy": 0.0, "approximate_entropy": 0.0, "efficiency_ratio": 0.0}
        shannon = self.compute_entropy(series)
        ap_en = self.approximate_entropy(series)
        changes = series.diff().dropna()
        abs_changes = changes.abs().sum()
        net_change = series.iloc[-1] - series.iloc[0]
        er = abs(net_change) / abs_changes if abs_changes > 0 else 0.0
        return {"shannon_entropy": round(shannon, 6), "approximate_entropy": round(ap_en, 6),
                "efficiency_ratio": round(er, 6)}
