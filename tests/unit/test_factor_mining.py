"""因子挖掘 — 单元测试 (Spec §7.1)。"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pandas as pd
import pytest

from core.alpha.mining.operator_set import (
    get_operator, get_operators, apply_operator, ts_rank, ts_sum, op_add, op_sub,
)
from core.alpha.mining import GeneticFactorMiner, GeneticConfig, MinedFactor


def _make_sample_data(n: int = 200) -> pd.DataFrame:
    np.random.seed(42)
    close = pd.Series(100 * (1 + np.random.randn(n) * 0.02).cumprod())
    return pd.DataFrame({
        "open": close * (1 + np.random.randn(n) * 0.003),
        "high": close * (1 + np.abs(np.random.randn(n)) * 0.01),
        "low": close * (1 - np.abs(np.random.randn(n)) * 0.01),
        "close": close,
        "volume": np.random.randint(1_000_000, 10_000_000, n).astype(float),
    })


class TestOperatorSet:
    def test_ts_rank_basic(self):
        s = pd.Series(range(1, 11))
        result = ts_rank(s, d=5)
        assert not result.isna().all()
        assert 0 <= result.iloc[-1] <= 1

    def test_ts_sum_basic(self):
        assert ts_sum(pd.Series([1, 2, 3, 4, 5]), d=3).iloc[-1] == 12

    def test_op_add(self):
        assert (op_add(pd.Series([1, 2, 3]), pd.Series([4, 5, 6])) == pd.Series([5, 7, 9])).all()

    def test_op_sub(self):
        assert (op_sub(pd.Series([4, 5, 6]), pd.Series([1, 2, 3])) == pd.Series([3, 3, 3])).all()

    def test_operator_registry(self):
        ops = get_operators()
        assert "ts_rank" in ops and "ts_sum" in ops and "op_add" in ops
        assert len(ops) >= 15

    def test_apply_operator(self):
        r = apply_operator("ts_sum", pd.Series([1, 2, 3]), d=2)
        assert r.iloc[-1] == 5

    def test_unknown_operator_raises(self):
        with pytest.raises(ValueError):
            apply_operator("no_such_op", pd.Series([1, 2]))


class TestGeneticFactorMiner:
    def test_miner_basic(self):
        miner = GeneticFactorMiner(GeneticConfig(population_size=20, generations=5))
        results = miner.mine(_make_sample_data(200), n_factors=5, seed=42)
        assert len(results) <= 5
        if results:
            f = results[0]
            assert isinstance(f, MinedFactor)
            assert hasattr(f, "ic_mean") and hasattr(f, "expression")

    def test_miner_different_data_sizes(self):
        for n in [50, 100, 300]:
            miner = GeneticFactorMiner(GeneticConfig(population_size=15, generations=3))
            results = miner.mine(_make_sample_data(n), n_factors=3)
            assert len(results) <= 3

    def test_empty_data_returns_empty(self):
        miner = GeneticFactorMiner()
        assert miner.mine(pd.DataFrame(), n_factors=3) == []

    def test_save_and_load(self, tmp_path):
        miner = GeneticFactorMiner(GeneticConfig(population_size=15, generations=3))
        results = miner.mine(_make_sample_data(150), n_factors=3)
        path = tmp_path / "mined_factors.json"
        miner.save_factors(results, str(path))
        assert path.exists()
        loaded = GeneticFactorMiner.load_factors(str(path))
        assert len(loaded) == len(results)
        if results:
            assert loaded[0].name == results[0].name

    def test_deap_fallback(self):
        """无 deap 时回退到 numpy 引擎, mine 仍可用。"""
        import core.alpha.mining.genetic_programming as gp
        # 模拟 deap 不可用
        orig = gp._deap_available
        gp._deap_available = lambda: False
        try:
            miner = gp.GeneticFactorMiner(gp.GeneticConfig(population_size=15, generations=3))
            assert miner.backend == "numpy"
            results = miner.mine(_make_sample_data(120), n_factors=2)
            assert len(results) <= 2
        finally:
            gp._deap_available = orig
