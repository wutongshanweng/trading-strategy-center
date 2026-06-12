import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha004(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha004"

    @property
    def category(self) -> str:
        return "price_position"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        return (data['close'] - data['low']) / (data['high'] - data['low'])