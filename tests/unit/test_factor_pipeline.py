import pytest
import pandas as pd
import numpy as np
from core.alpha.alpha101.factor_pipeline import FactorPipeline
from core.alpha.alpha101.factor_registry import FactorRegistry
from core.alpha.alpha101.base import AlphaFactor


class MockAlphaFactor(AlphaFactor):
    """测试用模拟因子"""
    
    @property
    def name(self) -> str:
        return "mock_factor"
    
    @property
    def category(self) -> str:
        return "test"
    
    @property
    def description(self) -> str:
        return "A mock factor for testing"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'] * 2


@pytest.fixture
def sample_data():
    """创建测试数据"""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'open': np.random.randn(n) + 100,
        'high': np.random.randn(n) + 101,
        'low': np.random.randn(n) + 99,
        'close': np.random.randn(n) + 100,
        'volume': np.random.randint(1000, 10000, n)
    })


@pytest.fixture(autouse=True)
def cleanup_registry():
    """测试后清理注册表"""
    yield
    FactorRegistry._factors.clear()
    FactorRegistry._names.clear()
    FactorRegistry._categories.clear()


class TestFactorPipeline:
    """因子管线测试"""
    
    def test_single_factor_computation(self, sample_data):
        """测试单因子计算"""
        FactorRegistry.register(MockAlphaFactor)
        
        pipeline = FactorPipeline(max_workers=1)
        results = pipeline.compute_factors(["mock_factor"], sample_data)
        
        assert "mock_factor" in results
        assert len(results["mock_factor"]) == len(sample_data)
        assert (results["mock_factor"] == sample_data['close'] * 2).all()
    
    def test_multiple_factor_parallel_computation(self, sample_data):
        """测试多因子并行计算"""
        class MockAlphaFactor2(AlphaFactor):
            @property
            def name(self) -> str:
                return "mock_factor2"
            
            @property
            def category(self) -> str:
                return "test"
            
            @property
            def description(self) -> str:
                return "Another mock factor"
            
            def compute(self, data: pd.DataFrame) -> pd.Series:
                return data['volume'] / 100
        
        FactorRegistry.register(MockAlphaFactor)
        FactorRegistry.register(MockAlphaFactor2)
        
        pipeline = FactorPipeline(max_workers=2)
        results = pipeline.compute_factors(
            ["mock_factor", "mock_factor2"], 
            sample_data
        )
        
        assert len(results) == 2
        assert "mock_factor" in results
        assert "mock_factor2" in results
    
    def test_pipeline_handles_missing_factors(self, sample_data):
        """测试管线处理缺失因子"""
        FactorRegistry.register(MockAlphaFactor)
        
        pipeline = FactorPipeline(max_workers=1)
        results = pipeline.compute_factors(
            ["mock_factor", "nonexistent_factor"], 
            sample_data
        )
        
        assert "mock_factor" in results
        assert "nonexistent_factor" not in results
        assert len(results) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
