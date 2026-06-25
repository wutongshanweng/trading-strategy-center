"""GTJA Alpha33: ((((-1 * TSMIN(LOW, 5)) + DELAY(TSMIN(LOW, 5), 5)) * RANK(((SUM(RET, 240) - SUM("""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha33(AlphaFactor):
    """GTJA Alpha33: ((((-1 * TSMIN(LOW, 5)) + DELAY(TSMIN(LOW, 5), 5)) * RANK(((SUM(RET, 240) - SUM("""

    @property
    def name(self) -> str:
        return "gtja_alpha33"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((((-1 * TSMIN(LOW, 5)) + DELAY(TSMIN(LOW, 5), 5)) * RANK(((SUM(RET, 240) - SUM("

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((((-1 * TSMIN(LOW, 5)) + DELAY(TSMIN(LOW, 5), 5)) * RANK(((SUM(RET, 240) - SUM(RET, 20)) / 220))) * TSRANK(VOLUME, 5))"
        return evaluate_gtja(formula, data)
