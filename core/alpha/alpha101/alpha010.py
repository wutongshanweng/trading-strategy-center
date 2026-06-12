import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha010(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha010"

    @property
    def category(self) -> str:
        return "volume_rank"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['volume'].rolling(20).rank()