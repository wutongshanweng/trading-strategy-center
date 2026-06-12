import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha043(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha043"

    @property
    def category(self) -> str:
        return "volume_volatility_rank"

    @property
    def description(self) -> str:
        return "Volume volatility rank factor - rolling rank of volume coefficient of variation over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vol_std = data["volume"].rolling(lookback).std()
        vol_mean = data["volume"].rolling(lookback).mean()
        return (vol_std / vol_mean).rank()
