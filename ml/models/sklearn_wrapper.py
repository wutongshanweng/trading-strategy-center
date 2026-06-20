"""
通用 sklearn 模型包装器 — 替代 N-BEATS/TFT 伪实现, 提供可直接用的真模型。

支持: rf / xgb / lgbm / ridge / svr / mlp (缺库自动回退 rf)。

用法:
    model = SklearnModel("lgbm", {"n_estimators": 100, "max_depth": 6})
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd
from loguru import logger


class SklearnModel:
    """通用 sklearn 模型包装器。"""

    def __init__(self, model_type: str = "lgbm", params: Optional[Dict] = None):
        self.model_type = model_type
        self.params = params or {}
        self._model = None
        self._build()

    def _build(self):
        p = self.params
        if self.model_type == "rf":
            from sklearn.ensemble import RandomForestRegressor
            self._model = RandomForestRegressor(
                n_estimators=p.get("n_estimators", 100),
                max_depth=p.get("max_depth", 10),
                min_samples_leaf=p.get("min_samples_leaf", 5),
                random_state=42, n_jobs=-1)
        elif self.model_type == "xgb":
            try:
                from xgboost import XGBRegressor
                self._model = XGBRegressor(
                    n_estimators=p.get("n_estimators", 100),
                    max_depth=p.get("max_depth", 6),
                    learning_rate=p.get("learning_rate", 0.1),
                    subsample=p.get("subsample", 0.8),
                    random_state=42, n_jobs=-1)
            except ImportError:
                logger.warning("xgboost not installed, falling back to rf")
                self._build_rf_fallback()
        elif self.model_type == "lgbm":
            try:
                import lightgbm as lgb
                self._model = lgb.LGBMRegressor(
                    n_estimators=p.get("n_estimators", 100),
                    max_depth=p.get("max_depth", 6),
                    learning_rate=p.get("learning_rate", 0.1),
                    subsample=p.get("subsample", 0.8),
                    random_state=42, n_jobs=-1, verbose=-1)
            except ImportError:
                logger.warning("lightgbm not installed, falling back to rf")
                self._build_rf_fallback()
        elif self.model_type == "ridge":
            from sklearn.linear_model import Ridge
            self._model = Ridge(alpha=p.get("alpha", 1.0))
        elif self.model_type == "svr":
            from sklearn.svm import SVR
            self._model = SVR(kernel=p.get("kernel", "rbf"), C=p.get("C", 1.0))
        elif self.model_type == "mlp":
            from sklearn.neural_network import MLPRegressor
            self._model = MLPRegressor(
                hidden_layer_sizes=p.get("hidden_layers", (64, 32)),
                learning_rate_init=p.get("lr", 0.001),
                max_iter=p.get("max_iter", 200), random_state=42)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def _build_rf_fallback(self):
        from sklearn.ensemble import RandomForestRegressor
        self._model = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        self.model_type = "rf"

    def fit(self, X, y):
        if self._model is None:
            raise RuntimeError("Model not built")
        self._model.fit(X, y)
        logger.info(f"{self.model_type} trained")
        return self

    def predict(self, X) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Model not built")
        return self._model.predict(X)

    def get_params(self) -> Dict:
        return self._model.get_params() if self._model else {}

    def feature_importance(self) -> Optional[pd.Series]:
        """获取特征重要性 (树模型)。"""
        if hasattr(self._model, "feature_importances_"):
            imp = self._model.feature_importances_
            return pd.Series(imp, index=[f"f{i}" for i in range(len(imp))]
                             ).sort_values(ascending=False)
        return None
