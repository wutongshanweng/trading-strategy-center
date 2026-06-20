"""
自动 ML Pipeline — 定期重训 + 模型选择 + 注册。

流程 (可 cron / 收盘后触发):
  1. 接收/获取行情 → 2. 构建特征 → 3. 准备标签(未来N天收益) →
  4. 切分训练/验证 → 5. 多候选搜参训练 → 6. 选最优 →
  7. 与 registry 已有模型比较, 更好则注册新版本

用法:
    pipeline = AutoMLPipeline()
    result = pipeline.run("RB2510", data=df)
    print(result.best_model_type, result.best_score)

CLI:
    python -m ml.auto_pipeline --symbol RB2510 --candidates rf,lgbm,xgb
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Optional

import numpy as np
import pandas as pd
from loguru import logger

from ml.registry import ModelRegistry
from ml.features.pipeline import FeaturePipeline
from ml.features.technical_features import TechnicalFeatureSet
from ml.model_selector import ModelSelector


@dataclass
class AutoMLResult:
    symbol: str
    best_model_name: str
    best_model_type: str
    best_score: float
    candidates_trained: int
    old_model_replaced: bool
    feature_count: int
    data_points: int
    best_params: dict

    def to_dict(self) -> dict:
        return asdict(self)


class AutoMLPipeline:
    """自动 ML Pipeline。"""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        selector: Optional[ModelSelector] = None,
        horizon: int = 5,
        val_fraction: float = 0.2,
    ):
        self.registry = registry or ModelRegistry()
        self.selector = selector or ModelSelector()
        self.horizon = horizon
        self.val_fraction = val_fraction
        self.feature_pipeline = FeaturePipeline()
        self.feature_pipeline.register_module(TechnicalFeatureSet())

    def _load_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """从仓库取数 (复用 factor_cli 的取数逻辑)。"""
        try:
            from core.alpha import factor_cli
            return factor_cli._load_from_warehouse(symbol)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"仓库取数失败: {e}")
            return None

    def run(
        self,
        symbol: str,
        data: Optional[pd.DataFrame] = None,
        candidate_types: Optional[List[str]] = None,
        n_trials: int = 10,
    ) -> AutoMLResult:
        """执行一次完整自动重训。"""
        candidate_types = candidate_types or ["rf", "lgbm", "ridge"]
        if data is None:
            data = self._load_data(symbol)
        if data is None or len(data) < 60:
            raise ValueError(f"{symbol} 数据不足 (需 ≥60 条, 实际 {0 if data is None else len(data)})")

        # 特征 + 标签 (未来 horizon 天收益)
        X = self.feature_pipeline.compute_all(data, dropna=True)
        y = data["close"].pct_change(self.horizon).shift(-self.horizon)
        common = X.index.intersection(y.dropna().index)
        X, y = X.loc[common], y.loc[common]
        if len(X) < 40:
            raise ValueError(f"{symbol} 有效样本不足 ({len(X)})")

        # 时序切分 (前段训练, 后段验证)
        split = int(len(X) * (1 - self.val_fraction))
        X_tr, X_val = X.iloc[:split].values, X.iloc[split:].values
        y_tr, y_val = y.iloc[:split].values, y.iloc[split:].values

        # 多候选搜参 + 选优
        mt, model, score, params = self.selector.select_with_hyperopt(
            candidate_types, X_tr, y_tr, X_val, y_val, n_trials=n_trials)

        # 与已有模型比较
        model_name = f"auto_{symbol}"
        old_replaced = False
        try:
            _, old_meta = self.registry.load(model_name)
            old_score = old_meta.metric_value
        except Exception:  # noqa: BLE001
            old_score = -np.inf
        should_register = score > old_score
        if should_register:
            self.registry.save(model._model, model_name, {
                "framework": "sklearn", "model_type": mt, "metric_name": "ic",
                "metric_value": float(score), "feature_count": X.shape[1],
                "symbol": symbol, "params": params,
                "description": f"AutoML {mt} for {symbol}",
            })
            old_replaced = old_score != -np.inf
        else:
            logger.info(f"新模型 IC={score:.4f} 未超过旧模型 {old_score:.4f}, 不替换")

        return AutoMLResult(
            symbol=symbol, best_model_name=model_name, best_model_type=mt,
            best_score=float(score), candidates_trained=len(candidate_types),
            old_model_replaced=old_replaced, feature_count=X.shape[1],
            data_points=len(X), best_params=params)


def _main(argv=None):
    import argparse
    p = argparse.ArgumentParser(prog="auto_pipeline", description="ML 自动重训")
    p.add_argument("--symbol", required=True)
    p.add_argument("--candidates", default="rf,lgbm,ridge")
    p.add_argument("--trials", type=int, default=10)
    args = p.parse_args(argv)
    result = AutoMLPipeline().run(
        args.symbol, candidate_types=[c.strip() for c in args.candidates.split(",")],
        n_trials=args.trials)
    print(f"[auto] {result.symbol}: {result.best_model_type} "
          f"IC={result.best_score:.4f} (替换旧模型={result.old_model_replaced})")


if __name__ == "__main__":
    _main()
