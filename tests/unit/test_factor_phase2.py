"""因子管理 Phase2 — 算子集/健康检测/行业中性化/报告 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pandas as pd
import pytest

from core.alpha.mining.operator_set import (
    get_operators, apply_operator, ts_sum, op_add, ts_argmax, ts_corr,
)
from core.alpha.management.factor_decay import FactorDecayDetector, FactorHealth
from core.alpha.management.industry_neutral import IndustryNeutralizer
from core.alpha.management.report_generator import FactorReportGenerator


class TestOperatorSet:
    def test_registry_size(self):
        assert len(get_operators()) >= 15

    def test_ts_sum(self):
        assert ts_sum(pd.Series([1, 2, 3, 4, 5]), 3).iloc[-1] == 12

    def test_op_add(self):
        assert list(op_add(pd.Series([1, 2, 3]), pd.Series([4, 5, 6]))) == [5, 7, 9]

    def test_ts_argmax(self):
        # 最大值 5 在倒数第2位 -> 1天前
        assert ts_argmax(pd.Series([1, 5, 2]), 3).iloc[-1] == 1.0

    def test_apply_operator_unknown(self):
        with pytest.raises(ValueError):
            apply_operator("nonexistent", pd.Series([1, 2]))

    def test_ts_corr_binary(self):
        a = pd.Series(np.arange(20, dtype=float))
        b = pd.Series(np.arange(20, dtype=float) * 2)
        c = ts_corr(a, b, 5)
        assert abs(c.iloc[-1] - 1.0) < 1e-6   # 完全正相关


class TestFactorDecay:
    def test_healthy(self):
        np.random.seed(42)
        ic = pd.Series(np.random.normal(0.05, 0.01, 200))
        r = FactorDecayDetector().check("h", ic)
        assert r.health == FactorHealth.HEALTHY

    def test_decayed(self):
        np.random.seed(1)
        ic = pd.Series(np.linspace(0.08, -0.01, 200) + np.random.normal(0, 0.004, 200))
        r = FactorDecayDetector().check("d", ic)
        assert r.health == FactorHealth.DECAYED

    def test_batch(self):
        m = {"a": pd.Series(np.random.normal(0.05, 0.01, 100)),
             "b": pd.Series(np.zeros(100))}
        out = FactorDecayDetector().batch_check(m)
        assert set(out.keys()) == {"a", "b"}


class TestIndustryNeutralizer:
    def test_mean_removes_industry_bias(self):
        np.random.seed(0)
        f = pd.Series(np.random.randn(100)); f[:40] += 0.5
        ind = pd.Series(["A"] * 40 + ["B"] * 30 + ["C"] * 30)
        neu = IndustryNeutralizer().neutralize_by_mean(f, ind)
        for i in ["A", "B", "C"]:
            assert abs(neu[ind == i].mean()) < 1e-6

    def test_zscore(self):
        np.random.seed(0)
        f = pd.Series(np.random.randn(60))
        ind = pd.Series(["A"] * 30 + ["B"] * 30)
        neu = IndustryNeutralizer().neutralize_by_zscore(f, ind)
        assert len(neu) == 60

    def test_regression_residual(self):
        np.random.seed(0)
        f = pd.Series(np.random.randn(90)); f[:30] += 1.0
        ind = pd.Series(["A"] * 30 + ["B"] * 30 + ["C"] * 30)
        neu = IndustryNeutralizer().neutralize_by_regression(f, ind)
        # 回归残差各行业均值应≈0
        assert abs(neu[ind == "A"].mean()) < 0.1

    def test_max_exposure_drops(self):
        np.random.seed(0)
        f = pd.Series(np.random.randn(90)); f[:30] += 1.0
        ind = pd.Series(["A"] * 30 + ["B"] * 30 + ["C"] * 30)
        n = IndustryNeutralizer()
        before = n.max_industry_exposure(f, ind)
        after = n.max_industry_exposure(n.neutralize_by_mean(f, ind), ind)
        assert after < before


class TestReportGenerator:
    def _data(self, n=300):
        np.random.seed(7)
        ret = pd.Series(np.random.randn(n) * 0.02)
        f_good = ret * 5 + np.random.randn(n) * 0.5
        f_dup = f_good * 0.98 + np.random.randn(n) * 0.05
        f_noise = pd.Series(np.random.randn(n))
        return pd.DataFrame({"f_good": f_good, "f_dup": f_dup, "f_noise": f_noise}), ret

    def test_generate_ranks_and_recommends(self):
        fdf, ret = self._data()
        rep = FactorReportGenerator().generate(fdf, ret, top_n=10)
        assert rep.total_factors == 3
        assert rep.top_factors[0].name == "f_good"        # 最强因子排第一
        # 冗余对检出 f_good~f_dup
        assert any({"f_good", "f_dup"} == {a, b} for a, b, _ in rep.high_correlation_pairs)
        # 推荐排除冗余 f_dup
        assert "f_dup" not in rep.recommended

    def test_outputs(self, tmp_path):
        fdf, ret = self._data()
        gen = FactorReportGenerator()
        rep = gen.generate(fdf, ret)
        gen.save_html(rep, str(tmp_path / "r.html"))
        gen.save_json(rep, str(tmp_path / "r.json"))
        assert (tmp_path / "r.html").exists() and (tmp_path / "r.json").exists()

    def test_industry_exposure_compare(self):
        fdf, ret = self._data()
        ind = pd.Series(np.random.choice(["钢铁", "有色"], len(fdf)))
        rep = FactorReportGenerator().generate(fdf, ret, industry_labels=ind)
        assert rep.industry_exposure_after <= rep.industry_exposure_before + 1e-9
