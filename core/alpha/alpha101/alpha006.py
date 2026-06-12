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

    def compute(self, data: pd.DataFrame) -> pd.Series:
        vwap = (data['close'] * data['volume']).rolling(20).sum() / data['volume'].rolling(20).sum()
        return data['close'] / vwap