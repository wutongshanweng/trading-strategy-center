"""ML 特征工程测试。"""

import numpy as np
import pandas as pd

from ml.features.pipeline import FeaturePipeline
from ml.features.technical_features import TechnicalFeatureSet


def _make_sample_data(n: int = 100) -> pd.DataFrame:
    np.random.seed(42)
    closes = 100 + np.cumsum(np.random.randn(n) * 0.5)
    return pd.DataFrame({
        "open": closes * (1 + np.random.randn(n) * 0.002),
        "high": closes * (1 + np.abs(np.random.randn(n)) * 0.01),
        "low": closes * (1 - np.abs(np.random.randn(n)) * 0.01),
        "close": closes,
        "volume": np.random.randint(10000, 100000, n),
    }, index=pd.date_range("2025-01-01", periods=n, freq="D"))


class TestFeaturePipeline:
    def test_register_and_compute(self):
        pipe = FeaturePipeline()
        pipe.register_module(TechnicalFeatureSet())
        X = pipe.compute_all(_make_sample_data(120))
        assert X.shape[1] >= 20  # 验收项 1

    def test_different_data_sizes(self):
        for n in [40, 100, 300]:
            pipe = FeaturePipeline()
            pipe.register_module(TechnicalFeatureSet())
            X = pipe.compute_all(_make_sample_data(n))
            assert X.shape[0] <= n

    def test_normalize(self):
        pipe = FeaturePipeline()
        pipe.register_module(TechnicalFeatureSet())
        X = pipe.compute_all(_make_sample_data(200), normalize=True)
        # 标准化后各列均值接近 0
        assert np.allclose(X.mean().values, 0, atol=1e-6)

    def test_save_load_config(self, tmp_path):
        pipe = FeaturePipeline()
        pipe.register_module(TechnicalFeatureSet())
        cfg = str(tmp_path / "feat.json")
        pipe.save_config(cfg)
        pipe2 = FeaturePipeline()
        pipe2.register_module(TechnicalFeatureSet())  # 先注册模块以便重映射
        pipe2.load_config(cfg)
        # 验收项 13: 特征数一致
        assert len(pipe2.get_feature_names()) == len(pipe.get_feature_names())
        X = pipe2.compute_all(_make_sample_data(120))
        assert X.shape[1] >= 20

    def test_list_features(self):
        pipe = FeaturePipeline()
        pipe.register_module(TechnicalFeatureSet())
        feats = pipe.list_features(category="technical")
        assert len(feats) >= 20
        assert all(f["category"] == "technical" for f in feats)


class TestTechnicalFeatureSet:
    def test_all_features_return_series(self):
        tfs = TechnicalFeatureSet()
        data = _make_sample_data(100)
        for name, fn, cat in tfs.get_features():
            result = fn(data)
            assert isinstance(result, pd.Series), f"{name} not Series"
