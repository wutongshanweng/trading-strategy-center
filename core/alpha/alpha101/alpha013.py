import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha013(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha013"

    @property
    def category(self) -> str:
        return "acceleration"

    @property
    def description(self) -> str:
        return "Acceleration factor - second derivative of close price"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data['close'].pct_change().diff()