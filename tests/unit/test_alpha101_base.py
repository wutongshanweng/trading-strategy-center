import numpy as np
import pandas as pd
import pytest

from core.alpha.alpha101 import AlphaFactor, FactorRegistry


def _make_price_data(n: int = 100) -> pd.DataFrame:
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    open_ = close * (1 + np.random.randn(n) * 0.01)
    high = close * (1 + np.random.rand(n) * 0.02)
    low = close * (1 - np.random.rand(n) * 0.02)
    volume = np.random.randint(1000, 10000, n).astype(float)
    return pd.DataFrame(
        {"open": open_, "close": close, "high": high, "low": low, "volume": volume},
        index=dates,
    )


class TestAlphaFactor:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            AlphaFactor()

    def test_subclass_interface(self):
        class DummyFactor(AlphaFactor):
            @property
            def name(self):
                return "dummy_factor"

            @property
            def category(self):
                return "test"

            def compute(self, data):
                return pd.Series(0, index=data.index)

        factor = DummyFactor()
        assert factor.name == "dummy_factor"
        assert factor.category == "test"
        result = factor.compute(_make_price_data())
        assert isinstance(result, pd.Series)

    def test_validate_with_complete_data(self):
        class DummyFactor(AlphaFactor):
            @property
            def name(self):
                return "dummy"

            @property
            def category(self):
                return "test"

            def compute(self, data):
                return pd.Series(0, index=data.index)

        factor = DummyFactor()
        data = _make_price_data()
        assert factor.validate(data) is True

    def test_validate_with_missing_columns(self):
        class DummyFactor(AlphaFactor):
            @property
            def name(self):
                return "dummy"

            @property
            def category(self):
                return "test"

            def compute(self, data):
                return pd.Series(0, index=data.index)

        factor = DummyFactor()
        data = pd.DataFrame({"close": [1, 2, 3], "volume": [100, 200, 300]})
        assert factor.validate(data) is False


class TestFactorRegistry:
    def setup_method(self):
        FactorRegistry._factors.clear()

    def test_register_and_get(self):
        class TestFactor(AlphaFactor):
            @property
            def name(self):
                return "test_factor"

            @property
            def category(self):
                return "test_category"

            def compute(self, data):
                return pd.Series(0, index=data.index)

        FactorRegistry.register(TestFactor)
        retrieved = FactorRegistry.get("test_factor")
        assert retrieved is TestFactor

    def test_list_all(self):
        class Factor1(AlphaFactor):
            @property
            def name(self):
                return "factor1"

            @property
            def category(self):
                return "cat1"

            def compute(self, data):
                return pd.Series(0, index=data.index)

        class Factor2(AlphaFactor):
            @property
            def name(self):
                return "factor2"

            @property
            def category(self):
                return "cat2"

            def compute(self, data):
                return pd.Series(0, index=data.index)

        FactorRegistry.register(Factor1)
        FactorRegistry.register(Factor2)
        all_factors = FactorRegistry.list_all()
        assert "factor1" in all_factors
        assert "factor2" in all_factors

    def test_list_by_category(self):
        class MomentumFactor(AlphaFactor):
            @property
            def name(self):
                return "momentum"

            @property
            def category(self):
                return "momentum"

            def compute(self, data):
                return pd.Series(0, index=data.index)

        class VolumeFactor(AlphaFactor):
            @property
            def name(self):
                return "volume"

            @property
            def category(self):
                return "volume"

            def compute(self, data):
                return pd.Series(0, index=data.index)

        FactorRegistry.register(MomentumFactor)
        FactorRegistry.register(VolumeFactor)
        momentum_factors = FactorRegistry.list_by_category("momentum")
        assert "momentum" in momentum_factors
        assert "volume" not in momentum_factors

    def test_get_nonexistent_factor(self):
        result = FactorRegistry.get("nonexistent")
        assert result is None

    def test_factor_has_correct_name_and_category(self):
        class CustomFactor(AlphaFactor):
            @property
            def name(self):
                return "custom_factor"

            @property
            def category(self):
                return "custom_category"

            def compute(self, data):
                return pd.Series(0, index=data.index)

        FactorRegistry.register(CustomFactor)
        factor_class = FactorRegistry.get("custom_factor")
        factor_instance = factor_class()
        assert factor_instance.name == "custom_factor"
        assert factor_instance.category == "custom_category"
