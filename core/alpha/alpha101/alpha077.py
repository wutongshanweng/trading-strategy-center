import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha077(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha077"

    @property
    def category(self) -> str:
        return "volatility_rank"

    @property
    def description(self) -> str:
        return "Volatility rank factor - rolling rank of return volatility over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data["close"].pct_change().rolling(lookback).std().rank()
