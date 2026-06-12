from typing import Dict
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


class FactorEvaluator:
    def compute_ic(self, factor_values: pd.Series, forward_returns: pd.Series):
        if factor_values is None or forward_returns is None:
            return np.nan
        fv, fr = factor_values.dropna().align(forward_returns.dropna(), join="inner")
        if len(fv) < 3:
            return np.nan
        corr, _ = spearmanr(fv.values, fr.values)
        return float(corr) if not np.isnan(corr) else np.nan

    def turnover(self, factor_values: pd.Series):
        if factor_values is None or len(factor_values) < 2:
            return np.nan
        if isinstance(factor_values, pd.DataFrame):
            return float(factor_values.rank(axis=1).diff().abs().fillna(0).values.mean())
        return 0.0

    def factor_decay(self, factor_values: pd.Series, forward_returns: pd.Series, lags=None):
        lags = lags or [1, 5, 10]
        return {f"lag_{lag}": self.compute_ic(factor_values, forward_returns.shift(-lag)) for lag in lags}
