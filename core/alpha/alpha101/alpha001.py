import pandas as pd

from .base import AlphaBase


class Alpha001(AlphaBase):
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
