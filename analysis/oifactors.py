from typing import Dict, List
import numpy as np
import pandas as pd


class OIAnalyzer:
    def __init__(self):
        self.result = None

    def analyze(self, df: pd.DataFrame) -> Dict:
        if df is None or len(df) < 2 or "oi" not in df.columns or "close" not in df.columns:
            return {}
        df = df.copy()
        df["oi_change"] = df["oi"].diff()
        df["price_change"] = df["close"].diff()
        total = max(len(df) - 1, 1)
        return {
            "trend_strong_ratio": float(((df["oi_change"] > 0) & (df["price_change"] > 0)).sum() / total),
            "reversal_ratio": float(((df["oi_change"] > 0) & (df["price_change"] < 0)).sum() / total),
            "oi_price_corr": float(df["oi"].corr(df["close"])),
        }

    def detect_divergence(self) -> List[str]:
        return [f"divergence_at_{i}" for i in range(1, len(self.result)) if self.result is not None
                and self.result["oi_change"].iloc[i] > 0 and self.result["price_change"].iloc[i] < 0]
