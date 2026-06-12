import numpy as np
import pandas as pd
import pytest

from core.alpha.factor_library import FactorLibrary, FactorMetadata
from core.alpha.factor_evaluator import FactorEvaluator, FactorReport
from core.alpha.factor_combiner import FactorCombiner


def _make_price_data(n: int = 100) -> pd.DataFrame:
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    high = close * (1 + np.random.rand(n) * 0.02)
    low = close * (1 - np.random.rand(n) * 0.02)
    volume = np.random.randint(1000, 10000, n).astype(float)
    return pd.DataFrame(
        {"close": close, "high": high, "low": low, "volume": volume},
        index=dates,
    )


def _momentum(data: pd.DataFrame, window: int = 20) -> pd.Series:
    return data["close"].pct_change(window)


def _volatility(data: pd.DataFrame, window: int = 20) -> pd.Series:
    return data["close"].pct_change().rolling(window).std()


def _volume_factor(data: pd.DataFrame) -> pd.Series:
    return data["volume"] / data["volume"].rolling(20).mean()


class TestFactorLibrary:
    def test_init(self):
        lib = FactorLibrary()
        assert lib.list_factors() == []

    def test_register_factor(self):
        lib = FactorLibrary()
        lib.register("momentum", _momentum, category="trend")
        factors = lib.list_factors()
        assert "momentum" in factors

    def test_register_multiple(self):
        lib = FactorLibrary()
        lib.register("momentum", _momentum, category="trend")
        lib.register("volatility", _volatility, category="risk")
        lib.register("volume", _volume_factor, category="flow")
        assert len(lib.list_factors()) == 3

    def test_get_factor(self):
        lib = FactorLibrary()
        lib.register("momentum", _momentum, category="trend")
        meta = lib.get_factor("momentum")
        assert isinstance(meta, FactorMetadata)
        assert meta.name == "momentum"
        assert meta.category == "trend"

    def test_get_factor_not_found(self):
        lib = FactorLibrary()
        with pytest.raises(KeyError):
            lib.get_factor("nonexistent")

    def test_list_factors_by_category(self):
        lib = FactorLibrary()
        lib.register("momentum", _momentum, category="trend")
        lib.register("volatility", _volatility, category="risk")
        lib.register("volume", _volume_factor, category="flow")

        trend_factors = lib.list_factors(category="trend")
        assert trend_factors == ["momentum"]

        risk_factors = lib.list_factors(category="risk")
        assert risk_factors == ["volatility"]

    def test_remove_factor(self):
        lib = FactorLibrary()
        lib.register("momentum", _momentum)
        assert lib.remove_factor("momentum") is True
        assert lib.list_factors() == []

    def test_remove_nonexistent(self):
        lib = FactorLibrary()
        assert lib.remove_factor("nonexistent") is False

    def test_get_categories(self):
        lib = FactorLibrary()
        lib.register("momentum", _momentum, category="trend")
        lib.register("volatility", _volatility, category="risk")
        categories = lib.get_categories()
        assert set(categories) == {"trend", "risk"}

    def test_compute_all(self):
        lib = FactorLibrary()
        lib.register("momentum", _momentum, category="trend")
        lib.register("volatility", _volatility, category="risk")

        data = _make_price_data()
        result = lib.compute_all(data)

        assert isinstance(result, pd.DataFrame)
        assert "momentum" in result.columns
        assert "volatility" in result.columns
        assert len(result) == len(data)

    def test_compute_all_selective(self):
        lib = FactorLibrary()
        lib.register("momentum", _momentum)
        lib.register("volatility", _volatility)

        data = _make_price_data()
        result = lib.compute_all(data, factors=["momentum"])

        assert "momentum" in result.columns
        assert "volatility" not in result.columns

    def test_compute_with_params(self):
        def custom_factor(data: pd.DataFrame, window: int = 10) -> pd.Series:
            return data["close"].pct_change(window)

        lib = FactorLibrary()
        lib.register("custom", custom_factor, params={"window": 5})

        data = _make_price_data()
        result = lib.compute_all(data)
        assert "custom" in result.columns

    def test_overwrite_factor(self):
        lib = FactorLibrary()
        lib.register("momentum", _momentum, category="trend")
        lib.register("momentum", _volatility, category="risk")

        meta = lib.get_factor("momentum")
        assert meta.category == "risk"


class TestFactorEvaluator:
    def test_init(self):
        evaluator = FactorEvaluator()
        assert evaluator.forward_returns is None

    def test_set_forward_returns(self):
        evaluator = FactorEvaluator()
        returns = pd.Series([0.01, -0.02, 0.03])
        evaluator.set_forward_returns(returns)
        assert evaluator.forward_returns is not None

    def test_calculate_ic(self):
        np.random.seed(42)
        n = 100
        factor = pd.Series(np.random.randn(n))
        returns = pd.Series(np.random.randn(n))

        evaluator = FactorEvaluator(forward_returns=returns)
        ic_series = evaluator.calculate_ic(factor)

        assert isinstance(ic_series, pd.Series)
        assert len(ic_series) > 0

    def test_calculate_ic_no_returns(self):
        evaluator = FactorEvaluator()
        factor = pd.Series([1, 2, 3])
        with pytest.raises(ValueError):
            evaluator.calculate_ic(factor)

    def test_calculate_ir(self):
        np.random.seed(42)
        n = 100
        factor = pd.Series(np.random.randn(n))
        returns = pd.Series(np.random.randn(n))

        evaluator = FactorEvaluator(forward_returns=returns)
        ir = evaluator.calculate_ir(factor)

        assert isinstance(ir, float)

    def test_calculate_turnover(self):
        np.random.seed(42)
        n = 100
        factor = pd.Series(np.random.randn(n))

        evaluator = FactorEvaluator()
        turnover = evaluator.calculate_turnover(factor, quantile=0.2)

        assert isinstance(turnover, float)
        assert 0 <= turnover <= 1

    def test_calculate_turnover_empty(self):
        evaluator = FactorEvaluator()
        factor = pd.Series(dtype=float)
        turnover = evaluator.calculate_turnover(factor)
        assert turnover == 0.0

    def test_generate_report(self):
        np.random.seed(42)
        n = 100
        dates = pd.date_range("2024-01-01", periods=n, freq="D")
        factor = pd.Series(np.random.randn(n), index=dates)
        returns = pd.Series(np.random.randn(n), index=dates)

        evaluator = FactorEvaluator(forward_returns=returns)
        report = evaluator.generate_report("test_factor", factor)

        assert isinstance(report, FactorReport)
        assert report.factor_name == "test_factor"
        assert isinstance(report.ic_mean, float)
        assert isinstance(report.ic_std, float)
        assert isinstance(report.ir, float)
        assert isinstance(report.turnover, float)
        assert report.ic_series is not None
        assert "periods" in report.metadata

    def test_generate_report_empty_factor(self):
        evaluator = FactorEvaluator(forward_returns=pd.Series([0.1, 0.2]))
        report = evaluator.generate_report("empty", pd.Series(dtype=float))

        assert report.ic_mean == 0.0
        assert report.ic_std == 0.0
        assert report.ir == 0.0
        assert report.turnover == 0.0


class TestFactorCombiner:
    def test_init(self):
        combiner = FactorCombiner()
        assert combiner.factors is None

    def test_set_factors(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        combiner = FactorCombiner(df)
        assert combiner.factors is not None

    def test_equal_weight(self):
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [3.0, 4.0, 5.0]})
        combiner = FactorCombiner(df)
        result = combiner.equal_weight()

        expected = df.mean(axis=1)
        pd.testing.assert_series_equal(result, expected)

    def test_equal_weight_empty(self):
        combiner = FactorCombiner()
        result = combiner.equal_weight()
        assert result.empty

    def test_ic_weight(self):
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [3.0, 4.0, 5.0]})
        ic_values = {"a": 0.5, "b": 0.3}
        combiner = FactorCombiner(df)
        result = combiner.ic_weight(ic_values=ic_values)

        assert isinstance(result, pd.Series)
        assert len(result) == 3

    def test_ic_weight_no_values(self):
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [3.0, 4.0, 5.0]})
        combiner = FactorCombiner(df)
        result = combiner.ic_weight()

        expected = combiner.equal_weight()
        pd.testing.assert_series_equal(result, expected)

    def test_regime_weight(self):
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "b": [4.0, 3.0, 2.0, 1.0]})
        regimes = pd.Series(["bull", "bull", "bear", "bear"])
        regime_weights = {
            "bull": {"a": 0.7, "b": 0.3},
            "bear": {"a": 0.3, "b": 0.7},
        }
        combiner = FactorCombiner(df)
        result = combiner.regime_weight(regimes=regimes, regime_weights=regime_weights)

        assert isinstance(result, pd.Series)
        assert len(result) == 4

    def test_regime_weight_no_weights(self):
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [3.0, 4.0, 5.0]})
        regimes = pd.Series([0, 0, 1])
        combiner = FactorCombiner(df)
        result = combiner.regime_weight(regimes=regimes)

        assert isinstance(result, pd.Series)

    def test_normalize_factors_zscore(self):
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
        combiner = FactorCombiner(df)
        result = combiner.normalize_factors(method="zscore")

        assert isinstance(result, pd.DataFrame)
        assert abs(result["a"].mean()) < 0.01

    def test_normalize_factors_minmax(self):
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
        combiner = FactorCombiner(df)
        result = combiner.normalize_factors(method="minmax")

        assert result.min().min() >= 0
        assert result.max().max() <= 1

    def test_normalize_factors_rank(self):
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
        combiner = FactorCombiner(df)
        result = combiner.normalize_factors(method="rank")

        assert isinstance(result, pd.DataFrame)
        assert result.max().max() <= 1

    def test_normalize_factors_unknown(self):
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
        combiner = FactorCombiner(df)
        with pytest.raises(ValueError):
            combiner.normalize_factors(method="unknown")
