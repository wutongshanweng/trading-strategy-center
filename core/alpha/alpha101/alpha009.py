import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha009(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha009"

    @property
    def category(self) -> str:
        return "momentum"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'] / data['close'].shift(5)