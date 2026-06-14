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
