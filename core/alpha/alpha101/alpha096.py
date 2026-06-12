import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha096(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha096"

    @property
    def category(self) -> str:
        return "correlation_rank"

    @property
    def description(self) -> str:
        return "Correlation rank factor - rolling rank of return autocorrelation over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        return returns.rolling(lookback).corr(returns.shift(1)).rank()
