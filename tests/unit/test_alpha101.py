import numpy as np
import pandas as pd
import pytest

from core.alpha.alpha101 import Alpha001, Alpha002, Alpha003, AlphaBase, AlphaFactor


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


class TestAlphaBase:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            AlphaBase()

    def test_subclass_interface(self):
        class DummyAlpha(AlphaBase):
            @property
            def name(self):
                return "dummy"

            @property
            def category(self):
                return "test"

            @property
            def description(self):
                return "dummy alpha"

            def compute(self, data):
                return pd.Series(0, index=data.index)

        alpha = DummyAlpha()
        assert alpha.name == "dummy"
        assert alpha.category == "test"
        assert alpha.description == "dummy alpha"
        result = alpha.compute(_make_price_data())
        assert isinstance(result, pd.Series)


class TestAlpha001:
    def test_is_alpha_base(self):
        assert issubclass(Alpha001, AlphaFactor)

    def test_properties(self):
        alpha = Alpha001()
        assert alpha.name == "alpha001"
        assert alpha.category == "momentum"
        assert "momentum" in alpha.description.lower()

    def test_compute(self):
        data = _make_price_data()
        alpha = Alpha001()
        result = alpha.compute(data, lookback=20)

        assert isinstance(result, pd.Series)
        assert len(result) == len(data)
        assert result.iloc[:20].isna().all()
        assert result.iloc[20:].notna().any()

    def test_compute_custom_lookback(self):
        data = _make_price_data()
        alpha = Alpha001()
        result = alpha.compute(data, lookback=10)

        assert result.iloc[:10].isna().all()
        assert result.iloc[10:].notna().any()


class TestAlpha002:
    def test_is_alpha_base(self):
        assert issubclass(Alpha002, AlphaFactor)

    def test_properties(self):
        alpha = Alpha002()
        assert alpha.name == "alpha002"
        assert alpha.category == "volume_price"

    def test_compute(self):
        data = _make_price_data()
        alpha = Alpha002()
        result = alpha.compute(data, lookback=20)

        assert isinstance(result, pd.Series)
        assert len(result) == len(data)
        assert result.iloc[:21].isna().all()


class TestAlpha003:
    def test_is_alpha_base(self):
        assert issubclass(Alpha003, AlphaFactor)

    def test_properties(self):
        alpha = Alpha003()
        assert alpha.name == "alpha003"
        assert alpha.category == "volume_price"

    def test_compute(self):
        data = _make_price_data()
        alpha = Alpha003()
        result = alpha.compute(data, lookback=20)

        assert isinstance(result, pd.Series)
        assert len(result) == len(data)
        assert result.iloc[:19].isna().all()
