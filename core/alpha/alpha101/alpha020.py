import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha020(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha020"

    @property
    def category(self) -> str:
        return "volume_price_rank"

    @property
    def description(self) -> str:
        return "Volume-price rank factor - rolling rank of price-volume product over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        price_volume = data['close'] * data['volume']
        return price_volume.rolling(lookback).rank()