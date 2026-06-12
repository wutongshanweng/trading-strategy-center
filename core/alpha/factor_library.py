from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
from loguru import logger


@dataclass
class FactorMetadata:
    name: str
    category: str
    description: str
    compute_fn: Callable[..., pd.Series]
    params: Dict[str, Any] = field(default_factory=dict)


class FactorLibrary:
    def __init__(self) -> None:
        self._factors: Dict[str, FactorMetadata] = {}

    def register(
        self,
        name: str,
        compute_fn: Callable[..., pd.Series],
        category: str = "custom",
        description: str = "",
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        if name in self._factors:
            logger.warning(f"Overwriting existing factor: {name}")
        self._factors[name] = FactorMetadata(
            name=name,
            category=category,
            description=description,
            compute_fn=compute_fn,
            params=params or {},
        )
        logger.info(f"Registered factor: {name} (category={category})")

    def get_factor(self, name: str) -> FactorMetadata:
        if name not in self._factors:
            raise KeyError(f"Factor '{name}' not found in library")
        return self._factors[name]

    def list_factors(self, category: Optional[str] = None) -> List[str]:
        if category is None:
            return list(self._factors.keys())
        return [
            name
            for name, meta in self._factors.items()
            if meta.category == category
        ]

    def compute_all(
        self,
        data: pd.DataFrame,
        factors: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        factor_names = factors if factors else self.list_factors()
        results = {}
        for name in factor_names:
            meta = self.get_factor(name)
            try:
                results[name] = meta.compute_fn(data, **meta.params)
            except Exception as e:
                logger.error(f"Failed to compute factor '{name}': {e}")
                results[name] = pd.Series(
                    index=data.index, dtype=float
                )
        return pd.DataFrame(results, index=data.index)

    def remove_factor(self, name: str) -> bool:
        if name in self._factors:
            del self._factors[name]
            logger.info(f"Removed factor: {name}")
            return True
        return False

    def get_categories(self) -> List[str]:
        return list(
            set(meta.category for meta in self._factors.values())
        )
