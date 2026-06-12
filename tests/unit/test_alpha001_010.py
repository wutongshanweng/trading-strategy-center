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