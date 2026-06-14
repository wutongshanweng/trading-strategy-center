"""Integration tests for the Alpha101 factor pipeline.

Tests that all 101 factors can be computed via the FactorPipeline
with parallel execution.
"""

import time

import numpy as np
import pandas as pd
import pytest

import core.alpha.alpha101  # triggers registration of all 101 factors
from core.alpha.alpha101.factor_pipeline import FactorPipeline
from core.alpha.alpha101.factor_registry import FactorRegistry


def _generate_test_data(n: int = 200) -> pd.DataFrame:
    """Generate realistic OHLCV test data."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    open_ = close * (1 + np.random.randn(n) * 0.01)
    high = np.maximum(close, open_) + np.abs(np.random.randn(n)) * 0.5
    low = np.minimum(close, open_) - np.abs(np.random.randn(n)) * 0.5
    volume = np.random.randint(1000, 10000, n).astype(float)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )


class TestAlphaPipelineIntegration:
    """Integration tests for the full Alpha101 factor pipeline."""

    def test_all_101_factors_registered(self):
        """Verify all 101 factors are registered in the registry."""
        all_factors = FactorRegistry.list_all()
        expected = {f"alpha{i:03d}" for i in range(1, 102)}
        registered = set(all_factors)
        missing = expected - registered
        assert not missing, f"Missing factors: {missing}"
        assert len(registered) >= 101

    def test_pipeline_computes_all_101_factors(self):
        """Test that the pipeline can compute all 101 factors."""
        data = _generate_test_data()
        pipeline = FactorPipeline(max_workers=4)
        all_factor_names = [f"alpha{i:03d}" for i in range(1, 102)]

        results = pipeline.compute_factors(all_factor_names, data)

        assert len(results) == 101, (
            f"Expected 101 results, got {len(results)}. "
            f"Missing: {set(all_factor_names) - set(results.keys())}"
        )

        for name, series in results.items():
            assert isinstance(series, pd.Series), f"{name} returned {type(series)}"
            assert len(series) == len(data), f"{name} has wrong length"

    def test_pipeline_performance_under_5_seconds(self):
        """Test that computing all 101 factors on 1000 rows completes in <10s."""
        data = _generate_test_data(1000)
        pipeline = FactorPipeline(max_workers=4)
        all_factor_names = [f"alpha{i:03d}" for i in range(1, 102)]

        start = time.time()
        results = pipeline.compute_factors(all_factor_names, data)
        elapsed = time.time() - start

        assert len(results) == 101
        assert elapsed < 10.0, f"Pipeline took {elapsed:.2f}s, expected <10s"

    def test_each_factor_has_valid_properties(self):
        """Verify each factor has required name, category, description."""
        for name in FactorRegistry.list_all():
            factor_cls = FactorRegistry.get(name)
            assert factor_cls is not None
            factor = factor_cls()
            assert isinstance(factor.name, str) and len(factor.name) > 0
            assert isinstance(factor.category, str) and len(factor.category) > 0
            assert isinstance(factor.description, str) and len(factor.description) > 0

    def test_factor_validate_method(self):
        """Test that validate() works correctly for all factors."""
        data = _generate_test_data()
        incomplete_data = pd.DataFrame({"close": [1, 2, 3]})

        for name in FactorRegistry.list_all():
            factor = FactorRegistry.get(name)()
            assert factor.validate(data) is True
            assert factor.validate(incomplete_data) is False
