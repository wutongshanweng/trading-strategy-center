from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class FactorReport:
    factor_name: str
    ic_mean: float
    ic_std: float
    ir: float
    turnover: float
    ic_series: Optional[pd.Series] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class FactorEvaluator:
    def __init__(
        self,
        forward_returns: Optional[pd.Series] = None,
        periods: int = 1,
    ) -> None:
        self.forward_returns = forward_returns
        self.periods = periods

    def set_forward_returns(self, returns: pd.Series) -> None:
        self.forward_returns = returns

    def calculate_ic(
        self,
        factor_values: pd.Series,
        method: str = "pearson",
    ) -> pd.Series:
        if self.forward_returns is None:
            raise ValueError("Forward returns not set")

        aligned = pd.concat(
            [factor_values, self.forward_returns], axis=1
        ).dropna()
        if aligned.empty or len(aligned) < 3:
            return pd.Series(dtype=float)

        aligned.columns = ["factor", "returns"]
        ic = aligned["factor"].corr(aligned["returns"], method=method)
        return pd.Series([ic], index=[0])

    def calculate_ir(
        self,
        factor_values: pd.Series,
        method: str = "pearson",
    ) -> float:
        ic_series = self.calculate_ic(factor_values, method)
        if ic_series.empty:
            return 0.0
        ic_mean = ic_series.mean()
        ic_std = ic_series.std()
        if ic_std == 0:
            return 0.0
        return ic_mean / ic_std

    def calculate_turnover(
        self,
        factor_values: pd.Series,
        quantile: float = 0.2,
    ) -> float:
        if factor_values.empty:
            return 0.0

        threshold = factor_values.quantile(1 - quantile)
        long_mask = factor_values >= threshold

        prev_indices = set()
        turnovers = []

        for i in range(len(long_mask)):
            curr_indices = (
                set(factor_values.index[:i + 1][long_mask.iloc[:i + 1]])
                if i == 0
                else set()
            )
            if long_mask.iloc[i]:
                curr_indices = {factor_values.index[i]}

            if curr_indices and prev_indices:
                turnover = 1 - len(prev_indices & curr_indices) / max(
                    len(curr_indices), 1
                )
                turnovers.append(turnover)

            if long_mask.iloc[i]:
                prev_indices = {factor_values.index[i]}

        return float(np.mean(turnovers)) if turnovers else 0.0

    def generate_report(
        self,
        factor_name: str,
        factor_values: pd.Series,
    ) -> FactorReport:
        ic_series = self.calculate_ic(factor_values)
        ic_mean = float(ic_series.mean()) if not ic_series.empty else 0.0
        ic_std = float(ic_series.std()) if not ic_series.empty else 0.0
        ir = self.calculate_ir(factor_values)
        turnover = self.calculate_turnover(factor_values)

        return FactorReport(
            factor_name=factor_name,
            ic_mean=ic_mean,
            ic_std=ic_std,
            ir=ir,
            turnover=turnover,
            ic_series=ic_series,
            metadata={
                "periods": self.periods,
                "n_observations": len(factor_values.dropna()),
            },
        )
