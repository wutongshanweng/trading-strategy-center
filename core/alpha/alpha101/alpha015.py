import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha015(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha015"

    @property
    def category(self) -> str:
        return "volume_volatility"

    @property
    def description(self) -> str:
        return "Volume volatility factor - coefficient of variation of volume over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        volume = data['volume']
        rolling_std = volume.rolling(lookback).std()
        rolling_mean = volume.rolling(lookback).mean()
        return rolling_std / rolling_mean