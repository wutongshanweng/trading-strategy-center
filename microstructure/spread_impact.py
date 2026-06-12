import numpy as np
import pandas as pd


class SpreadImpactAnalyzer:
    def __init__(self):
        self.effective = self.realized = None

    def effective_spread(self, df: pd.DataFrame) -> float:
        if df is None or len(df) < 2:
            return np.nan
        eff = 2 * np.abs(df["close"].diff()).dropna()
        self.effective = eff
        return float(eff.mean())

    def realized_spread(self, df: pd.DataFrame) -> float:
        if df is None or len(df) < 6:
            return np.nan
        mid = df["close"]
        direction = np.sign(mid.diff()).replace(0, 1)
        real = (2 * direction * (mid - mid.shift(-5))).abs().dropna()
        self.realized = real
        return float(real.mean())

    def adverse_selection(self):
        if self.effective is None or self.realized is None:
            return np.nan
        common = self.effective.dropna().index.intersection(self.realized.dropna().index)
        return float((self.effective[common] - self.realized[common]).mean()) if len(common) > 0 else np.nan
