import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha029(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha029"

    @property
    def category(self) -> str:
        return "volume_volatility_rank"

    @property
    def description(self) -> str:
        return "Volume volatility rank factor - rolling rank of volume coefficient of variation over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        volume = data['volume']
        rolling_std = volume.rolling(lookback).std()
        rolling_mean = volume.rolling(lookback).mean()
        volume_volatility = rolling_std / rolling_mean
        return volume_volatility.rank()