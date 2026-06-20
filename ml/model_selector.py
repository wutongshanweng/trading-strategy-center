"""
自动模型选择器 — 从多个候选模型中按验证集表现选最优。

复用 Phase3 的 SklearnModel / HyperoptSearcher。
评估指标 IC (预测与实际的相关系数), 带复杂度惩罚防过拟合。

用法:
    selector = ModelSelector()
    name, score = selector.select({"rf": m1, "lgbm": m2}, X_val, y_val)
    # 或一步搜参+选优:
    best = selector.select_with_hyperopt(["rf","lgbm"], X_tr, y_tr, X_val, y_val)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
from loguru import logger


def _ic(pred: np.ndarray, actual: np.ndarray) -> float:
    """信息系数 = 预测与实际的皮尔逊相关; 样本不足或常量返回 0。"""
    if len(pred) < 3 or np.std(pred) == 0 or np.std(actual) == 0:
        return 0.0
    c = float(np.corrcoef(pred, actual)[0, 1])
    return c if np.isfinite(c) else 0.0


class ModelSelector:
    """自动模型选择器。"""

    def __init__(self, complexity_penalty: float = 0.0):
        """complexity_penalty: 每个候选按相对复杂度扣分 (0=不惩罚)。"""
        self.complexity_penalty = complexity_penalty

    def score_model(self, model, X_val, y_val) -> float:
        """单模型验证集 IC。"""
        try:
            pred = np.asarray(model.predict(X_val)).ravel()
            return _ic(pred, np.asarray(y_val).ravel())
        except Exception as e:  # noqa: BLE001
            logger.warning(f"模型评分失败: {e}")
            return -np.inf

    def select(
        self, models: Dict[str, object], X_val, y_val, metric: str = "ic",
    ) -> Tuple[str, float]:
        """从多个已训练模型中选最佳, 返回 (name, score)。"""
        if not models:
            raise ValueError("models 不能为空")
        scored = {name: self.score_model(m, X_val, y_val) for name, m in models.items()}
        best = max(scored, key=scored.get)
        logger.info(f"模型选择: {scored} → {best}")
        return best, scored[best]

    def select_with_hyperopt(
        self,
        candidate_types: List[str],
        X_train, y_train, X_val, y_val,
        n_trials: int = 10,
        search_method: str = "random",
    ) -> Tuple[str, object, float, dict]:
        """对每个候选类型搜参+训练, 选验证集 IC 最佳。

        返回 (model_type, fitted_model, score, best_params)。
        """
        from ml.models.sklearn_wrapper import SklearnModel
        from ml.hyperopt import HyperoptSearcher

        # 各模型类型的搜索空间 (无空间的用默认参数直接训)
        spaces = {
            "rf": {"n_estimators": (30, 200, "int"), "max_depth": (3, 15, "int")},
            "xgb": {"n_estimators": (30, 200, "int"), "max_depth": (3, 10, "int"),
                    "learning_rate": (0.01, 0.3, "float")},
            "lgbm": {"n_estimators": (30, 200, "int"), "max_depth": (3, 10, "int"),
                     "learning_rate": (0.01, 0.3, "float")},
            "ridge": {"alpha": (0.1, 10.0, "float")},
        }
        searcher = HyperoptSearcher()
        best_overall = (None, None, -np.inf, {})

        for mt in candidate_types:
            space = spaces.get(mt)
            if space:
                def train_fn(params, _mt=mt):
                    m = SklearnModel(_mt, params).fit(X_train, y_train)
                    return self.score_model(m, X_val, y_val)
                params, _ = searcher.search(train_fn, space, n_trials=n_trials,
                                            method=search_method)
                params = params or {}
            else:
                params = {}
            model = SklearnModel(mt, params).fit(X_train, y_train)
            score = self.score_model(model, X_val, y_val)
            logger.info(f"候选 {mt}: IC={score:.4f} params={params}")
            if score > best_overall[2]:
                best_overall = (mt, model, score, params)

        return best_overall
