"""Unit tests for genetic programming factor mining module."""

import numpy as np
import pandas as pd
import pytest

from core.alpha.mining import (
    FactorExpression,
    FitnessFunction,
    FactorSynthesizer,
    GeneticProgramming,
    OperatorLibrary,
)


def _make_data(n: int = 200) -> pd.DataFrame:
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    open_ = close * (1 + np.random.randn(n) * 0.01)
    high = np.maximum(close, open_) + np.abs(np.random.randn(n)) * 0.5
    low = np.minimum(close, open_) - np.abs(np.random.randn(n)) * 0.5
    volume = np.random.randint(1000, 10000, n).astype(float)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )


class TestOperatorLibrary:
    def test_arithmetic_ops(self):
        ops = OperatorLibrary.arithmetic_ops()
        assert "add" in ops
        assert "sub" in ops
        assert "mul" in ops
        assert "div" in ops

    def test_div_by_zero(self):
        a = pd.Series([1.0, 2.0, 3.0])
        b = pd.Series([0.0, 1.0, 0.0])
        result = OperatorLibrary.arithmetic_ops()["div"](a, b)
        # div uses np.where which may return ndarray or Series
        result_series = pd.Series(result) if not isinstance(result, pd.Series) else result
        assert float(result_series.iloc[0]) == 0.0
        assert float(result_series.iloc[1]) == 2.0

    def test_time_series_ops(self):
        ops = OperatorLibrary.time_series_ops()
        assert "ts_mean" in ops
        assert "ts_std" in ops
        x = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = ops["ts_mean"](x, 3)
        assert len(result) == 5
        assert not result.isna().all()

    def test_unary_ops(self):
        ops = OperatorLibrary.unary_ops()
        assert "abs" in ops
        assert "zscore" in ops
        x = pd.Series([-1.0, 0.0, 1.0])
        result = ops["abs"](x)
        assert (result >= 0).all()

    def test_get_all_ops(self):
        all_ops = OperatorLibrary.get_all_ops()
        assert len(all_ops) >= 15


class TestFactorExpression:
    def test_compute(self):
        def my_expr(data):
            return data["close"]

        fe = FactorExpression(my_expr, "test_expr")
        data = _make_data()
        result = fe.compute(data)
        assert isinstance(result, pd.Series)
        assert len(result) == len(data)
        assert (result == data["close"]).all()

    def test_repr(self):
        fe = FactorExpression(lambda d: d["close"], "my_factor")
        assert "my_factor" in repr(fe)


class TestFitnessFunction:
    def test_evaluate(self):
        ff = FitnessFunction()
        data = _make_data()
        fe = FactorExpression(lambda d: d["close"].pct_change(), "pct_change")
        score = ff.evaluate(fe, data)
        assert isinstance(score, float)
        assert score >= 0.0

    def test_evaluate_with_high_correlation(self):
        ff = FitnessFunction()
        data = _make_data()
        returns = data["close"].pct_change()
        fe = FactorExpression(lambda d: d["close"].pct_change(), "same_as_returns")
        score = ff.evaluate(fe, data, returns)
        assert score > 0.0


class TestGeneticProgramming:
    def test_evolve_returns_factors(self):
        data = _make_data(200)
        gp = GeneticProgramming(
            population_size=10,
            generations=3,
            tournament_size=3,
            max_depth=2,
        )
        factors = gp.evolve(data, top_k=5)
        assert len(factors) > 0
        assert len(factors) <= 5
        for f in factors:
            assert isinstance(f, FactorExpression)

    def test_evolve_factors_produce_valid_output(self):
        data = _make_data(200)
        gp = GeneticProgramming(
            population_size=10,
            generations=2,
            max_depth=2,
        )
        factors = gp.evolve(data, top_k=3)
        for f in factors:
            result = f.compute(data)
            assert isinstance(result, pd.Series)
            assert len(result) == len(data)


class TestFactorSynthesizer:
    def test_empty_synthesizer(self):
        synth = FactorSynthesizer()
        data = _make_data()
        result = synth.combine(data)
        assert (result == 0.0).all()

    def test_combine_mean(self):
        f1 = FactorExpression(lambda d: d["close"], "f1")
        f2 = FactorExpression(lambda d: d["volume"], "f2")
        synth = FactorSynthesizer([f1, f2])
        data = _make_data()
        result = synth.combine(data, method="mean")
        assert len(result) == len(data)

    def test_add_factor(self):
        synth = FactorSynthesizer()
        f = FactorExpression(lambda d: d["close"], "f")
        synth.add_factor(f)
        assert len(synth.factors) == 1
