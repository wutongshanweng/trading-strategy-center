import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha031(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha031"

    @property
    def category(self) -> str:
        return "return_rank"

    @property
    def description(self) -> str:
        return "Return rank factor - rolling rank of returns over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data["close"].pct_change().rolling(lookback).rank()
