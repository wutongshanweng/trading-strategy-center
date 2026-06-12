import pandas as pd

from .base import AlphaBase


class Alpha002(AlphaBase):
    @property
    def name(self) -> str:
        return "alpha002"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Volume-price correlation factor - rolling correlation between price changes and volume"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        vol_ma = data["volume"].rolling(lookback).mean()
        return returns.rolling(lookback).corr(vol_ma)
