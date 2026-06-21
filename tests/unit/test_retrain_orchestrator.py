"""重训编排器 (阶段3) — 单测。

不触 DuckDB: 测模型层漂移检测 + 各层缺输入时的跳过逻辑。
"""

import numpy as np

from core.adaptive.retrain_orchestrator import RetrainOrchestrator, RetrainReport


class TestModelLayer:
    def test_healthy_model_no_retrain(self):
        orch = RetrainOrchestrator()
        # 预测与实际高度相关 → IC 高, 不需重训
        actuals = np.linspace(-1, 1, 50)
        preds = actuals + np.random.normal(0, 0.05, 50)
        checked, retrained = orch.check_models(
            {"model_RB": (preds, actuals, 0.9)}, auto_retrain=False)
        assert len(checked) == 1
        assert retrained == []

    def test_degraded_model_flagged(self):
        orch = RetrainOrchestrator()
        # 预测与实际反相关, baseline 高 → IC 大幅衰减
        actuals = np.linspace(-1, 1, 50)
        preds = -actuals + np.random.normal(0, 0.05, 50)
        checked, _ = orch.check_models(
            {"model_RB": (preds, actuals, 0.8)}, auto_retrain=False)
        assert checked[0]["needs_retrain"] is True

    def test_no_eval_data_skips(self):
        orch = RetrainOrchestrator()
        checked, retrained = orch.check_models(None)
        assert checked == [] and retrained == []


class TestFactorLayer:
    def test_no_ic_skips(self):
        orch = RetrainOrchestrator()
        assert orch.check_factor_health(None) == []


class TestCycleSkips:
    def test_cycle_skips_missing_layers(self):
        orch = RetrainOrchestrator()
        # 不提供任何输入 → 三层全跳过, 但应返回结构完整的报告
        report = orch.run_cycle(strategy_names=None, ic_series_map=None, model_eval_data=None)
        assert isinstance(report, RetrainReport)
        assert len(report.notes) == 3  # 三层各一条跳过说明
        d = report.to_dict()
        assert "param_optimized" in d and "factor_health" in d and "models_checked" in d
