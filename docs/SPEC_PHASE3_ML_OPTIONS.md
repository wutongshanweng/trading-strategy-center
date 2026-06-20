# Phase 3 — ML 升级 + 期权深度 合并 Specification

> 架构师: 冷域 | 开发者: Claude Code | 版本: v1.0
> 基准代码: https://github.com/wutongshanweng/trading-strategy-center (commit f220e89c)
> 本文件包含两个独立模块，可并行实现，互不依赖。

---

## 目录

- **A 篇 — ML 升级** (A 开头的文件/函数)
- **B 篇 — 期权深度** (B 开头的文件/函数)

---

# A 篇 — ML 升级 (Machine Learning)

## A.1 概述

### A.1.1 目标

现存的 `ml/` 模块只有骨架（N-BEATS/TFT 的训练是伪实现），需要补齐：

1. **特征工程 Pipeline** — 从原始行情自动构建 ML 特征
2. **模型注册中心** — 模型版本管理、保存/加载、元数据追踪
3. **超参自动搜索** — Optuna 网格/贝叶斯搜索
4. **模型集成** — Voting/Stacking/Blending 集成
5. **修复 N-BEATS/TFT** — 替换为 sklearn 等可用模型

### A.1.2 文件清单

| 文件 | 操作 | 模块 |
|------|------|------|
| `ml/features/pipeline.py` | 🆕 新建 | A-ML |
| `ml/features/technical_features.py` | 🆕 新建 | A-ML |
| `ml/features/cross_sectional_features.py` | 🆕 新建 | A-ML |
| `ml/registry.py` | 🆕 新建 | A-ML |
| `ml/hyperopt.py` | 🆕 新建 | A-ML |
| `ml/ensemble.py` | 🆕 新建 | A-ML |
| `ml/models/sklearn_wrapper.py` | 🆕 新建 | A-ML |
| `ml/__init__.py` | 🟡 改 | A-ML |
| `ml/pipeline.py` | 🟡 改 | A-ML |
| `tests/unit/test_ml_features.py` | 🆕 新建 | A-ML |
| `tests/unit/test_ml_registry.py` | 🆕 新建 | A-ML |
| `requirements-dev.txt` | 🟡 改 | A-ML |

### A.1.3 新增依赖

```
scikit-learn>=1.2.0   # 基础 ML（已有，但需确认）
optuna>=3.0.0         # 超参自动搜索
joblib>=1.2.0         # 模型序列化（已有）
```

`optuna` 放函数内部 import，无 optuna 时回退到随机搜索。

---

## A.2 模块：特征工程 Pipeline

### A.2.1 ml/features/pipeline.py — 特征管线主入口

```python
"""
特征工程 Pipeline — 从原始行情自动构建 ML 特征。

工作流:
  1. 注册特征函数（技术面 / 截面 / 自定义）
  2. 按顺序计算所有特征
  3. 可选标准化 / PCA
  4. 输出完整特征矩阵

用法:
    pipeline = FeaturePipeline()
    pipeline.register(tech_momentum_features)
    pipeline.register(tech_volatility_features)
    pipeline.register(cs_rank_features)
    X = pipeline.fit_transform(data)  # 返回 DataFrame
"""

from typing import Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from loguru import logger


@dataclass
class FeatureMeta:
    """特征元数据"""
    name: str
    category: str            # "technical" / "cross_sectional" / "fundamental" / "custom"
    compute_fn: Callable
    input_columns: List[str] = field(default_factory=list)
    output_columns: List[str] = field(default_factory=list)
    params: Dict = field(default_factory=dict)


class FeaturePipeline:
    """
    特征工程管线。
    
    用法:
        pipe = FeaturePipeline()
        
        # 方式一: 注册单个特征函数
        pipe.register_fn("momentum_5d", compute_momentum_5d, category="technical")
        
        # 方式二: 批量注册技术特征
        pipe.register_module(TechnicalFeatureSet())
        
        # 方式三: 注册截面特征
        @pipe.register
        def cs_rank_volume(data):
            return data.groupby(level=0)["volume"].rank(pct=True)
        
        # 计算
        X = pipe.compute_all(data)
        # X: DataFrame, columns = [feature_names], index = data.index
    """
    
    def __init__(self):
        self._features: Dict[str, FeatureMeta] = {}
        self._computed: Optional[pd.DataFrame] = None
    
    def register_fn(
        self,
        name: str,
        fn: Callable,
        category: str = "custom",
        input_columns: Optional[List[str]] = None,
    ):
        """注册一个特征计算函数"""
        self._features[name] = FeatureMeta(
            name=name, category=category,
            compute_fn=fn, input_columns=input_columns or [],
        )
        logger.debug(f"Registered feature: {name} ({category})")
    
    def register(self, fn: Callable):
        """装饰器方式注册"""
        name = getattr(fn, "__name__", fn.__class__.__name__)
        self.register_fn(name, fn)
        return fn
    
    def register_module(self, module):
        """批量注册一个特征模块（如 TechnicalFeatureSet）"""
        if hasattr(module, "get_features"):
            for name, fn, cat in module.get_features():
                self.register_fn(name, fn, cat)
    
    def compute_all(
        self,
        data: pd.DataFrame,
        feature_names: Optional[List[str]] = None,
        normalize: bool = False,
        dropna: bool = True,
    ) -> pd.DataFrame:
        """
        计算所有注册的特征。
        
        Args:
            data: 输入数据（需包含 open/high/low/close/volume 等列）
            feature_names: 只计算指定的特征子集
            normalize: 是否做 Z-score 标准化
            dropna: 是否删除 NaN 行
            
        Returns:
            特征矩阵 DataFrame
        """
        names = feature_names or list(self._features.keys())
        results = {}
        
        for name in names:
            if name not in self._features:
                logger.warning(f"Feature '{name}' not registered, skipping")
                continue
            meta = self._features[name]
            try:
                t0 = pd.Timestamp.now()
                result = meta.compute_fn(data, **meta.params)
                elapsed = (pd.Timestamp.now() - t0).total_seconds()
                
                if isinstance(result, pd.Series):
                    results[name] = result
                elif isinstance(result, pd.DataFrame):
                    for col in result.columns:
                        results[f"{name}_{col}"] = result[col]
                
                logger.debug(f"  {name}: {elapsed:.2f}s")
            except Exception as e:
                logger.error(f"Feature '{name}' failed: {e}")
        
        X = pd.DataFrame(results, index=data.index)
        
        if dropna:
            X = X.dropna()
        
        if normalize:
            X = (X - X.mean()) / (X.std() + 1e-10)
        
        self._computed = X
        logger.info(f"Computed {len(X.columns)} features, {len(X)} samples")
        return X
    
    def get_feature_names(self, category: Optional[str] = None) -> List[str]:
        """获取特征名列表"""
        if category:
            return [n for n, m in self._features.items() if m.category == category]
        return list(self._features.keys())
    
    @property
    def computed(self) -> Optional[pd.DataFrame]:
        return self._computed
```

### A.2.2 ml/features/technical_features.py — 技术面特征模块

```python
"""
技术面特征集 — 从行情数据自动构建。

分类:
  - 动量类: 过去 N 天收益率、RSI、乖离率
  - 波动类: ATR、标准差、波动率比率
  - 量价类: 成交量变化、量价比、OBV
  - 形态类: MACD、KDJ、布林带位置

用法:
    from ml.features.technical_features import TechnicalFeatureSet
    
    pipe = FeaturePipeline()
    pipe.register_module(TechnicalFeatureSet())
    X = pipe.compute_all(data)
"""

from typing import List, Tuple, Callable
import pandas as pd
import numpy as np


class TechnicalFeatureSet:
    """技术面特征集合（模块化注册）。"""
    
    def get_features(self) -> List[Tuple[str, Callable, str]]:
        """
        返回 [(name, compute_fn, category), ...]
        compute_fn 签名: fn(data: pd.DataFrame) -> pd.Series
        """
        return [
            # —— 动量类 ——
            ("momentum_5d", self._momentum, "technical"),
            ("momentum_10d", self._momentum_10d, "technical"),
            ("momentum_20d", self._momentum_20d, "technical"),
            ("rsi_14", self._rsi_14, "technical"),
            ("rsi_7", self._rsi_7, "technical"),
            ("close_to_ma5", self._close_to_ma5, "technical"),
            ("close_to_ma20", self._close_to_ma20, "technical"),
            ("close_to_ma60", self._close_to_ma60, "technical"),
            
            # —— 波动类 ——
            ("atr_14", self._atr_14, "technical"),
            ("volatility_5d", self._vol_5d, "technical"),
            ("volatility_20d", self._vol_20d, "technical"),
            ("vol_ratio_5_20", self._vol_ratio, "technical"),
            ("gap_pct", self._gap_pct, "technical"),
            
            # —— 量价类 ——
            ("volume_change_5d", self._vol_change, "technical"),
            ("volume_ma_ratio", self._volume_ma_ratio, "technical"),
            ("obv_change", self._obv_change, "technical"),
            
            # —— 形态类 ——
            ("macd_hist", self._macd_hist, "technical"),
            ("bb_position", self._bb_position, "technical"),
            ("kdj_k", self._kdj_k, "technical"),
            
            # —— 自定义 ——
            ("price_position_20d", self._price_position, "technical"),
            ("crossover_signals", self._crossover_signals, "technical"),
        ]
    
    # ──── 实现 ────
    
    def _momentum(self, data: pd.DataFrame) -> pd.Series:
        c = data["close"]
        return c.pct_change(5)
    
    def _momentum_10d(self, data: pd.DataFrame) -> pd.Series:
        return data["close"].pct_change(10)
    
    def _momentum_20d(self, data: pd.DataFrame) -> pd.Series:
        return data["close"].pct_change(20)
    
    def _rsi_14(self, data: pd.DataFrame) -> pd.Series:
        delta = data["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))
    
    def _rsi_7(self, data: pd.DataFrame) -> pd.Series:
        delta = data["close"].diff()
        gain = delta.clip(lower=0).rolling(7).mean()
        loss = (-delta.clip(upper=0)).rolling(7).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))
    
    def _close_to_ma5(self, data: pd.DataFrame) -> pd.Series:
        c = data["close"]
        ma5 = c.rolling(5).mean()
        return (c - ma5) / (ma5 + 1e-10)
    
    def _close_to_ma20(self, data: pd.DataFrame) -> pd.Series:
        c = data["close"]
        ma20 = c.rolling(20).mean()
        return (c - ma20) / (ma20 + 1e-10)
    
    def _close_to_ma60(self, data: pd.DataFrame) -> pd.Series:
        c = data["close"]
        ma60 = c.rolling(60).mean()
        return (c - ma60) / (ma60 + 1e-10)
    
    def _atr_14(self, data: pd.DataFrame) -> pd.Series:
        h, l, c = data["high"], data["low"], data["close"]
        tr = pd.concat([
            h - l,
            (h - c.shift()).abs(),
            (l - c.shift()).abs(),
        ], axis=1).max(axis=1)
        return tr.rolling(14).mean() / c
    
    def _vol_5d(self, data: pd.DataFrame) -> pd.Series:
        return data["close"].pct_change().rolling(5).std()
    
    def _vol_20d(self, data: pd.DataFrame) -> pd.Series:
        return data["close"].pct_change().rolling(20).std()
    
    def _vol_ratio(self, data: pd.DataFrame) -> pd.Series:
        """短期波动 / 长期波动"""
        v5 = data["close"].pct_change().rolling(5).std()
        v20 = data["close"].pct_change().rolling(20).std()
        return v5 / (v20 + 1e-10)
    
    def _gap_pct(self, data: pd.DataFrame) -> pd.Series:
        """跳空幅度 (open - prev_close) / prev_close"""
        return (data["open"] - data["close"].shift(1)) / (data["close"].shift(1) + 1e-10)
    
    def _vol_change(self, data: pd.DataFrame) -> pd.Series:
        """过去5天成交量变化率"""
        return data["volume"].pct_change(5)
    
    def _volume_ma_ratio(self, data: pd.DataFrame) -> pd.Series:
        """成交量 / 20日均量"""
        v = data["volume"]
        return v / (v.rolling(20).mean() + 1e-10)
    
    def _obv_change(self, data: pd.DataFrame) -> pd.Series:
        """OBV (On-Balance Volume) 变化率"""
        close = data["close"]
        volume = data["volume"]
        obv = (volume * (close.diff() > 0).astype(int) -
               volume * (close.diff() < 0).astype(int)).cumsum()
        return obv.pct_change(5)
    
    def _macd_hist(self, data: pd.DataFrame) -> pd.Series:
        """MACD 柱状图值"""
        c = data["close"]
        ema12 = c.ewm(span=12).mean()
        ema26 = c.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        return macd - signal
    
    def _bb_position(self, data: pd.DataFrame) -> pd.Series:
        """布林带位置: (close - lower) / (upper - lower), 0~1"""
        c = data["close"]
        ma = c.rolling(20).mean()
        std = c.rolling(20).std()
        upper = ma + 2 * std
        lower = ma - 2 * std
        return (c - lower) / (upper - lower + 1e-10)
    
    def _kdj_k(self, data: pd.DataFrame) -> pd.Series:
        """KDJ 随机指标 K 值"""
        h = data["high"].rolling(9).max()
        l = data["low"].rolling(9).min()
        rsv = (data["close"] - l) / (h - l + 1e-10) * 100
        return rsv.ewm(span=3).mean()
    
    def _price_position(self, data: pd.DataFrame) -> pd.Series:
        """过去20天价格位置: (close - min20) / (max20 - min20)"""
        c = data["close"]
        min20 = c.rolling(20).min()
        max20 = c.rolling(20).max()
        return (c - min20) / (max20 - min20 + 1e-10)
    
    def _crossover_signals(self, data: pd.DataFrame) -> pd.Series:
        """均线交叉信号: +1 金叉, -1 死叉, 0 无"""
        ma5 = data["close"].rolling(5).mean()
        ma20 = data["close"].rolling(20).mean()
        cross = pd.Series(0, index=data.index)
        cross[(ma5 > ma20) & (ma5.shift(1) <= ma20.shift(1))] = 1
        cross[(ma5 < ma20) & (ma5.shift(1) >= ma20.shift(1))] = -1
        return cross
```

### A.2.3 ml/features/cross_sectional_features.py — 截面特征

```python
"""
截面特征 — 横截面排名的相对强弱。

用于多标的同时预测（如全品种打分排序）。
对每个时点计算所有标的的相对排名。

用法:
    pipe.register_module(CrossSectionalFeatureSet())
"""

from typing import List, Tuple, Callable
import pandas as pd
import numpy as np


class CrossSectionalFeatureSet:
    """截面特征（横截面排名类）。"""
    
    def get_features(self) -> List[Tuple[str, Callable, str]]:
        return [
            ("cs_rank_momentum_5d", self._cs_rank_mom_5d, "cross_sectional"),
            ("cs_rank_momentum_20d", self._cs_rank_mom_20d, "cross_sectional"),
            ("cs_rank_volume", self._cs_rank_volume, "cross_sectional"),
            ("cs_rank_volatility", self._cs_rank_vol, "cross_sectional"),
            ("cs_zscore_momentum_5d", self._cs_z_mom_5d, "cross_sectional"),
        ]
    
    def _cs_rank_mom_5d(self, data: pd.DataFrame) -> pd.Series:
        # 假设 data 是多标的拼接，需按时间分组
        if "date" in data.columns:
            mom5 = data.groupby("date")["close"].transform(lambda x: x.pct_change(5))
            return mom5.groupby(data["date"]).rank(pct=True)
        return pd.Series(index=data.index, dtype=float)
    
    def _cs_rank_mom_20d(self, data: pd.DataFrame) -> pd.Series:
        if "date" in data.columns:
            mom20 = data.groupby("date")["close"].transform(lambda x: x.pct_change(20))
            return mom20.groupby(data["date"]).rank(pct=True)
        return pd.Series(index=data.index, dtype=float)
    
    def _cs_rank_volume(self, data: pd.DataFrame) -> pd.Series:
        if "date" in data.columns:
            return data.groupby("date")["volume"].rank(pct=True)
        return pd.Series(index=data.index, dtype=float)
    
    def _cs_rank_vol(self, data: pd.DataFrame) -> pd.Series:
        if "date" in data.columns:
            vol20 = data.groupby("date")["close"].transform(
                lambda x: x.pct_change().rolling(20).std()
            )
            return vol20.groupby(data["date"]).rank(pct=True)
        return pd.Series(index=data.index, dtype=float)
    
    def _cs_z_mom_5d(self, data: pd.DataFrame) -> pd.Series:
        if "date" in data.columns:
            mom5 = data.groupby("date")["close"].transform(lambda x: x.pct_change(5))
            return mom5.groupby(data["date"]).transform(
                lambda x: (x - x.mean()) / (x.std() + 1e-10)
            )
        return pd.Series(index=data.index, dtype=float)
```

---

## A.3 模块：模型注册中心

### A.3.1 ml/registry.py

```python
"""
模型注册中心 — 模型版本管理、保存/加载、元数据追踪。

功能:
  1. 保存训练好的模型（含元数据）
  2. 按名称/版本加载模型
  3. 列出所有已注册模型
  4. 自动版本递增

用法:
    registry = ModelRegistry()
    
    # 保存模型
    registry.save(model, "lgb_rank", {
        "symbol": "RB", "features": 20, "score": 0.65,
    })
    
    # 加载模型
    model, meta = registry.load("lgb_rank", version="latest")
    
    # 列出
    registry.list_models()
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import joblib
from loguru import logger


@dataclass
class ModelMeta:
    """模型元数据"""
    name: str
    version: int
    created_at: str
    framework: str              # "sklearn" / "lightgbm" / "xgboost" / "custom"
    model_type: str             # "classifier" / "regressor" / "ranker"
    metric_name: str            # "accuracy" / "f1" / "ic" / "sharpe"
    metric_value: float
    feature_count: int
    symbol: str                 # 训练品种
    description: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    

class ModelRegistry:
    """
    模型注册中心。
    
    Args:
        root_dir: 模型存储根目录，默认 ~/.trading/models/
    """
    
    def __init__(self, root_dir: Optional[str] = None):
        self.root = Path(root_dir or os.path.expanduser("~/.trading/models"))
        self.root.mkdir(parents=True, exist_ok=True)
        self._index_path = self.root / "_index.json"
        self._index: Dict[str, Dict[str, Any]] = self._load_index()
    
    def _load_index(self) -> Dict:
        if self._index_path.exists():
            with open(self._index_path) as f:
                return json.load(f)
        return {}
    
    def _save_index(self):
        with open(self._index_path, "w") as f:
            json.dump(self._index, f, indent=2)
    
    def save(
        self,
        model: Any,
        name: str,
        meta: Optional[Dict] = None,
    ) -> ModelMeta:
        """
        保存模型。
        
        Args:
            model: 模型对象（需支持 joblib.dump）
            name: 模型名称
            meta: 元数据字典
            
        Returns:
            ModelMeta
        """
        # 自动版本递增
        current = self._index.get(name, {})
        version = current.get("latest_version", 0) + 1
        
        model_dir = self.root / name
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存模型文件
        model_path = model_dir / f"v{version}.joblib"
        joblib.dump(model, model_path)
        
        # 构建元数据
        model_meta = ModelMeta(
            name=name,
            version=version,
            created_at=datetime.now().isoformat(),
            framework=meta.get("framework", "unknown") if meta else "unknown",
            model_type=meta.get("model_type", "unknown") if meta else "unknown",
            metric_name=meta.get("metric_name", "none") if meta else "none",
            metric_value=meta.get("metric_value", 0.0) if meta else 0.0,
            feature_count=meta.get("feature_count", 0) if meta else 0,
            symbol=meta.get("symbol", "") if meta else "",
            description=meta.get("description", "") if meta else "",
            params=meta.get("params", {}) if meta else {},
            tags=meta.get("tags", []) if meta else [],
        )
        
        # 保存元数据 JSON
        meta_path = model_dir / f"v{version}.json"
        with open(meta_path, "w") as f:
            json.dump(asdict(model_meta), f, indent=2, ensure_ascii=False)
        
        # 更新索引
        self._index[name] = {
            "latest_version": version,
            "created_at": model_meta.created_at,
            "framework": model_meta.framework,
            "metric_name": model_meta.metric_name,
            "metric_value": model_meta.metric_value,
            "symbol": model_meta.symbol,
        }
        self._save_index()
        
        logger.info(f"✅ Model '{name}' v{version} saved (metric={model_meta.metric_value:.4f})")
        return model_meta
    
    def load(
        self,
        name: str,
        version: Optional[int] = None,
    ) -> Tuple[Any, ModelMeta]:
        """
        加载模型。
        
        Args:
            name: 模型名称
            version: 版本号（None=latest）
            
        Returns:
            (model, ModelMeta)
        """
        if name not in self._index:
            raise ValueError(f"Model '{name}' not found in registry")
        
        if version is None:
            version = self._index[name]["latest_version"]
        
        model_path = self.root / name / f"v{version}.joblib"
        meta_path = self.root / name / f"v{version}.json"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        model = joblib.load(model_path)
        
        meta = ModelMeta(name=name, version=0, created_at="", framework="", model_type="",
                         metric_name="", metric_value=0.0, feature_count=0, symbol="")
        if meta_path.exists():
            with open(meta_path) as f:
                meta_dict = json.load(f)
                meta = ModelMeta(**meta_dict)
        
        logger.info(f"📦 Loaded '{name}' v{version}")
        return model, meta
    
    def list_models(self) -> List[Dict[str, Any]]:
        """列出所有已注册模型"""
        return [
            {"name": k, **v} for k, v in sorted(self._index.items())
        ]
    
    def delete(self, name: str, version: Optional[int] = None):
        """删除模型"""
        import shutil
        if version:
            model_path = self.root / name / f"v{version}.joblib"
            meta_path = self.root / name / f"v{version}.json"
            model_path.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
        else:
            shutil.rmtree(self.root / name, ignore_errors=True)
            self._index.pop(name, None)
            self._save_index()
        logger.info(f"🗑️  Deleted '{name}' v{version or 'all'}")
    
    def get_best_by_metric(
        self, metric: str = "ic", min_samples: int = 1
    ) -> List[Tuple[str, float]]:
        """按评估指标获取最佳模型（用于选模型集成）"""
        candidates = []
        for name, info in self._index.items():
            if info.get("metric_name") == metric:
                candidates.append((name, info["metric_value"]))
        return sorted(candidates, key=lambda x: -x[1])
```

---

## A.4 模块：超参自动搜索

### A.4.1 ml/hyperopt.py

```python
"""
超参自动搜索 — 使用 Optuna 或随机搜索。

用法:
    searcher = HyperoptSearcher()
    
    # 定义参数空间
    param_space = {
        "learning_rate": (0.01, 0.3, "float"),
        "max_depth": (3, 10, "int"),
        "n_estimators": (50, 300, "int"),
    }
    
    # 执行搜索
    best_params, best_score = searcher.search(
        train_fn=train_model,      # def train_fn(params) -> float
        param_space=param_space,
        n_trials=50,
        method="optuna",           # 或 "random" / "grid"
    )
"""

from typing import Callable, Dict, List, Optional, Tuple, Union
import numpy as np
from loguru import logger


class HyperoptSearcher:
    """
    超参自动搜索。
    
    三种搜索方法:
      - optuna: 贝叶斯优化（推荐，需要 optuna）
      - random: 随机搜索（无额外依赖）
      - grid: 网格搜索（参数离散化）
    """
    
    def search(
        self,
        train_fn: Callable[[Dict], float],
        param_space: Dict[str, Tuple],
        n_trials: int = 50,
        method: str = "optuna",
        direction: str = "maximize",
        seed: int = 42,
    ) -> Tuple[Dict, float]:
        """
        执行超参搜索。
        
        Args:
            train_fn: 训练函数，接收参数字典，返回评估分数
            param_space: 参数空间
                {"name": (low, high, "float"/"int"), "name2": ["a","b","c"]}
            n_trials: 搜索次数
            method: "optuna" / "random" / "grid"
            direction: "maximize" / "minimize"
            
        Returns:
            (best_params, best_score)
        """
        if method == "optuna":
            return self._optuna_search(train_fn, param_space, n_trials, direction, seed)
        elif method == "random":
            return self._random_search(train_fn, param_space, n_trials, direction, seed)
        elif method == "grid":
            return self._grid_search(train_fn, param_space, direction)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _random_search(
        self, train_fn, param_space, n_trials, direction, seed
    ) -> Tuple[Dict, float]:
        """随机搜索（无依赖，兜底方案）。"""
        np.random.seed(seed)
        best_params = None
        best_score = -np.inf if direction == "maximize" else np.inf
        
        for trial in range(n_trials):
            params = {}
            for name, spec in param_space.items():
                if isinstance(spec, list):
                    params[name] = np.random.choice(spec)
                elif isinstance(spec, tuple) and len(spec) == 3:
                    low, high, dtype = spec
                    if dtype == "float":
                        params[name] = float(np.random.uniform(low, high))
                    elif dtype == "int":
                        params[name] = int(np.random.randint(low, high + 1))
                else:
                    params[name] = spec
            
            try:
                score = train_fn(params)
                if (direction == "maximize" and score > best_score) or \
                   (direction == "minimize" and score < best_score):
                    best_score = score
                    best_params = params.copy()
                logger.debug(f"Trial {trial+1}/{n_trials}: score={score:.4f}")
            except Exception as e:
                logger.warning(f"Trial {trial+1} failed: {e}")
        
        return best_params, best_score
    
    def _optuna_search(
        self, train_fn, param_space, n_trials, direction, seed
    ) -> Tuple[Dict, float]:
        """Optuna 贝叶斯搜索（推荐）。"""
        try:
            import optuna
        except ImportError:
            logger.warning("optuna not installed, falling back to random search")
            return self._random_search(train_fn, param_space, n_trials, direction, seed)
        
        def objective(trial):
            params = {}
            for name, spec in param_space.items():
                if isinstance(spec, list):
                    params[name] = trial.suggest_categorical(name, spec)
                elif isinstance(spec, tuple) and len(spec) == 3:
                    low, high, dtype = spec
                    if dtype == "float":
                        params[name] = trial.suggest_float(name, low, high)
                    elif dtype == "int":
                        params[name] = trial.suggest_int(name, low, high)
                else:
                    params[name] = spec
            return train_fn(params)
        
        study = optuna.create_study(
            direction=direction,
            sampler=optuna.samplers.TPESampler(seed=seed),
        )
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        
        logger.info(f"Optuna best: {study.best_value:.4f}")
        return study.best_params, study.best_value
    
    def _grid_search(self, train_fn, param_space, direction) -> Tuple[Dict, float]:
        """网格搜索（参数少时用）。"""
        from itertools import product
        
        param_values = []
        param_names = []
        for name, spec in param_space.items():
            param_names.append(name)
            if isinstance(spec, list):
                param_values.append(spec)
            elif isinstance(spec, tuple) and len(spec) == 3:
                low, high, dtype = spec
                if dtype == "int":
                    values = list(range(int(low), int(high) + 1))
                else:
                    values = [round(low + (high - low) * i / 10, 2) for i in range(11)]
                param_values.append(values)
        
        best_params = None
        best_score = -np.inf if direction == "maximize" else np.inf
        
        for values in product(*param_values):
            params = dict(zip(param_names, values))
            try:
                score = train_fn(params)
                if (direction == "maximize" and score > best_score) or \
                   (direction == "minimize" and score < best_score):
                    best_score = score
                    best_params = params.copy()
            except Exception as e:
                logger.warning(f"Grid point {params} failed: {e}")
        
        return best_params, best_score
```

---

## A.5 模块：模型集成

### A.5.1 ml/ensemble.py

```python
"""
模型集成 — 组合多个模型提升预测稳定性。

方法:
  - Voting: 等权/加权投票（分类）或平均（回归）
  - Stacking: 用元模型组合基模型预测
  - Blending: 用验证集做加权组合

用法:
    ensemble = ModelEnsemble(method="voting")
    ensemble.add_model(model1, weight=0.5)
    ensemble.add_model(model2, weight=0.3)
    ensemble.add_model(model3, weight=0.2)
    pred = ensemble.predict(X)
"""

from typing import Any, Dict, List, Optional, Tuple, Callable
import numpy as np
import pandas as pd
from loguru import logger


class ModelEnsemble:
    """
    模型集成。
    
    支持三种集成方法:
      - voting: 等权/加权平均
      - stacking: 元模型组合（需额外训练）
      - blending: 验证集加权
    """
    
    def __init__(self, method: str = "voting"):
        """
        Args:
            method: "voting" / "stacking" / "blending"
        """
        self.method = method
        self.models: List[Tuple[Any, float]] = []  # [(model, weight), ...]
        self.meta_model: Optional[Any] = None
        self._fitted = False
    
    def add_model(self, model: Any, weight: float = 1.0):
        """添加一个基模型"""
        self.models.append((model, weight))
        logger.debug(f"Added model to ensemble: {type(model).__name__} (weight={weight})")
    
    def fit(self, X, y):
        """训练集成（仅 stacking 需要训练元模型）。"""
        if self.method == "stacking":
            self._fit_stacking(X, y)
        self._fitted = True
        return self
    
    def _fit_stacking(self, X, y):
        """Stacking: 用基模型的预测训练元模型。"""
        if len(self.models) < 2:
            logger.warning("Stacking needs at least 2 base models, falling back to voting")
            self.method = "voting"
            return
        
        # 生成基模型预测作为元特征
        meta_features = np.column_stack([
            model.predict(X) for model, _ in self.models
        ])
        
        # 训练元模型（默认用线性回归）
        from sklearn.linear_model import LinearRegression
        self.meta_model = LinearRegression()
        self.meta_model.fit(meta_features, y)
        logger.info(f"Stacking meta-model trained: weights={self.meta_model.coef_}")
    
    def predict(self, X) -> np.ndarray:
        """预测。"""
        if not self.models:
            raise ValueError("No models in ensemble")
        
        predictions = np.column_stack([
            model.predict(X) for model, _ in self.models
        ])
        
        if self.method == "voting":
            weights = np.array([w for _, w in self.models])
            weights = weights / weights.sum()
            return predictions @ weights
        
        elif self.method == "blending":
            return self._predict_blending(predictions)
        
        elif self.method == "stacking" and self.meta_model is not None:
            return self.meta_model.predict(predictions)
        
        else:
            return predictions.mean(axis=1)
    
    def _predict_blending(self, predictions: np.ndarray) -> np.ndarray:
        """Blending: 加权平均，权重从验证集表现计算。"""
        return predictions.mean(axis=1)  # 简化版
    
    @property
    def weights_info(self) -> str:
        """权重信息"""
        parts = [f"{type(m).__name__}:{w:.2f}" for m, w in self.models]
        return " | ".join(parts)
```

---

## A.6 修复：新增 sklearn 模型包装

### A.6.1 ml/models/sklearn_wrapper.py

```python
"""
通用 sklearn 模型包装器。

替代现存的 N-BEATS/TFT 伪实现，
提供可直接使用的「真」模型。

用法:
    from ml.models.sklearn_wrapper import SklearnModel
    
    model = SklearnModel(
        model_type="lgbm",  # "rf" / "xgb" / "lgbm" / "ridge" / "svr"
        params={"n_estimators": 100, "max_depth": 6},
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
"""

from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
from loguru import logger


class SklearnModel:
    """
    通用 sklearn 模型包装器。
    
    支持模型类型:
      - "rf": RandomForest
      - "xgb": XGBoost
      - "lgbm": LightGBM
      - "ridge": Ridge 回归
      - "svr": SVM 回归
      - "mlp": 简单神经网络
    """
    
    def __init__(
        self,
        model_type: str = "lgbm",
        params: Optional[Dict] = None,
    ):
        self.model_type = model_type
        self.params = params or {}
        self._model = None
        self._build()
    
    def _build(self):
        """构建内部模型。"""
        if self.model_type == "rf":
            from sklearn.ensemble import RandomForestRegressor
            self._model = RandomForestRegressor(
                n_estimators=self.params.get("n_estimators", 100),
                max_depth=self.params.get("max_depth", 10),
                min_samples_leaf=self.params.get("min_samples_leaf", 5),
                random_state=42, n_jobs=-1,
            )
        elif self.model_type == "xgb":
            try:
                from xgboost import XGBRegressor
                self._model = XGBRegressor(
                    n_estimators=self.params.get("n_estimators", 100),
                    max_depth=self.params.get("max_depth", 6),
                    learning_rate=self.params.get("learning_rate", 0.1),
                    subsample=self.params.get("subsample", 0.8),
                    random_state=42, n_jobs=-1,
                )
            except ImportError:
                logger.warning("xgboost not installed, falling back to rf")
                return self._build_rf_fallback()
        elif self.model_type == "lgbm":
            try:
                import lightgbm as lgb
                self._model = lgb.LGBMRegressor(
                    n_estimators=self.params.get("n_estimators", 100),
                    max_depth=self.params.get("max_depth", 6),
                    learning_rate=self.params.get("learning_rate", 0.1),
                    subsample=self.params.get("subsample", 0.8),
                    random_state=42, n_jobs=-1,
                )
            except ImportError:
                logger.warning("lightgbm not installed, falling back to rf")
                return self._build_rf_fallback()
        elif self.model_type == "ridge":
            from sklearn.linear_model import Ridge
            self._model = Ridge(alpha=self.params.get("alpha", 1.0))
        elif self.model_type == "svr":
            from sklearn.svm import SVR
            self._model = SVR(
                kernel=self.params.get("kernel", "rbf"),
                C=self.params.get("C", 1.0),
            )
        elif self.model_type == "mlp":
            from sklearn.neural_network import MLPRegressor
            self._model = MLPRegressor(
                hidden_layer_sizes=self.params.get("hidden_layers", (64, 32)),
                learning_rate_init=self.params.get("lr", 0.001),
                max_iter=self.params.get("max_iter", 200),
                random_state=42,
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def _build_rf_fallback(self):
        from sklearn.ensemble import RandomForestRegressor
        self._model = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1,
        )
        self.model_type = "rf"
    
    def fit(self, X, y):
        if self._model is None:
            raise RuntimeError("Model not built")
        self._model.fit(X, y)
        logger.info(f"✅ {self.model_type} trained")
        return self
    
    def predict(self, X) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Model not built")
        return self._model.predict(X)
    
    def get_params(self) -> Dict:
        return self._model.get_params() if self._model else {}
    
    def feature_importance(self) -> Optional[pd.Series]:
        """获取特征重要性（树模型）。"""
        if hasattr(self._model, "feature_importances_"):
            return pd.Series(
                self._model.feature_importances_,
                index=[f"f{i}" for i in range(len(self._model.feature_importances_))],
            ).sort_values(ascending=False)
        return None
```

---

## A.7 测试验证（ML）

### A.7.1 test_ml_features.py

```python
"""ML 特征工程测试"""

import pytest
import pandas as pd
import numpy as np
from ml.features.pipeline import FeaturePipeline
from ml.features.technical_features import TechnicalFeatureSet


class TestFeaturePipeline:
    def test_register_and_compute(self):
        pipe = FeaturePipeline()
        pipe.register_module(TechnicalFeatureSet())
        data = _make_sample_data(100)
        X = pipe.compute_all(data)
        assert X.shape[1] >= 20  # 至少 20 个特征
    
    def test_different_data_sizes(self):
        for n in [30, 100, 500]:
            pipe = FeaturePipeline()
            pipe.register_module(TechnicalFeatureSet())
            X = pipe.compute_all(_make_sample_data(n))
            assert X.shape[0] <= n


class TestTechnicalFeatureSet:
    def test_all_features_return_series(self):
        tfs = TechnicalFeatureSet()
        data = _make_sample_data(100)
        for name, fn, cat in tfs.get_features():
            result = fn(data)
            assert isinstance(result, pd.Series), f"{name} not Series"
```


---

# B 篇 — 期权深度 (Options)

## B.1 概述

### B.1.1 目标

现存的 `options/` 模块有扎实的基础（Greeks/定价/IV/SVI切片/策略），需要新增：

1. **全波动率曲面 3D 建模** — 跨到期日的 IV 曲面插值
2. **期限结构套利信号** — 利用日历价差+期限结构偏离
3. **期权-期货联合策略** — 同时使用期权和期货的复合信号

### B.1.2 文件清单

| 文件 | 操作 | 模块 |
|------|------|------|
| `options/volatility/surface.py` | 🆕 新建 | B-期权 |
| `options/strategies/term_arbitrage.py` | 🆕 新建 | B-期权 |
| `options/strategies/futures_combo.py` | 🆕 新建 | B-期权 |
| `options/strategies/__init__.py` | 🟡 改 | B-期权 |
| `tests/unit/test_options_surface.py` | 🆕 新建 | B-期权 |
| `tests/unit/test_options_strategies_extended.py` | 🆕 新建 | B-期权 |

### B.1.3 依赖

```
scipy>=1.7.0     # 已有，用于插值
```

不新增任何依赖。

---

## B.2 模块：全波动率曲面 3D 建模

### B.2.1 options/volatility/surface.py

```python
"""
全波动率曲面建模 — 跨到期日的 IV 曲面 3D 插值与分析。

已有 SVI 切片拟合（单个到期日），本模块在其基础上扩展:
  1. 多到期日 SVI 参数插值
  2. 任意 (K, T) 点的 IV 查询
  3. 曲面斜率/曲率分析
  4. 曲面可视化数据输出

用法:
    surface = VolSurface()
    surface.add_slice(T=0.1, strikes=[...], ivs=[...])
    surface.add_slice(T=0.3, strikes=[...], ivs=[...])
    surface.add_slice(T=0.6, strikes=[...], ivs=[...])
    
    # 查询任意点
    iv = surface.get_iv(K=3800, T=0.25)
    
    # 曲面分析
    skew = surface.get_skew(T=0.25)    # 偏度斜率
    curvature = surface.get_curvature(T=0.25)  # 曲率
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
from scipy import interpolate
from loguru import logger


@dataclass
class SurfaceSlice:
    """单个到期日的 IV 切片"""
    T: float                    # 到期时间（年）
    strikes: np.ndarray         # 行权价数组
    ivs: np.ndarray             # 对应 IV 数组
    moneyness: np.ndarray       # log-moneyness = log(K/F)
    svi_params: Optional[List[float]] = None  # [a, b, rho, m, sigma]


class VolSurface:
    """
    全波动率曲面。
    
    支持:
      - 多到期日注册
      - 到期日间线性/SVI 参数插值
      - 任意 (K, T) 点 IV 查询
      - 曲面特征提取（偏度、曲率、期限结构斜率）
    """
    
    def __init__(self):
        self.slices: Dict[float, SurfaceSlice] = {}
        self._forward_price: Optional[float] = None
        self._interpolator: Optional = None
    
    def set_forward(self, F: float):
        """设置标的远期价格"""
        self._forward_price = F
    
    def add_slice(
        self,
        T: float,
        strikes: np.ndarray,
        ivs: np.ndarray,
        svi_params: Optional[List[float]] = None,
    ):
        """
        添加一个到期日切片。
        
        Args:
            T: 到期时间（年）
            strikes: 行权价数组
            ivs: 对应隐含波动率数组
            svi_params: SVI 拟合参数（如有）
        """
        moneyness = np.log(strikes / self._forward_price) if self._forward_price else strikes
        self.slices[T] = SurfaceSlice(
            T=T, strikes=np.asarray(strikes),
            ivs=np.asarray(ivs), moneyness=moneyness,
            svi_params=svi_params,
        )
    
    def build(self):
        """
        构建全曲面插值器。
        
        采用双线性插值（strike × T），
        或基于 SVI 参数插值（如果有 SVI 拟合）。
        """
        if len(self.slices) < 2:
            logger.warning("Need at least 2 slices for surface interpolation")
            return
        
        # 收集所有 (T, K, IV) 点
        points = []
        values = []
        for s in self.slices.values():
            for k, iv in zip(s.strikes, s.ivs):
                points.append([s.T, k])
                values.append(iv)
        
        points = np.array(points)
        values = np.array(values)
        
        if len(points) >= 4:
            self._interpolator = interpolate.LinearNDInterpolator(points, values)
            logger.info(f"✅ Surface built: {len(self.slices)} slices, {len(points)} points")
    
    def get_iv(self, strike: float, T: float) -> Optional[float]:
        """
        查询任意 (strike, T) 点的隐含波动率。
        
        Args:
            strike: 行权价
            T: 到期时间（年）
            
        Returns:
            IV 值，或 None（超出边界）
        """
        if self._interpolator is None:
            return None
        result = self._interpolator(T, strike)
        return float(result) if not np.isnan(result) else None
    
    def get_skew(self, T: float, delta_range: Tuple[float, float] = (0.25, 0.75)) -> float:
        """
        计算偏度: IV(OTM put) - IV(OTM call) 的斜率。
        
        正 = put 更贵（恐惧），负 = call 更贵（贪婪）。
        
        Returns:
            skew 值
        """
        # 在实际中用 delta 计算对应 strike 的 IV 差
        # 这里简化: 用最低 strike vs 最高 strike 的 IV 差
        nearest = self._nearest_slice(T)
        if nearest is None:
            return 0.0
        return float(nearest.ivs[-1] - nearest.ivs[0])
    
    def get_curvature(self, T: float) -> float:
        """曲率: 中间 IV 与两端 IV 平均值的差"""
        nearest = self._nearest_slice(T)
        if nearest is None or len(nearest.ivs) < 3:
            return 0.0
        mid = nearest.ivs[len(nearest.ivs)//2]
        ends = (nearest.ivs[0] + nearest.ivs[-1]) / 2
        return float(mid - ends)
    
    def get_term_structure(
        self, strike: Optional[float] = None
    ) -> List[Tuple[float, float]]:
        """获取期限结构: [(T1, IV1), (T2, IV2), ...]"""
        if strike is None:
            strike = self._forward_price or 0
        result = []
        for T in sorted(self.slices.keys()):
            iv = self.get_iv(strike, T)
            if iv is not None:
                result.append((T, iv))
        return result
    
    def _nearest_slice(self, T: float) -> Optional[SurfaceSlice]:
        """获取最近的到期日切片"""
        if not self.slices:
            return None
        nearest_T = min(self.slices.keys(), key=lambda x: abs(x - T))
        return self.slices[nearest_T]
    
    def surface_to_grid(
        self, n_strikes: int = 20, n_ttm: int = 10
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        将曲面输出为网格数据（用于可视化）。
        
        Returns:
            (T_grid, K_grid, IV_grid) — 每个都是 2D array
        """
        if self._interpolator is None:
            return None, None, None
        
        all_T = sorted(self.slices.keys())
        all_K = np.linspace(
            min(s.strikes.min() for s in self.slices.values()),
            max(s.strikes.max() for s in self.slices.values()),
            n_strikes,
        )
        T_grid, K_grid = np.meshgrid(
            np.linspace(all_T[0], all_T[-1], n_ttm), all_K
        )
        IV_grid = self._interpolator(T_grid, K_grid)
        return T_grid, K_grid, IV_grid


# ──── 便捷函数 ────

def build_surface_from_data(
    option_chain: Dict[float, Tuple[np.ndarray, np.ndarray]],
    forward: float,
) -> VolSurface:
    """
    从期权链数据构建曲面。
    
    Args:
        option_chain: {T: (strikes, ivs)}
        forward: 标的远期价格
        
    Returns:
        VolSurface
    """
    surface = VolSurface()
    surface.set_forward(forward)
    for T, (strikes, ivs) in option_chain.items():
        surface.add_slice(T, strikes, ivs)
    surface.build()
    return surface
```

---

## B.3 模块：期限结构套利信号

### B.3.1 options/strategies/term_arbitrage.py

```python
"""
期限结构套利信号。

核心逻辑:
  利用期权 IV 期限结构的异常偏离产生交易信号。
  
  信号类型:
    1. IV_SKEW: 偏度极端 → 反转信号
    2. TERM_STRUCTURE: 近远月 IV 差极端 → 日历价差信号
    3. SURFACE_ARB: 曲面局部异常 → 蝶式/鹰式套利信号

用法:
    from options.strategies.term_arbitrage import TermArbitrageSignals
    
    arb = TermArbitrageSignals()
    signals = arb.compute(surface=vol_surface, spot=3800)
    
    for sig in signals:
        print(f"{sig['type']}: {sig['direction']} (score={sig['score']:.2f})")
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
from loguru import logger


@dataclass
class TermArbSignal:
    signal_type: str             # "IV_SKEW" / "TERM_STRUCTURE" / "SURFACE_ARB"
    direction: str               # "BULLISH" / "BEARISH" / "NEUTRAL"
    score: float                 # 0~1 信号强度
    confidence: float            # 0~1 置信度
    reason: str                  # 描述
    suggested_strategy: str = "" # 建议策略名
    metadata: Dict = field(default_factory=dict)


class TermArbitrageSignals:
    """
    期限结构套利信号。
    
    检测三类异常:
      1. Skew 极端: 当 put/call 失衡超过阈值
      2. 期限结构扭曲: 近月远月 IV 差超过历史 2-sigma
      3. 曲面局部异常: 相邻行权价 IV 异常凸起
    """
    
    def __init__(
        self,
        skew_threshold: float = 0.15,       # 偏度阈值
        term_zscore_threshold: float = 2.0,  # 期限结构 Z-score 阈值
    ):
        self.skew_threshold = skew_threshold
        self.term_zscore_threshold = term_zscore_threshold
    
    def compute(
        self,
        surface,
        spot: float,
        history: Optional[Dict] = None,
    ) -> List[TermArbSignal]:
        """
        计算所有期限结构套利信号。
        
        Args:
            surface: VolSurface 实例
            spot: 标的现价
            history: 历史数据（可选，含 IV 历史均值/标准差）
            
        Returns:
            信号列表
        """
        signals = []
        
        # 1. Skew 极端信号
        skew_sig = self._check_skew_extreme(surface, spot)
        if skew_sig:
            signals.append(skew_sig)
        
        # 2. 期限结构扭曲
        term_sig = self._check_term_structure(surface, spot, history)
        if term_sig:
            signals.append(term_sig)
        
        # 3. 曲面局部异常
        surface_sigs = self._check_surface_arb(surface, spot)
        signals.extend(surface_sigs)
        
        return signals
    
    def _check_skew_extreme(self, surface, spot) -> Optional[TermArbSignal]:
        """检测 Skew 偏度极端。"""
        # 取最近到期日
        sorted_T = sorted(surface.slices.keys())
        if not sorted_T:
            return None
        
        near_T = sorted_T[0]
        skew = surface.get_skew(near_T)
        
        if skew > self.skew_threshold:
            return TermArbSignal(
                signal_type="IV_SKEW",
                direction="BULLISH",
                score=min(abs(skew) * 2, 1.0),
                confidence=0.6,
                reason=f"Put 溢价极端 (skew={skew:.3f})，市场过度恐惧，预期反弹",
                suggested_strategy="bull_call_spread",
                metadata={"skew": skew, "T": near_T},
            )
        elif skew < -self.skew_threshold:
            return TermArbSignal(
                signal_type="IV_SKEW",
                direction="BEARISH",
                score=min(abs(skew) * 2, 1.0),
                confidence=0.6,
                reason=f"Call 溢价极端 (skew={skew:.3f})，市场过度贪婪，警惕回调",
                suggested_strategy="bear_put_spread",
                metadata={"skew": skew, "T": near_T},
            )
        return None
    
    def _check_term_structure(
        self, surface, spot, history
    ) -> Optional[TermArbSignal]:
        """检测期限结构扭曲。"""
        if len(surface.slices) < 2:
            return None
        
        sorted_T = sorted(surface.slices.keys())
        near = surface.slices[sorted_T[0]]
        far = surface.slices[sorted_T[-1]]
        
        # ATM IV 差值
        atm_strike = spot
        near_iv = surface.get_iv(atm_strike, near.T)
        far_iv = surface.get_iv(atm_strike, far.T)
        
        if near_iv is None or far_iv is None:
            return None
        
        spread = far_iv - near_iv  # 正 = contango（远月更贵）
        
        # 如果有历史数据，检查是否超过 2-sigma
        if history and "term_spread_hist" in history:
            hist = np.array(history["term_spread_hist"])
            mean = hist.mean()
            std = hist.std()
            z = (spread - mean) / (std + 1e-10)
            
            if abs(z) > self.term_zscore_threshold:
                direction = "BEARISH" if spread > mean else "BULLISH"
                return TermArbSignal(
                    signal_type="TERM_STRUCTURE",
                    direction=direction,
                    score=min(abs(z) / 5, 1.0),
                    confidence=0.7,
                    reason=f"期限结构扭曲 (z-score={z:.1f})，{near.T:.2f}y vs {far.T:.2f}y",
                    suggested_strategy="calendar_spread",
                    metadata={"spread": spread, "zscore": z},
                )
        
        # 无历史数据时用绝对值判断
        if spread > 0.05:  # 5% 以上
            return TermArbSignal(
                signal_type="TERM_STRUCTURE",
                direction="BEARISH",
                score=0.4, confidence=0.4,
                reason=f"期限结构陡峭contango (spread={spread:.2%})，远月溢价高",
                suggested_strategy="calendar_spread",
            )
        elif spread < -0.05:
            return TermArbSignal(
                signal_type="TERM_STRUCTURE",
                direction="BULLISH",
                score=0.4, confidence=0.4,
                reason=f"期限结构backwardation (spread={spread:.2%})，近月恐慌",
                suggested_strategy="calendar_spread",
            )
        
        return None
    
    def _check_surface_arb(
        self, surface, spot
    ) -> List[TermArbSignal]:
        """检测曲面局部异常（蝶式套利机会）。"""
        signals = []
        # 检查同一到期日相邻行权价的 IV 是否有异常凸起
        for T, s in surface.slices.items():
            if len(s.ivs) < 3:
                continue
            # 检测 butterfly 套利: 中间 strike 的 IV 异常偏离线性插值
            for i in range(1, len(s.ivs) - 1):
                left_iv = s.ivs[i-1]
                mid_iv = s.ivs[i]
                right_iv = s.ivs[i+1]
                expected_mid = (left_iv + right_iv) / 2
                deviation = abs(mid_iv - expected_mid)
                
                if deviation > 0.03:  # 3% 偏离
                    strike = s.strikes[i]
                    is_convex = mid_iv > expected_mid  # 凸起
                    signals.append(TermArbSignal(
                        signal_type="SURFACE_ARB",
                        direction="BEARISH" if is_convex else "BULLISH",
                        score=min(deviation * 10, 0.8),
                        confidence=0.5,
                        reason=f"K={strike} IV 异常{'凸起' if is_convex else '凹陷'} ({deviation:.1%})",
                        suggested_strategy="iron_condor" if is_convex else "long_butterfly",
                        metadata={"T": T, "strike": strike, "deviation": deviation},
                    ))
                    break  # 每个到期日最多一个信号
        
        return signals
```

---

## B.4 模块：期权-期货联合策略

### B.4.1 options/strategies/futures_combo.py

```python
"""
期权-期货联合策略 — 同时使用期权和期货的复合信号。

核心思想:
  期货信号提供方向判断，期权信号提供执行结构。
  二者结合产生比单一工具更优的风险收益。

策略类型:
  1. FUTURES_COVERED: 期货 + 期权保险（替代止损）
  2. OPTIONS_FENCE: 期权 fence 保护期货头寸
  3. SIGNAL_BOOST: 期权信号强化/削弱期货信号
  4. VOL_HEDGE: 用期权对冲期货的波动率风险

用法:
    from options.strategies.futures_combo import FuturesOptionsComboSignals
    
    combo = FuturesOptionsComboSignals()
    signal = combo.combine(
        futures_direction="BUY",
        futures_confidence=0.7,
        iv_rank=0.85,
        skew=-0.08,
        spot=3800,
    )
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
from loguru import logger


@dataclass
class ComboSignal:
    """期货-期权联合信号"""
    strategy_name: str              # "covered_call" / "protective_put" / "collar"
    futures_direction: str          # "LONG" / "SHORT" / "FLAT"
    options_leg: str                # 期权腿描述
    adjusted_confidence: float      # 联合置信度
    adjusted_direction: str         # 最终方向
    reason: str
    entry_conditions: Dict = field(default_factory=dict)
    risk_notes: str = ""


class FuturesOptionsComboSignals:
    """
    期货-期权联合策略信号。
    
    根据期货信号 + 期权市场状态，推荐最优的联合策略。
    """
    
    def combine(
        self,
        futures_direction: str,        # "BUY" / "SELL" / "HOLD"
        futures_confidence: float,     # 0~1
        iv_rank: float,                # 0~100
        skew: float,                   # 偏度
        spot: float,                   # 标的现价
        term_structure: Optional[str] = None,  # "CONTANGO" / "BACKWARD"
        options_available: bool = True,
    ) -> ComboSignal:
        """
        综合期货和期权信号，输出联合策略。
        
        决策树:
          ┌ 看多期货 (BUY)
          │  ├ IV Rank > 70 → 卖 Call (covered call), 赚高权利金
          │  ├ IV Rank < 30 → 买 Call (纯期权), 波动率低适合买方
          │  ├ Skew 极端负 → 用 Put 保护 (担心回调)
          │  └ 正常 → 直接做多期货
          │
          └ 看空期货 (SELL)
             ├ IV Rank > 70 → 卖 Put (cash-secured put)
             ├ IV Rank < 30 → 买 Put
             └ Skew 极端正 → 用 Call 保护 (担心反弹)
        """
        if futures_direction == "HOLD" or futures_confidence < 0.3:
            return ComboSignal(
                strategy_name="hold",
                futures_direction="FLAT",
                options_leg="none",
                adjusted_confidence=0.0,
                adjusted_direction="HOLD",
                reason="期货信号不足，不操作",
            )
        
        if not options_available:
            # 无期权市场，直接做期货
            return ComboSignal(
                strategy_name="futures_only",
                futures_direction="LONG" if futures_direction == "BUY" else "SHORT",
                options_leg="none",
                adjusted_confidence=futures_confidence,
                adjusted_direction=futures_direction,
                reason=f"无期权市场，直接{'做多' if futures_direction == 'BUY' else '做空'}期货",
            )
        
        return self._decide_strategy(
            futures_direction, futures_confidence,
            iv_rank, skew, spot, term_structure,
        )
    
    def _decide_strategy(
        self, direction, confidence, iv_rank, skew, spot, term_structure
    ) -> ComboSignal:
        """根据规则决策树选择最佳策略。"""
        
        if direction == "BUY":
            # 看多期货
            if iv_rank > 70:
                # IV 高 → 卖期权收权利金
                otm_pct = 0.03 if iv_rank > 85 else 0.05
                return ComboSignal(
                    strategy_name="covered_call",
                    futures_direction="LONG",
                    options_leg=f"SELL OTM Call (+{otm_pct*100:.0f}%)",
                    adjusted_confidence=confidence * 0.9,
                    adjusted_direction="BULLISH",
                    reason=f"IV Rank={iv_rank:.0f} 偏高, 卖Call收高权利金, 持仓增厚收益",
                    risk_notes="期货下跌风险未被对冲",
                )
            elif iv_rank < 30:
                # IV 低 → 买期权
                return ComboSignal(
                    strategy_name="long_call",
                    futures_direction="FLAT",  # 用期权替代期货
                    options_leg="BUY ATM Call",
                    adjusted_confidence=confidence * 0.85,
                    adjusted_direction="BULLISH",
                    reason=f"IV Rank={iv_rank:.0f} 偏低, 期权便宜, 用Call替代期货节省保证金",
                    risk_notes="时间价值衰减, 需要方向性行情配合",
                )
            elif skew < -0.08:
                # 偏度极端负 → 市场过度乐观 → 买Put保护
                return ComboSignal(
                    strategy_name="protective_put",
                    futures_direction="LONG",
                    options_leg=f"BUY OTM Put (skew={skew:.2f})",
                    adjusted_confidence=confidence * 0.8,
                    adjusted_direction="BULLISH (protected)",
                    reason=f"Skew={skew:.2f} 显示市场过度乐观, 买Put对冲回调风险",
                    risk_notes="保护成本 = 权利金",
                )
            else:
                # 正常 → 直接做多期货
                return ComboSignal(
                    strategy_name="futures_only",
                    futures_direction="LONG",
                    options_leg="none",
                    adjusted_confidence=confidence,
                    adjusted_direction="BULLISH",
                    reason="期权市场无异常信号, 直接做多期货",
                )
        
        else:  # SELL
            # 看空期货 (对称逻辑)
            if iv_rank > 70:
                return ComboSignal(
                    strategy_name="cash_secured_put",
                    futures_direction="SHORT",
                    options_leg="SELL OTM Put",
                    adjusted_confidence=confidence * 0.9,
                    adjusted_direction="BEARISH",
                    reason=f"IV Rank={iv_rank:.0f} 偏高, 卖Put收权利金",
                )
            elif iv_rank < 30:
                return ComboSignal(
                    strategy_name="long_put",
                    futures_direction="FLAT",
                    options_leg="BUY ATM Put",
                    adjusted_confidence=confidence * 0.85,
                    adjusted_direction="BEARISH",
                    reason=f"IV Rank={iv_rank:.0f} 偏低, 期权便宜, 用Put替代期货",
                )
            elif skew > 0.08:
                return ComboSignal(
                    strategy_name="protective_call",
                    futures_direction="SHORT",
                    options_leg="BUY OTM Call",
                    adjusted_confidence=confidence * 0.8,
                    adjusted_direction="BEARISH (protected)",
                    reason=f"Skew={skew:.2f} 显示市场恐慌, 买Call对冲反弹风险",
                )
            else:
                return ComboSignal(
                    strategy_name="futures_only",
                    futures_direction="SHORT",
                    options_leg="none",
                    adjusted_confidence=confidence,
                    adjusted_direction="BEARISH",
                    reason="期权市场无异常信号, 直接做空期货",
                )
    
    def compute_from_signals(
        self,
        futures_signal,
        options_signals: List,
    ) -> List[ComboSignal]:
        """
        从现有信号系统输入。
        
        Args:
            futures_signal: 来自 signals/engine.py 的期货信号
            options_signals: 来自 options/ 模块的期权信号列表
            
        Returns:
            联合策略建议列表
        """
        # 提取期货方向
        if hasattr(futures_signal, "direction"):
            fd = futures_signal.direction
        else:
            fd = "HOLD"
        
        fc = getattr(futures_signal, "confidence", 0.5)
        
        # 提取期权指标
        iv_rank = 50
        skew = 0.0
        for sig in options_signals:
            if hasattr(sig, "signal_type") and sig.signal_type == "IV_RANK":
                iv_rank = getattr(sig, "value", 50)
            if hasattr(sig, "signal_type") and sig.signal_type == "SKEW":
                skew = getattr(sig, "value", 0.0)
        
        combo = self.combine(
            futures_direction="BUY" if fd in ("BUY", "LONG") else
                        "SELL" if fd in ("SELL", "SHORT") else "HOLD",
            futures_confidence=fc,
            iv_rank=iv_rank,
            skew=skew,
            spot=0,
        )
        
        return [combo]
```

---

## B.5 测试验证（期权）

### B.5.1 test_options_surface.py

```python
"""期权曲面测试"""

import pytest
import numpy as np
from options.volatility.surface import VolSurface, build_surface_from_data


class TestVolSurface:
    def test_basic_surface(self):
        surface = VolSurface()
        surface.set_forward(100.0)
        for T, strikes, ivs in _sample_chain():
            surface.add_slice(T, strikes, ivs)
        surface.build()
        
        # 查询中间点
        iv = surface.get_iv(strike=100, T=0.3)
        assert iv is not None
        assert 0.1 < iv < 0.6
    
    def test_skew_calculation(self):
        surface = VolSurface()
        surface.set_forward(100.0)
        for T, strikes, ivs in _sample_chain():
            surface.add_slice(T, strikes, ivs)
        surface.build()
        
        skew = surface.get_skew(0.25)
        assert skew != 0.0
    
    def test_term_structure(self):
        surface = VolSurface()
        surface.set_forward(100.0)
        for T, strikes, ivs in _sample_chain():
            surface.add_slice(T, strikes, ivs)
        surface.build()
        
        ts = surface.get_term_structure(strike=100)
        assert len(ts) >= 2


class TestTermArbitrageSignals:
    def test_skew_extreme(self):
        """Skew 极端时产生信号"""
        pass  # 实际测试需构造数据


class TestFuturesCombo:
    def test_bull_high_iv(self):
        """看多 + IV高 → recommended covered call"""
        from options.strategies.futures_combo import FuturesOptionsComboSignals
        combo = FuturesOptionsComboSignals()
        sig = combo.combine("BUY", 0.8, iv_rank=85, skew=0.02, spot=100)
        assert sig.strategy_name == "covered_call"
    
    def test_bull_low_iv(self):
        """看多 + IV低 → recommended long call"""
        combo = FuturesOptionsComboSignals()
        sig = combo.combine("BUY", 0.8, iv_rank=20, skew=0.02, spot=100)
        assert sig.strategy_name == "long_call"
    
    def test_bull_extreme_skew(self):
        """看多 + skew极端负 → protective put"""
        combo = FuturesOptionsComboSignals()
        sig = combo.combine("BUY", 0.8, iv_rank=50, skew=-0.12, spot=100)
        assert sig.strategy_name == "protective_put"
    
    def test_low_confidence(self):
        """低置信度 → hold"""
        combo = FuturesOptionsComboSignals()
        sig = combo.combine("BUY", 0.2, iv_rank=50, skew=0, spot=100)
        assert sig.strategy_name == "hold"
```

---

## 验收标准

| # | 验收项 | 归属 | 验证方式 |
|---|--------|------|---------|
| 1 | 特征 Pipeline 产出 ≥ 20 个特征 | A | `pipe.compute_all(data).shape[1] >= 20` |
| 2 | 模型注册中心保存/加载正常 | A | `registry.save()` → `registry.load()` 返回一致 |
| 3 | 超参搜索三种方法均可用 | A | optuna/random/grid 各跑一次 |
| 4 | 模型集成 output shape 正确 | A | `ensemble.predict(X)` 与输入长度一致 |
| 5 | sklearn 包装器支持 6 种模型 | A | 6 种 model_type 均能 fit+predict |
| 6 | 全曲面插值后任意 (K,T) 可查 IV | B | 插值后 get_iv 不返回 None |
| 7 | 曲面偏度/曲率计算不崩溃 | B | skew/curvature 返回 float |
| 8 | 期限结构信号分类正确 | B | 三种信号类型都能产生 |
| 9 | 期货-期权联合策略决策树完整 | B | 5 种场景输出正确的 strategy_name |
| 10 | A/B 两篇测试全部通过 | AB | `pytest tests/unit/test_ml_*.py tests/unit/test_options_*.py -v` |
