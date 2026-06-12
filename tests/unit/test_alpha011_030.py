import pytest
import pandas as pd
import numpy as np
from core.alpha.alpha101.factor_registry import FactorRegistry
from core.alpha.alpha101.factor_pipeline import FactorPipeline
import core.alpha.alpha101  # This triggers registration of all factors

def generate_test_data(n=100):
    np.random.seed(42)
    return pd.DataFrame({
        'open': np.random.randn(n),
        'high': np.random.randn(n),
        'low': np.random.randn(n),
        'close': np.random.randn(n),
        'volume': np.random.randn(n)
    })

@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(11, 31)])
def test_alpha_factor(factor_name):
    data = generate_test_data()
    factor_class = FactorRegistry.get(factor_name)
    assert factor_class is not None, f"{factor_name} not registered"
    factor = factor_class()
    result = factor.compute(data)
    assert len(result) == 100
    assert isinstance(result, pd.Series)

@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(11, 31)])
def test_alpha_factor_description(factor_name):
    factor_class = FactorRegistry.get(factor_name)
    factor = factor_class()
    assert hasattr(factor, 'description'), f"{factor_name} missing description property"
    desc = factor.description
    assert isinstance(desc, str), f"{factor_name} description not a string"
    assert len(desc) > 0, f"{factor_name} description is empty"

@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(11, 31)])
def test_alpha_factor_compute_with_lookback(factor_name):
    data = generate_test_data()
    factor_class = FactorRegistry.get(factor_name)
    factor = factor_class()
    # Should accept lookback parameter without error
    result = factor.compute(data, lookback=10)
    assert len(result) == 100
    assert isinstance(result, pd.Series)

def test_alpha011_correlation_momentum():
    data = generate_test_data()
    factor_class = FactorRegistry.get('alpha011')
    factor = factor_class()
    result = factor.compute(data)
    # Should have some valid values (not all NaN)
    assert not result.isna().all(), "Alpha011 produced all NaN values"
    # Should have some NaN values due to rolling window
    assert result.isna().any(), "Alpha011 should have some NaN values due to rolling window"

def test_alpha012_volume_change():
    data = generate_test_data()
    factor_class = FactorRegistry.get('alpha012')
    factor = factor_class()
    result = factor.compute(data)
    # Should have some valid values (not all NaN)
    assert not result.isna().all(), "Alpha012 produced all NaN values"
    # Should have some NaN values due to pct_change
    assert result.isna().any(), "Alpha012 should have some NaN values due to pct_change"

def test_alpha013_acceleration():
    data = generate_test_data()
    factor_class = FactorRegistry.get('alpha013')
    factor = factor_class()
    result = factor.compute(data)
    # Should have some valid values (not all NaN)
    assert not result.isna().all(), "Alpha013 produced all NaN values"
    # Should have some NaN values due to diff
    assert result.isna().any(), "Alpha013 should have some NaN values due to diff"

def test_alpha014_correlation():
    data = generate_test_data()
    factor_class = FactorRegistry.get('alpha014')
    factor = factor_class()
    result = factor.compute(data)
    # Should have some valid values (not all NaN)
    assert not result.isna().all(), "Alpha014 produced all NaN values"
    # Should have some NaN values due to rolling window
    assert result.isna().any(), "Alpha014 should have some NaN values due to rolling window"

def test_alpha015_volume_volatility():
    data = generate_test_data()
    factor_class = FactorRegistry.get('alpha015')
    factor = factor_class()
    result = factor.compute(data)
    # Should have some valid values (not all NaN)
    assert not result.isna().all(), "Alpha015 produced all NaN values"
    # Should have some NaN values due to rolling window
    assert result.isna().any(), "Alpha015 should have some NaN values due to rolling window"