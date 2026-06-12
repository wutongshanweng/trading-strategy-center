import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha025(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha025"

    @property
    def category(self) -> str:
        return "volume_momentum_rank"

    @property
    def description(self) -> str:
        return "Volume momentum rank factor - rolling rank of 5-period volume momentum over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        volume_momentum = data['volume'] / data['volume'].shift(5)
        return volume_momentum.rolling(lookback).rank()