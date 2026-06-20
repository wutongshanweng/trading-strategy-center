"""
模型注册中心 — 模型版本管理、保存/加载、元数据追踪。

用法:
    registry = ModelRegistry()
    registry.save(model, "lgb_rank", {"symbol": "RB", "metric_value": 0.65})
    model, meta = registry.load("lgb_rank")           # latest
    registry.list_models()
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
from loguru import logger


@dataclass
class ModelMeta:
    """模型元数据。"""
    name: str
    version: int
    created_at: str
    framework: str              # sklearn / lightgbm / xgboost / custom
    model_type: str             # classifier / regressor / ranker
    metric_name: str            # accuracy / f1 / ic / sharpe
    metric_value: float
    feature_count: int
    symbol: str
    description: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


class ModelRegistry:
    """模型注册中心。默认存 ~/.trading/models/。"""

    def __init__(self, root_dir: Optional[str] = None):
        self.root = Path(root_dir or os.path.expanduser("~/.trading/models"))
        self.root.mkdir(parents=True, exist_ok=True)
        self._index_path = self.root / "_index.json"
        self._index: Dict[str, Dict[str, Any]] = self._load_index()

    def _load_index(self) -> Dict:
        if self._index_path.exists():
            with open(self._index_path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_index(self):
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2, ensure_ascii=False)

    def save(self, model: Any, name: str, meta: Optional[Dict] = None) -> ModelMeta:
        """保存模型 (自动版本递增)。"""
        m = meta or {}
        version = self._index.get(name, {}).get("latest_version", 0) + 1
        model_dir = self.root / name
        model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_dir / f"v{version}.joblib")

        model_meta = ModelMeta(
            name=name, version=version, created_at=datetime.now().isoformat(),
            framework=m.get("framework", "unknown"),
            model_type=m.get("model_type", "unknown"),
            metric_name=m.get("metric_name", "none"),
            metric_value=m.get("metric_value", 0.0),
            feature_count=m.get("feature_count", 0),
            symbol=m.get("symbol", ""), description=m.get("description", ""),
            params=m.get("params", {}), tags=m.get("tags", []))

        with open(model_dir / f"v{version}.json", "w", encoding="utf-8") as f:
            json.dump(asdict(model_meta), f, indent=2, ensure_ascii=False)

        self._index[name] = {
            "latest_version": version, "created_at": model_meta.created_at,
            "framework": model_meta.framework, "metric_name": model_meta.metric_name,
            "metric_value": model_meta.metric_value, "symbol": model_meta.symbol,
        }
        self._save_index()
        logger.info(f"Model '{name}' v{version} saved (metric={model_meta.metric_value:.4f})")
        return model_meta

    def load(self, name: str, version: Optional[int] = None) -> Tuple[Any, ModelMeta]:
        """加载模型 (version=None 取 latest)。"""
        if name not in self._index:
            raise ValueError(f"Model '{name}' not found in registry")
        if version is None:
            version = self._index[name]["latest_version"]
        model_path = self.root / name / f"v{version}.joblib"
        meta_path = self.root / name / f"v{version}.json"
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        model = joblib.load(model_path)
        meta = ModelMeta(name=name, version=version, created_at="", framework="",
                         model_type="", metric_name="", metric_value=0.0,
                         feature_count=0, symbol="")
        if meta_path.exists():
            with open(meta_path, encoding="utf-8") as f:
                meta = ModelMeta(**json.load(f))
        logger.info(f"Loaded '{name}' v{version}")
        return model, meta

    def list_models(self) -> List[Dict[str, Any]]:
        """列出所有已注册模型。"""
        return [{"name": k, **v} for k, v in sorted(self._index.items())]

    def delete(self, name: str, version: Optional[int] = None):
        """删除模型 (version=None 删全部版本)。"""
        if version:
            (self.root / name / f"v{version}.joblib").unlink(missing_ok=True)
            (self.root / name / f"v{version}.json").unlink(missing_ok=True)
        else:
            shutil.rmtree(self.root / name, ignore_errors=True)
            self._index.pop(name, None)
            self._save_index()
        logger.info(f"Deleted '{name}' v{version or 'all'}")

    def get_best_by_metric(self, metric: str = "ic") -> List[Tuple[str, float]]:
        """按评估指标获取最佳模型 (用于选模型集成)。"""
        candidates = [(name, info["metric_value"])
                      for name, info in self._index.items()
                      if info.get("metric_name") == metric]
        return sorted(candidates, key=lambda x: -x[1])
