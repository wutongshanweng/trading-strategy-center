"""Phase4 A篇 — 策略目录 + C篇 反馈闭环 测试。"""

from signals.catalog import StrategyCatalog, StrategyType, RegimeFit
from core.feedback_loop import FeedbackLoop
from core.feedback_config import FeedbackConfig


def _catalog():
    c = StrategyCatalog()
    c.build_from_registry()
    return c


class TestStrategyCatalog:
    def test_build_collects_strategies(self):
        c = _catalog()
        assert len(c.all()) >= 40  # 已有数十个策略

    def test_type_inference(self):
        c = _catalog()
        ma = c.get("trend_ma_cross")
        assert ma is not None and ma.strategy_type == StrategyType.TREND
        roc = c.get("momentum_roc")
        assert roc is not None and roc.strategy_type == StrategyType.MOMENTUM

    def test_query_by_type(self):
        c = _catalog()
        trends = c.query(strategy_type="trend", top_k=100, active_only=False)
        assert len(trends) >= 4
        assert all(s.strategy_type == StrategyType.TREND for s in trends)

    def test_query_by_regime(self):
        c = _catalog()
        res = c.query(regime="trending", top_k=200, active_only=False)
        # trend/momentum/breakout + ALL 类都应匹配
        assert len(res) > 0

    def test_update_performance_and_best_for(self):
        c = _catalog()
        c.update_performance("trend_ma_cross", sharpe=1.5, win_rate=0.6,
                             total_trades=40, symbol="RB2510")
        assert c.get("trend_ma_cross").sharpe == 1.5
        best = c.best_for("RB2510")
        assert best and best[0].name == "trend_ma_cross"

    def test_new_arbitrage_extended_registered(self):
        c = _catalog()
        assert c.get("arb_vol_spread") is not None
        assert c.get("arb_correlation_break") is not None

    def test_performance_persistence(self, tmp_path):
        # #4: save/load 往返
        store = str(tmp_path / "perf.json")
        c1 = StrategyCatalog(store_path=store)
        c1.build_from_registry()
        c1.update_performance("trend_ma_cross", sharpe=1.7, total_trades=20, symbol="RB")
        # 新实例从同一路径加载, 表现应恢复
        c2 = StrategyCatalog(store_path=store)
        c2.build_from_registry()
        assert c2.get("trend_ma_cross").sharpe == 1.7
        assert c2.get("trend_ma_cross").total_trades == 20


class TestFeedbackLoop:
    def test_process_updates_catalog(self):
        c = _catalog()
        loop = FeedbackLoop(catalog=c, config=FeedbackConfig())
        results = {"id": "T1", "strategies": [
            {"name": "trend_ma_cross", "sharpe": 1.5, "win_rate": 0.6,
             "total_trades": 50, "symbol": "RB2510"},
            {"name": "momentum_roc", "sharpe": -0.8, "win_rate": 0.3, "total_trades": 30},
        ]}
        entry = loop.process_tournament_results(results)
        assert entry.top_strategy == "trend_ma_cross"
        assert entry.worst_strategy == "momentum_roc"
        assert "momentum_roc" in entry.strategies_retired
        assert "trend_ma_cross" in entry.strategies_starred
        assert c.get("trend_ma_cross").sharpe == 1.5
        # 验收6: 赛后 catalog 表现更新
        assert c.get("momentum_roc").is_active is False

    def test_retire_needs_min_trades(self):
        c = _catalog()
        loop = FeedbackLoop(catalog=c)
        # 夏普低但交易数不足 → 不下线
        loop.process_tournament_results({"id": "T2", "strategies": [
            {"name": "reversal_rsi", "sharpe": -0.9, "total_trades": 3}]})
        assert c.get("reversal_rsi").is_active is True

    def test_history(self, tmp_path):
        loop = FeedbackLoop(catalog=_catalog(), store_path=str(tmp_path / "h.json"))
        loop.process_tournament_results({"id": "A", "strategies": []})
        loop.process_tournament_results({"id": "B", "strategies": []})
        assert len(loop.get_history()) == 2

    def test_history_persistence(self, tmp_path):
        # #3: 反馈历史持久化往返
        store = str(tmp_path / "fb.json")
        loop1 = FeedbackLoop(catalog=_catalog(), store_path=store)
        loop1.process_tournament_results({"id": "X", "strategies": [
            {"name": "trend_ma_cross", "sharpe": 1.1, "total_trades": 20}]})
        loop2 = FeedbackLoop(catalog=_catalog(), store_path=store)
        assert len(loop2.get_history()) == 1
        assert loop2.get_history()[0].tournament_id == "X"
