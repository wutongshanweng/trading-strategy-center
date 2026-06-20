"""
特征工程 Pipeline — 从原始行情自动构建 ML 特征。

工作流:
  1. 注册特征函数 (技术面 / 截面 / 自定义)
  2. 按顺序计算所有特征
  3. 可选标准化
  4. 输出完整特征矩阵

用法:
    pipe = FeaturePipeline()
    pipe.register_module(TechnicalFeatureSet())
    X = pipe.compute_all(data, normalize=True)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class FeatureMeta:
    """特征元数据。"""
    name: str
    category: str            # technical / cross_sectional / fundamental / custom
    compute_fn: Callable
    input_columns: List[str] = field(default_factory=list)
    output_columns: List[str] = field(default_factory=list)
    params: Dict = field(default_factory=dict)


class FeaturePipeline:
    """特征工程管线。"""

    def __init__(self):
        self._features: Dict[str, FeatureMeta] = {}
        self._modules: List = []
        self._computed: Optional[pd.DataFrame] = None

    def register_fn(
        self,
        name: str,
        fn: Callable,
        category: str = "custom",
        input_columns: Optional[List[str]] = None,
    ):
        """注册一个特征计算函数。"""
        self._features[name] = FeatureMeta(
            name=name, category=category,
            compute_fn=fn, input_columns=input_columns or [],
        )
        logger.debug(f"Registered feature: {name} ({category})")

    def register(self, fn: Callable):
        """装饰器方式注册。"""
        name = getattr(fn, "__name__", fn.__class__.__name__)
        self.register_fn(name, fn)
        return fn

    def register_module(self, module):
        """批量注册一个特征模块 (如 TechnicalFeatureSet)。"""
        if hasattr(module, "get_features"):
            self._modules.append(module)
            for name, fn, cat in module.get_features():
                self.register_fn(name, fn, cat)

    def compute_all(
        self,
        data: pd.DataFrame,
        feature_names: Optional[List[str]] = None,
        normalize: bool = False,
        dropna: bool = True,
    ) -> pd.DataFrame:
        """计算所有注册的特征, 返回特征矩阵 DataFrame。"""
        names = feature_names or list(self._features.keys())
        results = {}

        for name in names:
            if name not in self._features:
                logger.warning(f"Feature '{name}' not registered, skipping")
                continue
            meta = self._features[name]
            try:
                result = meta.compute_fn(data, **meta.params)
                if isinstance(result, pd.Series):
                    results[name] = result
                elif isinstance(result, pd.DataFrame):
                    for col in result.columns:
                        results[f"{name}_{col}"] = result[col]
            except Exception as e:  # noqa: BLE001
                logger.error(f"Feature '{name}' failed: {e}")

        X = pd.DataFrame(results, index=data.index)
        if dropna:
            X = X.dropna()
        if normalize and not X.empty:
            X = (X - X.mean()) / (X.std() + 1e-10)

        self._computed = X
        logger.info(f"Computed {len(X.columns)} features, {len(X)} samples")
        return X

    def get_feature_names(self, category: Optional[str] = None) -> List[str]:
        """获取特征名列表。"""
        if category:
            return [n for n, m in self._features.items() if m.category == category]
        return list(self._features.keys())

    @property
    def computed(self) -> Optional[pd.DataFrame]:
        return self._computed

    # ───────── 配置持久化 (补充 2) ─────────

    def save_config(self, path: str):
        """保存特征配置到 JSON (compute_fn 不序列化, 仅存元数据)。"""
        import json
        config = {
            name: {
                "name": meta.name,
                "category": meta.category,
                "input_columns": meta.input_columns,
                "params": {k: (str(v) if callable(v) else v)
                           for k, v in meta.params.items()},
            }
            for name, meta in self._features.items()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"Feature config saved to {path} ({len(config)} features)")

    def load_config(self, path: str):
        """从 JSON 加载特征配置 (compute_fn 按名重映射到已注册模块)。"""
        import json
        with open(path, encoding="utf-8") as f:
            config = json.load(f)
        for name, data in config.items():
            self._features[name] = FeatureMeta(
                name=data["name"],
                category=data.get("category", "custom"),
                compute_fn=self._resolve_fn(data["name"]),
                input_columns=data.get("input_columns", []),
                params=data.get("params", {}),
            )
        logger.info(f"Feature config loaded from {path} ({len(config)} features)")

    def _resolve_fn(self, name: str):
        """按特征名解析对应计算函数 (需提前 register_module 已知特征集)。"""
        for module in self._modules:
            for fn_name, fn, _ in module.get_features():
                if fn_name == name:
                    return fn
        logger.warning(f"Cannot resolve function for feature '{name}', will be skipped")
        return lambda data: pd.Series(0.0, index=data.index)

    def list_features(self, category: Optional[str] = None) -> List[Dict]:
        """列出所有特征及元数据 (给前端展示)。"""
        features = []
        for name, meta in self._features.items():
            if category and meta.category != category:
                continue
            features.append({
                "name": name, "category": meta.category,
                "input_columns": meta.input_columns,
            })
        return features

