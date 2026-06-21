"""Champion/Challenger 安全晋级 (阶段4) — 单测。

用独立临时状态文件, 不依赖现有 data。
"""

import importlib

import core.adaptive.champion_challenger as cc_mod
from core.adaptive.champion_challenger import ChallengerRecord


def _fresh_registry(tmp_path):
    """指向临时状态文件的全新注册表。"""
    cc_mod._STATE_FILE = tmp_path / "cc_test.json"
    reg = cc_mod.ChampionChallengerRegistry()
    reg._records.clear()
    return reg


class TestEligibility:
    def test_not_eligible_too_few_evals(self):
        r = ChallengerRecord(name="s")
        r.evals = [{"passed": True, "oos_sharpe": 1.0}]
        assert r.eligible_for_graduation() is False

    def test_eligible_meets_all(self):
        r = ChallengerRecord(name="s")
        r.evals = [{"passed": True, "oos_sharpe": 0.8}] * 3
        assert r.eligible_for_graduation() is True

    def test_not_eligible_low_pass_rate(self):
        r = ChallengerRecord(name="s")
        r.evals = [{"passed": True, "oos_sharpe": 0.8},
                   {"passed": False, "oos_sharpe": -0.2},
                   {"passed": False, "oos_sharpe": -0.1}]
        assert r.eligible_for_graduation() is False


class TestLifecycle:
    def test_enroll_and_evaluate(self, tmp_path):
        reg = _fresh_registry(tmp_path)
        reg.enroll("alpha", regime="TRENDING")
        reg.record_evaluation("alpha", passed=True, oos_sharpe=0.9)
        view = reg.list_all()
        assert len(view["challengers"]) == 1
        assert view["challengers"][0]["n_evals"] == 1

    def test_graduate_blocked_until_eligible(self, tmp_path):
        reg = _fresh_registry(tmp_path)
        reg.enroll("beta")
        reg.record_evaluation("beta", passed=True, oos_sharpe=0.8)
        # 只有 1 次评估, 不应毕业
        res = reg.graduate("beta", approved_by="user")
        assert res["ok"] is False

    def test_graduate_succeeds_when_eligible(self, tmp_path):
        reg = _fresh_registry(tmp_path)
        reg.enroll("gamma")
        for _ in range(3):
            reg.record_evaluation("gamma", passed=True, oos_sharpe=0.7)
        res = reg.graduate("gamma", approved_by="user", allocation=0.15)
        assert res["ok"] is True
        view = reg.list_all()
        assert len(view["champions"]) == 1
        assert view["champions"][0]["allocation"] == 0.15

    def test_ingest_verdicts(self, tmp_path):
        reg = _fresh_registry(tmp_path)
        verdicts = [
            {"strategy_name": "s1", "passed": True, "mean_oos_sharpe": 0.6, "regime": "TRENDING"},
            {"strategy_name": "s2", "passed": False, "mean_oos_sharpe": -0.3, "regime": "QUIET"},
        ]
        res = reg.ingest_promotion_verdicts(verdicts)
        assert res["enrolled"] == 2 and res["evaluations_recorded"] == 2

    def test_retire(self, tmp_path):
        reg = _fresh_registry(tmp_path)
        reg.enroll("delta")
        res = reg.retire("delta")
        assert res["ok"] is True
        assert len(reg.list_all()["retired"]) == 1
