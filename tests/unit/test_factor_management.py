"""Unit tests for the factor management system."""

import numpy as np
import pandas as pd
import pytest

from core.alpha.management import (
    FactorMonitoring,
    FactorRetirement,
    FactorStore,
    FactorVersioning,
)


def _make_series(n: int = 100) -> pd.Series:
    np.random.seed(42)
    return pd.Series(np.random.randn(n), name="test_factor")


class TestFactorStore:
    def test_save_and_load(self):
        store = FactorStore(":memory:")
        data = _make_series()
        store.save_factor("my_factor", data, {"description": "test"})
        loaded = store.load_factor("my_factor")
        assert len(loaded) == len(data)
        np.testing.assert_array_almost_equal(data.values, loaded.values)
        store.close()

    def test_versioning(self):
        store = FactorStore(":memory:")
        d1 = _make_series(100)
        d2 = _make_series(100)
        v1 = store.save_factor("f", d1)
        v2 = store.save_factor("f", d2)
        assert v1 == 1
        assert v2 == 2
        store.close()

    def test_load_specific_version(self):
        store = FactorStore(":memory:")
        d1 = pd.Series([1.0, 2.0, 3.0])
        d2 = pd.Series([4.0, 5.0, 6.0])
        store.save_factor("f", d1)
        store.save_factor("f", d2)
        loaded = store.load_factor("f", version=1)
        assert len(loaded) == 3
        np.testing.assert_array_almost_equal(d1.values, loaded.values)
        store.close()

    def test_deactivate_factor(self):
        store = FactorStore(":memory:")
        store.save_factor("f", _make_series())
        store.deactivate_factor("f")
        with pytest.raises(ValueError, match="not found"):
            store.load_factor("f")
        store.close()

    def test_factor_history(self):
        store = FactorStore(":memory:")
        for _ in range(5):
            store.save_factor("f", _make_series())
        history = store.get_factor_history("f")
        assert len(history) == 5
        assert history[0]["version"] >= 1
        assert history[0]["version"] <= 5
        store.close()

    def test_load_nonexistent(self):
        store = FactorStore(":memory:")
        with pytest.raises(ValueError, match="not found"):
            store.load_factor("nonexistent")
        store.close()


class TestFactorVersioning:
    def test_create_version(self):
        store = FactorStore(":memory:")
        versioning = FactorVersioning(store)
        v = versioning.create_version("f", _make_series(), "initial")
        assert v == 1
        store.close()

    def test_compare_versions(self):
        store = FactorStore(":memory:")
        versioning = FactorVersioning(store)
        d1 = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        d2 = pd.Series([1.1, 2.1, 3.1, 4.1, 5.1])
        versioning.create_version("f", d1, "v1")
        versioning.create_version("f", d2, "v2")
        comp = versioning.compare_versions("f", 1, 2)
        assert "correlation" in comp
        assert comp["correlation"] > 0.9
        store.close()


class TestFactorMonitoring:
    def test_monitor_existing_factor(self):
        store = FactorStore(":memory:")
        store.save_factor("f", _make_series())
        monitoring = FactorMonitoring(store)
        result = monitoring.monitor_factor("f")
        assert result["status"] == "normal"
        assert "metrics" in result
        store.close()

    def test_monitor_empty_factor(self):
        store = FactorStore(":memory:")
        monitoring = FactorMonitoring(store)
        result = monitoring.monitor_factor("nonexistent")
        assert result["status"] == "no_data"
        store.close()


class TestFactorRetirement:
    def test_no_retirement_for_new_factor(self):
        store = FactorStore(":memory:")
        store.save_factor("f", _make_series())
        monitoring = FactorMonitoring(store)
        retirement = FactorRetirement(store, monitoring, min_versions=5)
        assert retirement.check_retirement("f") is False
        store.close()

    def test_retire_inactive_factor(self):
        store = FactorStore(":memory:")
        monitoring = FactorMonitoring(store)
        retirement = FactorRetirement(store, monitoring)
        assert retirement.check_retirement("nonexistent") is True
        store.close()

    def test_retire_deactivates_factor(self):
        store = FactorStore(":memory:")
        store.save_factor("f", _make_series())
        monitoring = FactorMonitoring(store)
        retirement = FactorRetirement(store, monitoring, min_versions=1)
        retirement.retire("f", "test_reason")
        with pytest.raises(ValueError):
            store.load_factor("f")
        store.close()


# ═══ Phase2: 因子衰减检测 / 行业中性化 / 研究报告 (Spec §7.2) ═══

from core.alpha.management import (  # noqa: E402
    FactorDecayDetector, FactorHealth, IndustryNeutralizer, FactorReportGenerator,
)


class TestFactorDecay:
    def test_healthy_factor(self):
        np.random.seed(42)
        ic = pd.Series(np.random.normal(0.05, 0.01, 200))
        assert FactorDecayDetector().check("h", ic).health == FactorHealth.HEALTHY

    def test_decayed_factor(self):
        np.random.seed(1)
        ic = pd.Series(np.linspace(0.08, -0.01, 200) + np.random.normal(0, 0.004, 200))
        assert FactorDecayDetector().check("d", ic).health == FactorHealth.DECAYED

    def test_batch_check(self):
        m = {"a": pd.Series(np.random.normal(0.05, 0.01, 100)), "b": pd.Series(np.zeros(100))}
        out = FactorDecayDetector().batch_check(m)
        assert set(out.keys()) == {"a", "b"}


class TestIndustryNeutralizer:
    def test_neutralize_by_mean(self):
        np.random.seed(0)
        f = pd.Series(np.random.randn(100)); f[:40] += 0.5
        ind = pd.Series(["A"] * 40 + ["B"] * 30 + ["C"] * 30)
        neu = IndustryNeutralizer().neutralize_by_mean(f, ind)
        for i in ["A", "B", "C"]:
            assert abs(neu[ind == i].mean()) < 0.1

    def test_neutralize_by_zscore(self):
        np.random.seed(0)
        f = pd.Series(np.random.randn(60))
        ind = pd.Series(["A"] * 30 + ["B"] * 30)
        assert len(IndustryNeutralizer().neutralize_by_zscore(f, ind)) == 60

    def test_neutralize_by_regression(self):
        np.random.seed(0)
        f = pd.Series(np.random.randn(90)); f[:30] += 1.0
        ind = pd.Series(["A"] * 30 + ["B"] * 30 + ["C"] * 30)
        neu = IndustryNeutralizer().neutralize_by_regression(f, ind)
        assert abs(neu[ind == "A"].mean()) < 0.1


class TestFactorReport:
    def test_generate_report(self):
        np.random.seed(7)
        n = 300
        ret = pd.Series(np.random.randn(n) * 0.02)
        fdf = pd.DataFrame({
            "f_good": ret * 5 + np.random.randn(n) * 0.5,
            "f_noise": pd.Series(np.random.randn(n)),
        })
        rep = FactorReportGenerator().generate(fdf, ret, top_n=10)
        assert rep.total_factors == 2
        assert rep.top_factors[0].name == "f_good"
