"""晋升闸门 (阶段2) — 单测。

不触 DuckDB: 只测参数空间构建 + 裁决 dataclass + 闸门判定逻辑。
"""

import pandas as pd
import numpy as np

from core.adaptive.promotion_gate import _build_param_space, _detect_regime, PromotionVerdict
from core.adaptive.walk_forward_validator import WalkForwardValidator, ValidationReport, WindowResult


class TestParamSpace:
    def test_builds_from_numeric_params(self):
        spaces, base = _build_param_space("trend_ma_cross")
        names = {s.name for s in spaces}
        # trend_ma_cross 有 fast/slow 两个数值参数
        assert "fast" in names or "slow" in names
        for s in spaces:
            assert s.low < s.high
            assert s.low >= 1.0

    def test_unknown_strategy_empty(self):
        spaces, base = _build_param_space("__nope__")
        assert spaces == [] and base == {}


class TestRegimeDetect:
    def test_handles_inf_nan(self):
        # 构造含 0 价 (pct_change 产生 inf) 的序列, 不应抛异常
        close = [100, 0, 50, 55, 60] + list(np.linspace(60, 80, 50))
        df = pd.DataFrame({"close": close})
        regime = _detect_regime(df)
        assert isinstance(regime, str)  # 不抛异常, 返回标签或 UNKNOWN

    def test_short_series_unknown(self):
        df = pd.DataFrame({"close": [100, 101, 102]})
        assert _detect_regime(df) == "UNKNOWN"


class TestGateDecision:
    def _report(self, mean_deg, overfit_ratio, mean_oos):
        w = WindowResult(0, 0, 80, 80, 100, 0.5, mean_oos, {})
        rep = ValidationReport(n_windows=1, mean_oos_score=mean_oos, std_oos_score=0.1,
                               mean_degradation=mean_deg, overfit_ratio=overfit_ratio,
                               windows=[w])
        return rep

    def test_robust_passes_checks(self):
        v = WalkForwardValidator()
        rep = self._report(mean_deg=-0.1, overfit_ratio=0.1, mean_oos=0.8)
        assert v.check_robustness(rep) is True
        assert v.detect_overfitting(rep) is False

    def test_overfit_detected(self):
        v = WalkForwardValidator()
        rep = self._report(mean_deg=-0.5, overfit_ratio=0.6, mean_oos=0.2)
        assert v.detect_overfitting(rep) is True
        assert v.check_robustness(rep) is False

    def test_verdict_to_dict(self):
        verdict = PromotionVerdict("s", "RB2510", True, "通过", mean_oos_sharpe=1.2, regime="TRENDING")
        d = verdict.to_dict()
        assert d["passed"] is True and d["regime"] == "TRENDING"
