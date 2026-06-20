"""
模型集成 — 组合多个模型提升预测稳定性。

方法: voting (加权平均) / stacking (元模型组合) / blending。

用法:
    ens = ModelEnsemble("voting")
    ens.add_model(m1, weight=0.6)
    ens.add_model(m2, weight=0.4)
    pred = ens.predict(X)
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

import numpy as np
from loguru import logger


class ModelEnsemble:
    """模型集成 (voting / stacking / blending)。"""

    def __init__(self, method: str = "voting"):
        self.method = method
        self.models: List[Tuple[Any, float]] = []
        self.meta_model: Optional[Any] = None
        self._fitted = False

    def add_model(self, model: Any, weight: float = 1.0):
        """添加一个基模型。"""
        self.models.append((model, weight))
        logger.debug(f"Added model: {type(model).__name__} (weight={weight})")

    def fit(self, X, y):
        """训练集成 (仅 stacking 需训练元模型)。"""
        if self.method == "stacking":
            self._fit_stacking(X, y)
        self._fitted = True
        return self

    def _fit_stacking(self, X, y):
        if len(self.models) < 2:
            logger.warning("Stacking needs >=2 base models, falling back to voting")
            self.method = "voting"
            return
        meta_features = np.column_stack([m.predict(X) for m, _ in self.models])
        from sklearn.linear_model import LinearRegression
        self.meta_model = LinearRegression()
        self.meta_model.fit(meta_features, y)
        logger.info(f"Stacking meta-model trained: weights={self.meta_model.coef_}")

    def predict(self, X) -> np.ndarray:
        """预测。"""
        if not self.models:
            raise ValueError("No models in ensemble")
        predictions = np.column_stack([m.predict(X) for m, _ in self.models])

        if self.method == "voting":
            weights = np.array([w for _, w in self.models], dtype=float)
            weights = weights / weights.sum()
            return predictions @ weights
        if self.method == "stacking" and self.meta_model is not None:
            return self.meta_model.predict(predictions)
        # blending 简化版 / 兜底: 等权平均
        return predictions.mean(axis=1)

    @property
    def weights_info(self) -> str:
        return " | ".join(f"{type(m).__name__}:{w:.2f}" for m, w in self.models)
