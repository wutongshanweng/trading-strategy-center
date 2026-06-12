from __future__ import annotations

from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd
from loguru import logger


class FactorCombiner:
    def __init__(self, factors: Optional[pd.DataFrame] = None) -> None:
        self.factors = factors

    def set_factors(self, factors: pd.DataFrame) -> None:
        self.factors = factors

    def equal_weight(
        self,
        factors: Optional[pd.DataFrame] = None,
    ) -> pd.Series:
        df = factors if factors is not None else self.factors
        if df is None or df.empty:
            return pd.Series(dtype=float)
        return df.mean(axis=1)

    def ic_weight(
        self,
        factors: Optional[pd.DataFrame] = None,
        ic_values: Optional[Dict[str, float]] = None,
    ) -> pd.Series:
        df = factors if factors is not None else self.factors
        if df is None or df.empty:
            return pd.Series(dtype=float)

        if ic_values is None:
            ic_values = {}

        weights = {}
        for col in df.columns:
            ic = ic_values.get(col, 0.0)
            weights[col] = abs(ic)

        total_weight = sum(weights.values())
        if total_weight == 0:
            return self.equal_weight(df)

        normalized = {k: v / total_weight for k, v in weights.items()}
        result = sum(
            df[col] * w for col, w in normalized.items() if col in df.columns
        )
        return result

    def regime_weight(
        self,
        factors: Optional[pd.DataFrame] = None,
        regimes: Optional[pd.Series] = None,
        regime_weights: Optional[Dict[Union[str, int], Dict[str, float]]] = None,
    ) -> pd.Series:
        df = factors if factors is not None else self.factors
        if df is None or df.empty:
            return pd.Series(dtype=float)

        if regimes is None:
            regimes = pd.Series(0, index=df.index)

        if regime_weights is None:
            regime_weights = {}

        result = pd.Series(0.0, index=df.index)
        for regime in regimes.unique():
            mask = regimes == regime
            regime_data = df[mask]
            if regime_data.empty:
                continue

            weights = regime_weights.get(regime, {})
            if not weights:
                regime_result = regime_data.mean(axis=1)
            else:
                total_weight = sum(abs(w) for w in weights.values())
                if total_weight == 0:
                    regime_result = regime_data.mean(axis=1)
                else:
                    normalized = {
                        k: abs(w) / total_weight for k, w in weights.items()
                    }
                    regime_result = sum(
                        regime_data[col] * w
                        for col, w in normalized.items()
                        if col in regime_data.columns
                    )

            result[mask] = regime_result

        return result

    def normalize_factors(
        self,
        factors: Optional[pd.DataFrame] = None,
        method: str = "zscore",
    ) -> pd.DataFrame:
        df = factors if factors is not None else self.factors
        if df is None or df.empty:
            return pd.DataFrame()

        if method == "zscore":
            return (df - df.mean()) / (df.std() + 1e-10)
        elif method == "minmax":
            min_vals = df.min()
            max_vals = df.max()
            return (df - min_vals) / (max_vals - min_vals + 1e-10)
        elif method == "rank":
            return df.rank(pct=True)
        else:
            raise ValueError(f"Unknown normalization method: {method}")
