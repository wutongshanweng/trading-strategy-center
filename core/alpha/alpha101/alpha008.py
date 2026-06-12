import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha008(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha008"

    @property
    def category(self) -> str:
        return "risk_return"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        return returns.rolling(20).mean() / returns.rolling(20).std()