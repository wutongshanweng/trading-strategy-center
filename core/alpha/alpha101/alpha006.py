import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha006(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha006"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Volume-weighted average price ratio - close relative to VWAP"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data['close'] * data['volume']).rolling(lookback).sum() / data['volume'].rolling(lookback).sum()
        return data['close'] / vwap