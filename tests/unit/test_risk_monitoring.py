"""Unit tests for risk monitoring and position management."""

import numpy as np
import pandas as pd
import pytest


class TestVaRCalculator:
    def test_historical(self):
        from core.risk.monitoring.var_calculator import VaRCalculator
        returns = pd.Series(np.random.randn(1000) * 0.01)
        calc = VaRCalculator(confidence=0.95)
        var = calc.historical(returns)
        assert var > 0

    def test_parametric(self):
        from core.risk.monitoring.var_calculator import VaRCalculator
        returns = pd.Series(np.random.randn(1000) * 0.01)
        calc = VaRCalculator(confidence=0.95)
        var = calc.parametric(returns)
        assert var > 0

    def test_monte_carlo(self):
        from core.risk.monitoring.var_calculator import VaRCalculator
        np.random.seed(42)
        returns = pd.Series(np.random.randn(1000) * 0.01)
        calc = VaRCalculator(confidence=0.95)
        var = calc.monte_carlo(returns, n_sims=5000)
        assert isinstance(var, float)


class TestCVaRCalculator:
    def test_calculate(self):
        from core.risk.monitoring.cvar_calculator import CVaRCalculator
        returns = pd.Series(np.random.randn(1000) * 0.01)
        calc = CVaRCalculator(confidence=0.95)
        cvar = calc.calculate(returns)
        assert cvar > 0


class TestStressTesting:
    def test_hypothetical(self):
        from core.risk.monitoring.stress_testing import StressTesting
        portfolio = {"AAPL": {"value": 100000, "beta": 1.2}, "GOOG": {"value": 50000, "beta": 0.8}}
        st = StressTesting(portfolio)
        scenarios = st.hypothetical_scenarios()
        assert len(scenarios) > 0
        assert any(s["name"] == "Market Drop 20%" for s in scenarios)

    def test_reverse_stress_test(self):
        from core.risk.monitoring.stress_testing import StressTesting
        portfolio = {"AAPL": {"value": 100000, "beta": 1.2}}
        st = StressTesting(portfolio)
        results = st.reverse_stress_test(0.05)
        assert len(results) > 0


class TestRiskAttribution:
    def test_factor_attribution(self):
        from core.risk.monitoring.risk_attribution import RiskAttribution
        ra = RiskAttribution()
        result = ra.factor_attribution({"market": 0.5, "size": 0.3}, {"market": 0.02, "size": 0.01})
        assert "total" in result
        assert abs(result["total"] - 0.013) < 1e-6

    def test_brinson_attribution(self):
        from core.risk.monitoring.risk_attribution import RiskAttribution
        ra = RiskAttribution()
        result = ra.brinson_attribution(
            port_weights={"A": 0.6, "B": 0.4},
            bench_weights={"A": 0.5, "B": 0.5},
            port_returns={"A": 0.1, "B": 0.05},
            bench_returns={"A": 0.08, "B": 0.04},
        )
        assert "allocation" in result
        assert "selection" in result
        assert "interaction" in result


class TestKellyCriterion:
    def test_calculate(self):
        from core.risk.position.kelly_criterion import KellyCriterion
        k = KellyCriterion()
        f = k.calculate(win_rate=0.6, win_loss_ratio=2.0)
        assert 0 < f <= 0.5

    def test_fractional(self):
        from core.risk.position.kelly_criterion import KellyCriterion
        k = KellyCriterion()
        f = k.fractional(win_rate=0.6, win_loss_ratio=2.0, fraction=0.5)
        assert 0 < f <= 0.25


class TestVolatilityTargeting:
    def test_calculate(self):
        from core.risk.position.volatility_targeting import VolatilityTargeting
        vt = VolatilityTargeting(target_vol=0.15)
        returns = np.random.randn(100) * 0.01
        size = vt.calculate_position_size(returns)
        assert 0.1 <= size <= 2.0

    def test_adjust(self):
        from core.risk.position.volatility_targeting import VolatilityTargeting
        vt = VolatilityTargeting(target_vol=0.15)
        returns = np.random.randn(100) * 0.01
        new_size = vt.adjust_position(1.0, returns)
        assert isinstance(new_size, float)


class TestRegimeBasedPosition:
    def test_regimes(self):
        from core.risk.position.regime_based import RegimeBasedPosition
        rb = RegimeBasedPosition()
        assert rb.get_position_size("TRENDING") == 1.2
        assert rb.get_position_size("CRISIS") == 0.2
        assert rb.get_position_size("QUIET") == 1.0
        assert rb.get_position_size("UNKNOWN") == 1.0
