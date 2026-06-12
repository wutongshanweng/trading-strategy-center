import pandas as pd

from .base import AlphaBase


class Alpha003(AlphaBase):
    @property
    def name(self) -> str:
        return "alpha003"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Open-volume correlation factor - correlation between open price and volume"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data["open"].rolling(lookback).corr(data["volume"])
