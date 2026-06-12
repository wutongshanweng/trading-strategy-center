from typing import Dict
import numpy as np
import pandas as pd


class SeasonalityAnalyzer:
    def __init__(self):
        self.dow_effects = self.month_effects = {}

    def day_of_week_effect(self, df: pd.DataFrame) -> Dict[str, float]:
        returns = (df["returns"] if "returns" in df.columns else df["close"].pct_change()).dropna()
        return {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d]: float(returns[returns.index.dayofweek == d].mean())
                for d in range(7) if (returns.index.dayofweek == d).any()}

    def month_effect(self, df: pd.DataFrame) -> Dict[str, float]:
        returns = (df["returns"] if "returns" in df.columns else df["close"].pct_change()).dropna()
        names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return {names[m - 1]: float(returns[returns.index.month == m].mean()) for m in range(1, 13) if (returns.index.month == m).any()}

    def get_seasonal_adjustment(self, dt) -> float:
        ts = pd.Timestamp(dt)
        names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        dows = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        mon_adj = self.month_effects.get(names[ts.month - 1], 0.0)
        dow_adj = self.dow_effects.get(dows[ts.dayofweek], 0.0)
        all_vals = list(self.month_effects.values()) + list(self.dow_effects.values())
        return float(mon_adj + dow_adj - (np.mean(all_vals) if all_vals else 0.0))
