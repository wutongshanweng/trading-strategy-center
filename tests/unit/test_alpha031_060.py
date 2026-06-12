import pytest
import pandas as pd
import numpy as np
from core.alpha.alpha101.factor_registry import FactorRegistry
import core.alpha.alpha101


def generate_test_data(n=100):
    np.random.seed(42)
    return pd.DataFrame({
        'open': np.random.randn(n),
        'high': np.random.randn(n),
        'low': np.random.randn(n),
        'close': np.random.randn(n),
        'volume': np.random.randn(n)
    })


@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(31, 61)])
def test_alpha_factor(factor_name):
    data = generate_test_data()
    factor_class = FactorRegistry.get(factor_name)
    assert factor_class is not None, f"{factor_name} not registered"
    factor = factor_class()
    result = factor.compute(data)
    assert len(result) == 100
    assert isinstance(result, pd.Series)


@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(31, 61)])
def test_alpha_factor_description(factor_name):
    factor_class = FactorRegistry.get(factor_name)
    factor = factor_class()
    assert hasattr(factor, 'description'), f"{factor_name} missing description property"
    desc = factor.description
    assert isinstance(desc, str), f"{factor_name} description not a string"
    assert len(desc) > 0, f"{factor_name} description is empty"


@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(31, 61)])
def test_alpha_factor_compute_with_lookback(factor_name):
    data = generate_test_data()
    factor_class = FactorRegistry.get(factor_name)
    factor = factor_class()
    result = factor.compute(data, lookback=10)
    assert len(result) == 100
    assert isinstance(result, pd.Series)


@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(31, 61)])
def test_alpha_factor_not_all_nan(factor_name):
    data = generate_test_data()
    factor_class = FactorRegistry.get(factor_name)
    factor = factor_class()
    result = factor.compute(data)
    assert not result.isna().all(), f"{factor_name} produced all NaN values"


@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(31, 61)])
def test_alpha_factor_has_rolling_nan(factor_name):
    data = generate_test_data()
    factor_class = FactorRegistry.get(factor_name)
    factor = factor_class()
    result = factor.compute(data)
    assert result.isna().any(), f"{factor_name} should have some NaN values due to rolling window"
