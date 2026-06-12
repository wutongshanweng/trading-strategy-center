import pytest
from ml.pipeline import MLPipeline

@pytest.mark.asyncio
async def test_pipeline_uses_xgboost_not_random_forest():
    """验证pipeline确实使用XGBoost而非RandomForest"""
    pipeline = MLPipeline()
    
    # 检查模型类型
    assert hasattr(pipeline, 'models')
    
    # 创建测试数据
    import pandas as pd
    import numpy as np
    np.random.seed(42)
    n_samples = 100
    test_data = pd.DataFrame({
        'open': np.random.randn(n_samples).cumsum() + 100,
        'high': np.random.randn(n_samples).cumsum() + 101,
        'low': np.random.randn(n_samples).cumsum() + 99,
        'close': np.random.randn(n_samples).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, n_samples)
    })
    
    # 训练pipeline
    await pipeline.train(test_data)
    
    # 检查xgboost层是否使用了正确的模型
    from xgboost import XGBRegressor
    assert isinstance(pipeline.models.get('xgboost'), XGBRegressor), \
        "XGBoost层应该使用XGBRegressor而非RandomForestRegressor"
