from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from dataclasses import dataclass


@dataclass
class PairSignal:
    timestamp: pd.Timestamp
    action: str
    zscore: float
    spread: float


class PairTrader:
    def __init__(self, symbol_a: str, symbol_b: str):
        self.symbol_a, self.symbol_b = symbol_a, symbol_b
        self.hedge_ratio = self.intercept = self.adf_stat = self.pvalue = None

    def compute_cointegration(self, df_a, df_b):
        common = df_a.index.intersection(df_b.index)
        a = df_a.loc[common, "close"].values
        b = df_b.loc[common, "close"].values
        valid = ~(np.isnan(a) | np.isnan(b))
        a, b = a[valid], b[valid]
        if len(a) < 5:
            return {"adf_stat": np.nan, "pvalue": np.nan, "hedge_ratio": np.nan}
        model = sm.OLS(a, sm.add_constant(b)).fit()
        self.hedge_ratio, self.intercept = model.params[1], model.params[0]
        spread = a - self.hedge_ratio * b
        try:
            adf = adfuller(spread, autolag="AIC")
            self.adf_stat, self.pvalue = float(adf[0]), float(adf[1])
        except Exception:
            self.adf_stat = self.pvalue = np.nan
        return {"adf_stat": self.adf_stat, "pvalue": self.pvalue, "hedge_ratio": self.hedge_ratio}

    def generate_signals(self, df_a, df_b, entry_z=2.0):
        common = df_a.index.intersection(df_b.index)
        if self.hedge_ratio is None or len(common) == 0:
            return []
        a = df_a.loc[common, "close"].values
        b = df_b.loc[common, "close"].values
        valid = ~(np.isnan(a) | np.isnan(b))
        a, b, idx = a[valid], b[valid], common[valid]
        spread = a - self.hedge_ratio * b
        zs = (spread - np.mean(spread)) / (np.std(spread) + 1e-10)
        signals, pos = [], 0
        for i in range(len(zs)):
            z = zs[i]
            if np.isnan(z):
                continue
            if pos == 0:
                if z < -entry_z:
                    signals.append(PairSignal(idx[i], "long", z, spread[i])); pos = 1
                elif z > entry_z:
                    signals.append(PairSignal(idx[i], "short", z, spread[i])); pos = -1
            elif (pos == 1 and z > -0.5) or (pos == -1 and z < 0.5):
                signals.append(PairSignal(idx[i], "exit", z, spread[i])); pos = 0
        return signals
