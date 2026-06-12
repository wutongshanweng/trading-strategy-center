import numpy as np
import pandas as pd


class MarketDepthAnalyzer:
    def __init__(self):
        self.estimated_spread_value = None

    def estimate_spread(self, df: pd.DataFrame) -> float:
        if df is None or len(df) < 2:
            return np.nan
        if "high" in df.columns and "low" in df.columns:
            s = float((df["high"] - df["low"]).mean())
        elif "ask" in df.columns and "bid" in df.columns:
            s = float((df["ask"] - df["bid"]).mean())
        elif "close" in df.columns:
            s = float((df["close"].rolling(20).max() - df["close"].rolling(20).min()).mean())
        else:
            return np.nan
        self.estimated_spread_value = s
        return s

    def impact_cost(self, volume: float) -> float:
        if volume <= 0:
            return 0.0
        s = self.estimated_spread_value or 0.001
        return float(s + 0.5 * s * np.sqrt(volume / 1000.0))
