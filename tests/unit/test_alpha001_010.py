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

@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(1, 11)])
def test_alpha_factor(factor_name):
    data = generate_test_data()
    factor_class = FactorRegistry.get(factor_name)
    assert factor_class is not None, f"{factor_name} not registered"
    factor = factor_class()
    result = factor.compute(data)
    assert len(result) == 100
    assert isinstance(result, pd.Series)

@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(1, 11)])
def test_alpha_factor_description(factor_name):
    factor_class = FactorRegistry.get(factor_name)
    factor = factor_class()
    assert hasattr(factor, 'description'), f"{factor_name} missing description property"
    desc = factor.description
    assert isinstance(desc, str), f"{factor_name} description not a string"
    assert len(desc) > 0, f"{factor_name} description is empty"

@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(1, 11)])
def test_alpha_factor_compute_with_lookback(factor_name):
    data = generate_test_data()
    factor_class = FactorRegistry.get(factor_name)
    factor = factor_class()
    # Should accept lookback parameter without error
    result = factor.compute(data, lookback=10)
    assert len(result) == 100
    assert isinstance(result, pd.Series)

def test_alpha004_edge_case_high_equals_low():
    data = generate_test_data()
    data['high'] = data['low']  # force high == low
    factor_class = FactorRegistry.get('alpha004')
    factor = factor_class()
    result = factor.compute(data)
    # Should produce inf or nan due to division by zero, but no exception
    assert len(result) == 100
    assert isinstance(result, pd.Series)

def test_alpha006_edge_case_zero_volume():
    data = generate_test_data()
    data['volume'] = 0  # zero volume leads to division by zero in VWAP
    factor_class = FactorRegistry.get('alpha006')
    factor = factor_class()
    result = factor.compute(data)
    # Should produce inf or nan, but no exception
    assert len(result) == 100
    assert isinstance(result, pd.Series)