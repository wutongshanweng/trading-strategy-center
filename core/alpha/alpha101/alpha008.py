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

    @property
    def description(self) -> str:
        return "Risk-return ratio - rolling Sharpe-like ratio of returns"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data['close'].pct_change()
        return returns.rolling(lookback).mean() / returns.rolling(lookback).std()