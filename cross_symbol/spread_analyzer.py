import numpy as np
import pandas as pd
import statsmodels.api as sm


def compute_spread(price_a: pd.Series, price_b: pd.Series, method: str = "ratio") -> pd.Series:
    if method == "ratio":
        return price_a / price_b
    return price_a - price_b


def zscore(spread: pd.Series) -> pd.Series:
    mean, std = np.nanmean(spread), np.nanstd(spread)
    if std == 0 or np.isnan(std):
        return pd.Series(np.zeros_like(spread), index=spread.index)
    return (spread - mean) / std


def half_life(spread: pd.Series) -> float:
    vals = spread.dropna().values
    if len(vals) < 2:
        return np.nan
    X = sm.add_constant(vals[:-1])
    try:
        beta = sm.OLS(vals[1:], X).fit().params[1]
        return -np.log(2) / np.log(beta) if 0 < beta < 1 else np.nan
    except Exception:
        return np.nan


def generate_signals(spread: pd.Series, entry_z: float = 2.0, exit_z: float = 0.5) -> pd.Series:
    zs = zscore(spread)
    signals = pd.Series(0, index=zs.index)
    pos = 0
    for i in range(len(zs)):
        z = zs.iloc[i]
        if np.isnan(z):
            continue
        if pos == 0:
            if z < -entry_z:
                signals.iloc[i], pos = 1, 1
            elif z > entry_z:
                signals.iloc[i], pos = -1, -1
        elif pos == 1:
            signals.iloc[i] = 1 if z <= -exit_z else 0
            if z > -exit_z:
                pos = 0
        elif pos == -1:
            signals.iloc[i] = -1 if z >= exit_z else 0
            if z < exit_z:
                pos = 0
    return signals
