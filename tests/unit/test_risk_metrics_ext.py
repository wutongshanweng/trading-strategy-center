"""empyrical 风险指标扩展 — 单测。

不触网/不触库。验证全套指标计算 + numpy2.0 兼容 + 容错。
"""

import numpy as np

from backtest.risk_metrics_ext import full_metrics, is_available


class TestFullMetrics:
    def test_available(self):
        assert is_available() is True  # empyrical 已安装

    def test_full_suite_keys(self):
        np.random.seed(1)
        r = np.random.normal(0.001, 0.02, 252).tolist()
        m = full_metrics(r)
        assert m["available"] is True
        for k in ("sharpe", "sortino", "calmar", "omega", "max_drawdown",
                  "tail_ratio", "stability", "value_at_risk", "annual_return"):
            assert k in m
            assert isinstance(m[k], float)

    def test_with_factor_returns(self):
        np.random.seed(2)
        r = np.random.normal(0.001, 0.02, 200).tolist()
        f = np.random.normal(0.0008, 0.018, 200).tolist()
        m = full_metrics(r, factor_returns=f)
        assert "alpha" in m and "beta" in m and "excess_sharpe" in m

    def test_insufficient_samples(self):
        m = full_metrics([0.01])
        assert m["available"] is False

    def test_handles_nan_inf(self):
        r = [0.01, float("nan"), 0.02, float("inf"), -0.01] + [0.005] * 50
        m = full_metrics(r)
        assert m["available"] is True
        assert np.isfinite(m["sharpe"])
