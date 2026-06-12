import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha001(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha001"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Price momentum factor - close/open ratio over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data["close"].pct_change(lookback)
