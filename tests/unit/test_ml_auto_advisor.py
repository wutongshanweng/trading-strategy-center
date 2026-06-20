"""Phase4 B篇 ML自动迭代 + D篇 LLM建议器 测试。"""

import numpy as np
import pandas as pd
import tempfile

from ml.auto_pipeline import AutoMLPipeline
from ml.model_monitor import ModelMonitor
from ml.model_selector import ModelSelector
from ml.registry import ModelRegistry
from core.llm.strategy_advisor import LLMStrategyAdvisor


def _ohlcv(n=400, seed=0):
    rng = np.random.default_rng(seed)
    c = 100 + np.cumsum(rng.normal(0, 0.5, n))
    return pd.DataFrame({
        "open": c, "high": c * 1.01, "low": c * 0.99, "close": c,
        "volume": rng.integers(1e4, 1e5, n),
    }, index=pd.date_range("2024-01-01", periods=n, freq="D"))


class TestAutoMLPipeline:
    def test_run_returns_result(self):
        tmp = tempfile.mkdtemp()
        pipe = AutoMLPipeline(registry=ModelRegistry(tmp), horizon=5)
        r = pipe.run("TEST", data=_ohlcv(), candidate_types=["rf", "ridge"], n_trials=3)
        assert r.feature_count >= 20
        assert r.data_points > 0
        assert r.best_model_type in ("rf", "ridge")  # 验收4

    def test_registers_model(self):
        tmp = tempfile.mkdtemp()
        reg = ModelRegistry(tmp)
        AutoMLPipeline(registry=reg, horizon=5).run(
            "TEST", data=_ohlcv(), candidate_types=["ridge"], n_trials=2)
        assert any(m["name"] == "auto_TEST" for m in reg.list_models())


class TestModelMonitor:
    def test_detects_decay(self):
        mon = ModelMonitor(decay_threshold=-0.3)
        rng = np.random.default_rng(1)
        report = mon.check("m", rng.normal(size=50), rng.normal(size=50), baseline_ic=0.5)
        assert report.needs_retrain is True  # 验收5

    def test_healthy_no_retrain(self):
        mon = ModelMonitor(decay_threshold=-0.3)
        x = np.array([1, 2, 3, 4, 5, 6.0])
        report = mon.check("m", x, x, baseline_ic=0.9)
        assert report.needs_retrain is False


class TestModelSelector:
    def test_select_best(self):
        from ml.models.sklearn_wrapper import SklearnModel
        rng = np.random.default_rng(0)
        X = rng.normal(size=(120, 5)); y = X[:, 0] * 0.5 + rng.normal(0, 0.1, 120)
        m1 = SklearnModel("ridge").fit(X[:90], y[:90])
        m2 = SklearnModel("rf", {"n_estimators": 20}).fit(X[:90], y[:90])
        name, score = ModelSelector().select({"ridge": m1, "rf": m2}, X[90:], y[90:])
        assert name in ("ridge", "rf")

    def test_select_with_hyperopt(self):
        rng = np.random.default_rng(0)
        X = rng.normal(size=(150, 5)); y = X[:, 0] * 0.5 + rng.normal(0, 0.1, 150)
        mt, model, score, params = ModelSelector().select_with_hyperopt(
            ["ridge", "rf"], X[:110], y[:110], X[110:], y[110:], n_trials=3)
        assert mt in ("ridge", "rf") and model is not None


class TestLLMStrategyAdvisor:
    def test_ask_returns_nonempty(self):
        # 无有效 LLM key → 本地降级, 必返回非空 (验收7)
        adv = LLMStrategyAdvisor()
        out = adv.ask("推荐趋势策略", context={"regime": "trending"})
        assert isinstance(out, str) and len(out) > 0

    def test_generate_strategy(self):
        adv = LLMStrategyAdvisor()
        r = adv.generate_strategy("突破20日高点做多")
        assert "code" in r and r["source"] in ("llm", "template")
