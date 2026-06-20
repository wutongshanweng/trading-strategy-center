#!/usr/bin/env python3
"""
ML + 期权模块演示脚本。

一行命令跑完全部新功能:
    python -m ml.demo

展示: 特征工程 / 模型训练+注册 / 超参搜索 / 模型集成 /
      期权曲面 / 期权套利信号 / 期权-期货联合策略。
"""

import sys
import tempfile

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _make_sample_data(n: int = 500) -> pd.DataFrame:
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
    print("\n" + "=" * 60 + "\n  A. 特征工程 Pipeline\n" + "=" * 60)
    from ml.features.pipeline import FeaturePipeline
    from ml.features.technical_features import TechnicalFeatureSet

    data = _make_sample_data(500)
    pipe = FeaturePipeline()
    pipe.register_module(TechnicalFeatureSet())
    X = pipe.compute_all(data, normalize=True)
    print(f"  特征数: {len(X.columns)}  样本数: {len(X)}")
    print(f"  特征名: {list(X.columns[:5])}...")

    tmp = tempfile.gettempdir()
    pipe.save_config(f"{tmp}/demo_features.json")
    pipe2 = FeaturePipeline()
    pipe2.register_module(TechnicalFeatureSet())
    pipe2.load_config(f"{tmp}/demo_features.json")
    print(f"  Config 保存/加载: OK ({len(pipe2.get_feature_names())} 特征)")

    print("\n" + "=" * 60 + "\n  B. 模型注册中心 + sklearn 包装\n" + "=" * 60)
    from ml.models.sklearn_wrapper import SklearnModel
    from ml.registry import ModelRegistry

    y = data["close"].pct_change().shift(-1)
    X_train = X.loc[X.index.intersection(y.dropna().index)]
    y_train = y.loc[X_train.index]
    model = SklearnModel("rf", {"n_estimators": 50, "max_depth": 5})
    model.fit(X_train.values, y_train.values)
    print(f"  模型训练: OK  预测样例: {model.predict(X_train.values[:3]).round(5)}")

    reg = ModelRegistry(f"{tmp}/demo_models")
    meta = reg.save(model._model, "demo_rf", {
        "framework": "sklearn", "model_type": "regressor",
        "metric_name": "ic", "metric_value": 0.05,
        "symbol": "DEMO", "feature_count": X_train.shape[1]})
    reg.load("demo_rf")
    print(f"  模型注册: v{meta.version} → 加载: OK")

    print("\n" + "=" * 60 + "\n  C. 超参搜索\n" + "=" * 60)
    from ml.hyperopt import HyperoptSearcher

    def train_fn(params):
        m = SklearnModel("rf", params).fit(X_train.values[:200], y_train.values[:200])
        pred = m.predict(X_train.values[200:240])
        real = y_train.values[200:240]
        return float(np.corrcoef(pred, real)[0, 1]) if len(pred) > 1 else 0.0

    bp, bs = HyperoptSearcher().search(
        train_fn, {"n_estimators": (20, 100, "int"), "max_depth": (3, 10, "int")},
        n_trials=5, method="random")
    print(f"  超参搜索: {bp} → score={bs:.4f}")

    print("\n" + "=" * 60 + "\n  D. 模型集成\n" + "=" * 60)
    from ml.ensemble import ModelEnsemble
    m1 = SklearnModel("rf", {"n_estimators": 50}).fit(X_train.values, y_train.values)
    m2 = SklearnModel("ridge", {"alpha": 1.0}).fit(X_train.values, y_train.values)
    ens = ModelEnsemble("voting")
    ens.add_model(m1, 0.6)
    ens.add_model(m2, 0.4)
    print(f"  集成预测: {ens.predict(X_train.values[:3]).round(5)}  OK")


def demo_options():
    print("\n" + "=" * 60 + "\n  E. 期权波动率曲面\n" + "=" * 60)
    from options.volatility.surface import VolSurface
    surface = VolSurface()
    surface.set_forward(100.0)
    K = np.arange(80, 121, 5).astype(float)
    # 带明显偏斜的微笑 (put 端 IV 高 → skew 超阈值, 可触发 IV_SKEW 信号)
    for T, base in [(0.1, 0.20), (0.3, 0.22), (0.6, 0.25)]:
        surface.add_slice(T, K, base + 0.005 * (100 - K))
    surface.build()
    print(f"  曲面查询: IV(K=100,T=0.3)={surface.get_iv(100, 0.3):.4f}")
    print(f"  偏度: skew={surface.get_skew(0.3):.4f}  曲率={surface.get_curvature(0.3):.4f}")
    _, _, IV = surface.surface_to_grid(10, 5)
    print(f"  网格输出: {IV.shape}  OK")

    print("\n" + "=" * 60 + "\n  F. 期权套利信号\n" + "=" * 60)
    from options.strategies.term_arbitrage import TermArbitrageSignals
    sigs = TermArbitrageSignals().compute(surface, spot=100)
    if sigs:
        for s in sigs:
            print(f"  {s.signal_type}: {s.direction} (score={s.score:.2f})")
    else:
        print("  (当前曲面无异常, 无套利信号)")

    print("\n" + "=" * 60 + "\n  G. 期权-期货联合策略\n" + "=" * 60)
    from options.strategies.futures_combo import FuturesOptionsComboSignals
    combo = FuturesOptionsComboSignals()
    for name, d, conf, iv, sk in [
        ("看多+高IV", "BUY", 0.8, 85, 0.02),
        ("看多+低IV", "BUY", 0.8, 20, 0.02),
        ("看多+极端skew", "BUY", 0.8, 50, -0.12),
        ("看空+高IV", "SELL", 0.7, 80, 0.05),
        ("低置信度", "BUY", 0.2, 50, 0.0),
    ]:
        print(f"  {name}: → {combo.combine(d, conf, iv, sk, spot=100).strategy_name}")


if __name__ == "__main__":
    print("=" * 44)
    print("  Phase 3 功能演示 — ML + 期权")
    print("=" * 44)
    demo_ml()
    demo_options()
    print("\n" + "=" * 60 + "\n  全部演示完成 OK\n" + "=" * 60)
