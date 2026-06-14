"""Value at Risk (VaR) calculator."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


class VaRCalculator:
    """Calculate VaR using historical, parametric, or Monte Carlo methods."""

    def __init__(self, confidence: float = 0.95):
        self.confidence = confidence

    def historical(self, returns: pd.Series, period: int = 1) -> float:
        """Historical simulation VaR."""
        sorted_r = np.sort(returns.dropna().values)
        cutoff = int((1 - self.confidence) * len(sorted_r))
        if cutoff < 1:
            cutoff = 1
        return float(-sorted_r[cutoff - 1] * np.sqrt(period))

    def parametric(self, returns: pd.Series, period: int = 1) -> float:
        """Parametric (variance-covariance) VaR assuming normal distribution."""
        mu = returns.mean()
        sigma = returns.std()
        z = stats.norm.ppf(self.confidence)
        return float(-(mu - z * sigma) * np.sqrt(period))

    def monte_carlo(self, returns: pd.Series, period: int = 1, n_sims: int = 10000) -> float:
        """Monte Carlo simulation VaR."""
        mu = returns.mean()
        sigma = returns.std()
        sims = np.random.normal(mu, sigma, (n_sims, period))
        portfolio_returns = sims.sum(axis=1)
        cutoff = int((1 - self.confidence) * n_sims)
        return float(-np.percentile(portfolio_returns, (1 - self.confidence) * 100))
