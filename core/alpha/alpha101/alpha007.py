import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha007(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha007"

    @property
    def category(self) -> str:
        return "correlation"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].rolling(20).corr(data['volume'])