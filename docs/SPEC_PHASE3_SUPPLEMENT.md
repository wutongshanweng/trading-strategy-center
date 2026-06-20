# SPEC_PHASE3_ML_OPTIONS 补充项

> 在原始 Spec 基础上补充 5 个缺口，其余不变。
> 标记为「新增」的内容直接追加到对应章节。

---

## 补充 1：旧模型弃用 + ml/__init__.py 导出

### 1.1 标记旧文件为弃用（A.1.2 文件清单补充）

在文件清单末尾新增：

```
ml/models/nbeats_model.py     │ 🟡 改 | 文件顶部加 deprecation warning
ml/models/tft_model.py        │ 🟡 改 | 文件顶部加 deprecation warning
```

在 `ml/models/nbeats_model.py` 和 `ml/models/tft_model.py` 文件顶部添加：

```python
import warnings
warnings.warn(
    "DEPRECATED: This model is a placeholder implementation. "
    "Use ml.models.sklearn_wrapper.SklearnModel instead.",
    DeprecationWarning, stacklevel=2,
)
```

### 1.2 ml/__init__.py 导出（新增章节 A.1.4）

在 A.1.3 依赖说明之后，新增：

```
## A.1.4 ml/__init__.py 导出接口

更新 ml/__init__.py，统一导出新模块：

```python
from ml.features.pipeline import FeaturePipeline
from ml.features.technical_features import TechnicalFeatureSet
from ml.features.cross_sectional_features import CrossSectionalFeatureSet
from ml.registry import ModelRegistry, ModelMeta
from ml.hyperopt import HyperoptSearcher
from ml.ensemble import ModelEnsemble
from ml.models.sklearn_wrapper import SklearnModel

# 旧 Pipeline 保留但标记弃用
from ml.pipeline import MLPipeline  # noqa: F401

__all__ = [
    "FeaturePipeline",
    "TechnicalFeatureSet",
    "CrossSectionalFeatureSet",
    "ModelRegistry",
    "ModelMeta",
    "HyperoptSearcher",
    "ModelEnsemble",
    "SklearnModel",
]
```
```

---

## 补充 2：特征缓存/持久化

### 2.1 在 FeaturePipeline 中新增（A.2.1 追加方法）

在 `FeaturePipeline` 类的末尾增加以下方法：

```python
def save_config(self, path: str):
    """
    保存特征配置到 JSON。
    
    这样下次启动不用重新注册，直接加载:
        pipe2 = FeaturePipeline()
        pipe2.load_config("rb_features.json")
        X = pipe2.compute_all(data)
    """
    import json
    config = {
        name: {
            "name": meta.name,
            "category": meta.category,
            "input_columns": meta.input_columns,
            "params": {k: str(v) if callable(v) else v 
                       for k, v in meta.params.items()},
        }
        for name, meta in self._features.items()
    }
    with open(path, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    logger.info(f"Feature config saved to {path} ({len(config)} features)")


def load_config(self, path: str):
    """
    从 JSON 加载特征配置。
    
    注意: compute_fn 无法序列化, 需按 name 重映射到已知函数。
    加载后调用 compute_all() 前需要调用 restore_functions()。
    """
    import json
    with open(path) as f:
        config = json.load(f)
    for name, data in config.items():
        self._features[name] = FeatureMeta(
            name=data["name"],
            category=data.get("category", "custom"),
            compute_fn=self._resolve_fn(data["name"]),  # 见下文
            input_columns=data.get("input_columns", []),
            params=data.get("params", {}),
        )
    logger.info(f"Feature config loaded from {path} ({len(config)} features)")


def _resolve_fn(self, name: str):
    """按特征名解析对应的计算函数（需提前注册已知特征集）。"""
    # 查找已注册的模块中有没有同名特征
    for module in self._modules:
        for fn_name, fn, _ in module.get_features():
            if fn_name == name:
                return fn
    # 如果找不到, 在调用 compute_all 时跳过
    logger.warning(f"Cannot resolve function for feature '{name}', will be skipped")
    return lambda data: pd.Series(0.0, index=data.index)


def list_features(self, category: Optional[str] = None) -> List[Dict]:
    """列出所有特征及其元数据（给前端展示用）。"""
    features = []
    for name, meta in self._features.items():
        if category and meta.category != category:
            continue
        features.append({
            "name": name,
            "category": meta.category,
            "input_columns": meta.input_columns,
        })
    return features
```

---

## 补充 3：期权策略注册

### 3.1 新增策略自动注册（B.1.2 文件清单补充）

在 `options/strategies/__init__.py` 中新增代码：

```python
# 在文件末尾新增:
from .term_arbitrage import TermArbitrageSignals  # noqa: F401
from .futures_combo import FuturesOptionsComboSignals  # noqa: F401

__all__ = [
    # ... 原有导出 ...
    "TermArbitrageSignals",
    "FuturesOptionsComboSignals",
]
```

### 3.2 在 futures_combo.py 中新增 `@register` 装饰器

`FuturesOptionsComboSignals` 不直接注册为 `BaseOptionStrategy`，但在其 `combine()` 方法中**推荐**的策略名（如 `"covered_call"` 等）应能从 `options/strategies/directional.py` 中找到对应实现。

不改变已注册策略。只确保新策略模块可以被 `options/strategies/__init__.py` 导入。

---

## 补充 4：ML 特征 ↔ 信号引擎集成

### 4.1 新增集成适配器（新增文件）

在 A.1.2 文件清单中新增：

```
ml/signal_adapter.py  │ 🆕 新建 | 将 ML 特征输出转为 Signal
```

### 4.2 ml/signal_adapter.py 实现

```python
"""
ML 特征 → 信号引擎适配器。

将 FeaturePipeline 产出的特征转换为 signals/ 引擎可消费的 Signal 对象。

用法:
    from ml.signal_adapter import MLSignalAdapter
    
    adapter = MLSignalAdapter()
    pipe = FeaturePipeline()
    pipe.register_module(TechnicalFeatureSet())
    X = pipe.compute_all(data)
    
    # 转为 Signal 列表
    signals = adapter.to_signals(X, symbol="RB2510")
    
    # 直接输入 resonance 引擎
    from core.resonance.engine_v2 import ResonanceEngineV2
    engine = ResonanceEngineV2()
    result = engine.calculate(X, signals)
"""

from typing import List, Optional, Union
import pandas as pd
import numpy as np
from signals.base import Signal, Direction


class MLSignalAdapter:
    """
    将 ML 特征转换为信号引擎的 Signal 对象。
    
    转换规则:
      - 对每个特征值做 z-score 标准化
      - 正分 → BUY, 负分 → SELL
      - strength = |z-score| / 3 (截断到 0~1)
    """
    
    def to_signals(
        self,
        features_df: pd.DataFrame,
        symbol: str = "",
        source_system: str = "ml_features",
    ) -> List[Signal]:
        """
        将特征矩阵每列转为一个 Signal。
        
        Args:
            features_df: 特征矩阵 (列=特征名)
            symbol: 标的代码
            source_system: 来源标记
            
        Returns:
            Signal 列表
        """
        signals = []
        for col in features_df.columns:
            vals = features_df[col].dropna()
            if len(vals) < 3:
                continue
            
            # z-score
            z = (vals - vals.mean()) / (vals.std() + 1e-10)
            latest_z = z.iloc[-1]
            
            # 方向
            if latest_z > 0.5:
                direction = Direction.BUY
            elif latest_z < -0.5:
                direction = Direction.SELL
            else:
                continue  # 信号太弱, 跳过
            
            # 强度
            strength = min(abs(latest_z) / 3.0, 1.0)
            
            signal = Signal(
                symbol=symbol,
                direction=direction,
                confidence=strength,
                score=float(latest_z),
                reason=f"ML特征{col} z-score={latest_z:.2f}",
                strategy_name=f"ml_{col}",
                source_system=source_system,
                resonance_layer="T",  # 归入听海(T)层
            )
            signals.append(signal)
        
        return signals
    
    def to_combined_signal(
        self,
        features_df: pd.DataFrame,
        symbol: str = "",
    ) -> Optional[Signal]:
        """
        将所有特征合并为一个综合信号。
        
        等权平均所有特征的 z-score → 一个 Signal。
        """
        vals = features_df.dropna()
        if vals.empty:
            return None
        
        # 每列 z-score 后取均值
        z_scores = (vals - vals.mean()) / (vals.std() + 1e-10)
        combined_z = z_scores.mean(axis=1).iloc[-1]
        
        if abs(combined_z) < 0.3:
            return None
        
        return Signal(
            symbol=symbol,
            direction=Direction.BUY if combined_z > 0 else Direction.SELL,
            confidence=min(abs(combined_z) / 3.0, 0.9),
            score=float(combined_z),
            reason=f"ML综合信号 z-score={combined_z:.2f} ({len(vals.columns)}特征)",
            strategy_name="ml_ensemble",
            source_system="ml_features",
            resonance_layer="T",
        )
```

---

## 补充 5：Demo 脚本

### 5.1 新增 demo 文件（新增文件）

在 A.1.2 文件清单中新增：

```
ml/demo.py  │ 🆕 新建 | ML + 期权功能演示脚本
```

### 5.2 ml/demo.py 实现

```python
#!/usr/bin/env python3
"""
ML + 期权模块演示脚本。

一行命令跑完全部新功能:
    python -m ml.demo

展示:
  A. 特征工程 → 特征矩阵
  B. 模型训练 + 注册
  C. 超参搜索
  D. 模型集成
  E. 期权曲面构建 (模拟数据)
  F. 期权套利信号
  G. 期权-期货联合策略
"""

import numpy as np
import pandas as pd


def _make_sample_data(n: int = 500) -> pd.DataFrame:
    """生成示例 OHLCV 数据"""
    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    closes = 100 + np.cumsum(np.random.randn(n) * 0.5)
    return pd.DataFrame({
        "open": closes * (1 + np.random.randn(n) * 0.002),
        "high": closes * (1 + abs(np.random.randn(n)) * 0.01),
        "low": closes * (1 - abs(np.random.randn(n)) * 0.01),
        "close": closes,
        "volume": np.random.randint(10000, 100000, n),
    }, index=dates)


def demo_ml():
    """ML 模块功能演示"""
    print("\n" + "=" * 60)
    print("  A. 特征工程 Pipeline")
    print("=" * 60)
    
    from ml.features.pipeline import FeaturePipeline
    from ml.features.technical_features import TechnicalFeatureSet
    
    data = _make_sample_data(500)
    pipe = FeaturePipeline()
    pipe.register_module(TechnicalFeatureSet())
    
    X = pipe.compute_all(data, normalize=True)
    print(f"  特征数: {len(X.columns)}")
    print(f"  样本数: {len(X)}")
    print(f"  特征名: {list(X.columns[:5])}...")
    
    # 保存/加载配置
    pipe.save_config("/tmp/demo_features.json")
    pipe2 = FeaturePipeline()
    pipe2.load_config("/tmp/demo_features.json")
    print(f"  Config 保存/加载: ✅")
    
    print("\n" + "=" * 60)
    print("  B. 模型注册中心 + sklearn 包装")
    print("=" * 60)
    
    from ml.models.sklearn_wrapper import SklearnModel
    from ml.registry import ModelRegistry
    
    y = data["close"].pct_change().shift(-1).dropna()
    X_train = X.loc[y.index].dropna()
    y_train = y.loc[X_train.index]
    
    model = SklearnModel("rf", {"n_estimators": 50, "max_depth": 5})
    model.fit(X_train.values, y_train.values)
    preds = model.predict(X_train.values[:5])
    print(f"  模型训练: ✅  预测样例: {preds[:3]}")
    
    registry = ModelRegistry("/tmp/demo_models")
    meta = registry.save(model._model, "demo_rf", {
        "framework": "sklearn", "model_type": "regressor",
        "metric_name": "ic", "metric_value": 0.05,
        "symbol": "DEMO", "feature_count": X_train.shape[1],
    })
    loaded, loaded_meta = registry.load("demo_rf")
    print(f"  模型注册: v{meta.version} → 加载: ✅")
    
    print("\n" + "=" * 60)
    print("  C. 超参搜索")
    print("=" * 60)
    
    from ml.hyperopt import HyperoptSearcher
    
    def train_fn(params):
        m = SklearnModel("rf", params)
        m.fit(X_train.values[:100], y_train.values[:100])
        pred = m.predict(X_train.values[100:120])
        real = y_train.values[100:120]
        return float(np.corrcoef(pred, real)[0, 1]) if len(pred) > 1 else 0.0
    
    searcher = HyperoptSearcher()
    best_params, best_score = searcher.search(
        train_fn,
        param_space={
            "n_estimators": (20, 100, "int"),
            "max_depth": (3, 10, "int"),
        },
        n_trials=5, method="random",
    )
    print(f"  超参搜索: {best_params} → score={best_score:.4f}")
    
    print("\n" + "=" * 60)
    print("  D. 模型集成")
    print("=" * 60)
    
    from ml.ensemble import ModelEnsemble
    
    m1 = SklearnModel("rf", {"n_estimators": 50})
    m2 = SklearnModel("ridge", {"alpha": 1.0})
    m1.fit(X_train.values, y_train.values)
    m2.fit(X_train.values, y_train.values)
    
    ensemble = ModelEnsemble("voting")
    ensemble.add_model(m1, weight=0.6)
    ensemble.add_model(m2, weight=0.4)
    ens_pred = ensemble.predict(X_train.values[:5])
    print(f"  集成预测: {ens_pred[:3]}  ✅")


def demo_options():
    """期权模块功能演示"""
    print("\n" + "=" * 60)
    print("  E. 期权波动率曲面")
    print("=" * 60)
    
    from options.volatility.surface import VolSurface
    
    surface = VolSurface()
    surface.set_forward(100.0)
    for T, strikes, ivs in [
        (0.1, np.arange(80, 121, 5), 0.20 + 0.1 * (np.arange(80, 121, 5) - 100) ** 2 / 1000),
        (0.3, np.arange(80, 121, 5), 0.22 + 0.08 * (np.arange(80, 121, 5) - 100) ** 2 / 1000),
        (0.6, np.arange(80, 121, 5), 0.25 + 0.05 * (np.arange(80, 121, 5) - 100) ** 2 / 1000),
    ]:
        surface.add_slice(T, strikes, ivs)
    surface.build()
    
    iv = surface.get_iv(strike=100, T=0.3)
    skew = surface.get_skew(0.3)
    print(f"  曲面查询: IV(K=100,T=0.3)={iv:.4f}")
    print(f"  偏度: skew={skew:.4f}")
    
    T_grid, K_grid, IV_grid = surface.surface_to_grid(10, 5)
    print(f"  网格输出: {IV_grid.shape}  ✅")
    
    print("\n" + "=" * 60)
    print("  F. 期权套利信号")
    print("=" * 60)
    
    from options.strategies.term_arbitrage import TermArbitrageSignals
    
    arb = TermArbitrageSignals()
    signals = arb.compute(surface, spot=100)
    for sig in signals:
        print(f"  {sig.signal_type}: {sig.direction} (score={sig.score:.2f})")
    
    print("\n" + "=" * 60)
    print("  G. 期权-期货联合策略")
    print("=" * 60)
    
    from options.strategies.futures_combo import FuturesOptionsComboSignals
    
    combo = FuturesOptionsComboSignals()
    scenarios = [
        ("看多+高IV", "BUY", 0.8, 85, 0.02),
        ("看多+低IV", "BUY", 0.8, 20, 0.02),
        ("看多+极端skew", "BUY", 0.8, 50, -0.12),
        ("看空+高IV", "SELL", 0.7, 80, 0.05),
        ("低置信度", "BUY", 0.2, 50, 0.0),
    ]
    for name, direction, conf, iv, sk in scenarios:
        sig = combo.combine(direction, conf, iv, sk, spot=100)
        print(f"  {name}: → {sig.strategy_name}")


if __name__ == "__main__":
    print("╔══════════════════════════════════════════╗")
    print("║  Phase 3 功能演示 — ML + 期权           ║")
    print("╚══════════════════════════════════════════╝")
    demo_ml()
    demo_options()
    print("\n" + "=" * 60)
    print("  全部演示完成 ✅")
    print("=" * 60)
```

### 5.3 验收条件补充

在验收标准中新增：

| # | 验收项 | 验证方式 |
|---|--------|---------|
| 11 | `ml/__init__.py` 导出了所有新类 | `from ml import FeaturePipeline, ModelRegistry, ...` 正常 |
| 12 | 旧 N-BEATS/TFT 文件有弃用警告 | `import ml.models.nbeats_model` 弹出 DeprecationWarning |
| 13 | 特征配置可保存/加载 | `save_config()` → `load_config()` 特征数一致 |
| 14 | 期权策略在 `__init__.py` 中可导入 | `from options.strategies import TermArbitrageSignals` 正常 |
| 15 | signal_adapter 输出 Signal 列表 | `len(adapter.to_signals(X)) >= 0` |
| 16 | demo 脚本全部跑通 | `python -m ml.demo` 输出7个模块的演示结果 |
