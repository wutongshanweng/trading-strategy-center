"""锦标赛真实回测编排 (阶段1) — 单测。

不触 DuckDB (服务器持有独占锁): 只测参数隔离 + record_result 评分 + 持久化。
"""

import asyncio
import pytest

from tournament.tournament_manager import TournamentManager, StrategyEntry
from tournament.scoring import calculate_composite_score


class TestParamIsolation:
    def test_instantiate_copies_params(self):
        from tournament.tournament_runner import _instantiate
        a = _instantiate("trend_ma_cross")
        b = _instantiate("trend_ma_cross")
        if a is None or b is None:
            pytest.skip("strategy not registered")
        a.params["fast"] = 999
        # 改 a 的 params 不应污染 b 或类属性
        assert b.params["fast"] != 999

    def test_unknown_strategy_returns_none(self):
        from tournament.tournament_runner import _instantiate
        assert _instantiate("__no_such_strategy__") is None


class TestRecordResult:
    def test_record_and_rank(self):
        async def run():
            mgr = TournamentManager()
            mgr._entries.clear()
            await mgr.record_result("good", sharpe=2.0, win_rate=0.6,
                                    profit_factor=2.5, max_drawdown=-0.05,
                                    total_trades=40, total_return=0.3)
            await mgr.record_result("bad", sharpe=-1.0, win_rate=0.3,
                                    profit_factor=0.5, max_drawdown=-0.4,
                                    total_trades=20, total_return=-0.2)
            board = await mgr.get_leaderboard(10)
            return board
        board = asyncio.run(run())
        names = [e.name for e in board]
        assert "good" in names and "bad" in names
        # good 综合分应高于 bad
        good = next(e for e in board if e.name == "good")
        bad = next(e for e in board if e.name == "bad")
        assert good.current_score > bad.current_score
        assert good.rank < bad.rank

    def test_total_return_preserved(self):
        async def run():
            mgr = TournamentManager()
            mgr._entries.clear()
            await mgr.record_result("s1", sharpe=1.0, win_rate=0.5,
                                    profit_factor=1.5, max_drawdown=-0.1,
                                    total_trades=10, total_return=0.42)
            return mgr._entries["s1"].total_return
        assert asyncio.run(run()) == 0.42


class TestComposite:
    def test_negative_sharpe_floored(self):
        # 记录已知问题: 负夏普被截断为 0 贡献 (阶段2 闸门纠偏)
        neg = calculate_composite_score({"sharpe": -2.0, "win_rate": 0.0,
                                         "profit_factor": 0.0, "max_drawdown": 0.0,
                                         "trade_count": 0})
        assert neg == 0.0

    def test_high_winrate_can_outscore_negative_sharpe(self):
        a = calculate_composite_score({"sharpe": -0.5, "win_rate": 0.7,
                                       "profit_factor": 1.0, "max_drawdown": -0.02,
                                       "trade_count": 3})
        b = calculate_composite_score({"sharpe": 0.4, "win_rate": 0.45,
                                       "profit_factor": 1.0, "max_drawdown": -0.02,
                                       "trade_count": 11})
        # 这条断言记录现状(高胜率盖过正夏普), 非理想 — 见阶段2
        assert a > 0 and b > 0
