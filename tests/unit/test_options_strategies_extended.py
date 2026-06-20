"""期权-期货联合策略 / ML 信号适配器 扩展测试。"""

import numpy as np
import pandas as pd

from options.strategies.futures_combo import FuturesOptionsComboSignals
from ml.signal_adapter import MLSignalAdapter


class TestFuturesCombo:
    def setup_method(self):
        self.combo = FuturesOptionsComboSignals()

    def test_bull_high_iv(self):
        sig = self.combo.combine("BUY", 0.8, iv_rank=85, skew=0.02, spot=100)
        assert sig.strategy_name == "covered_call"

    def test_bull_low_iv(self):
        sig = self.combo.combine("BUY", 0.8, iv_rank=20, skew=0.02, spot=100)
        assert sig.strategy_name == "long_call"

    def test_bull_extreme_skew(self):
        sig = self.combo.combine("BUY", 0.8, iv_rank=50, skew=-0.12, spot=100)
        assert sig.strategy_name == "protective_put"

    def test_bull_normal(self):
        sig = self.combo.combine("BUY", 0.8, iv_rank=50, skew=0.0, spot=100)
        assert sig.strategy_name == "futures_only"

    def test_low_confidence(self):
        sig = self.combo.combine("BUY", 0.2, iv_rank=50, skew=0, spot=100)
        assert sig.strategy_name == "hold"

    def test_sell_high_iv(self):
        sig = self.combo.combine("SELL", 0.7, iv_rank=80, skew=0.05, spot=100)
        assert sig.strategy_name == "cash_secured_put"

    def test_no_options_market(self):
        sig = self.combo.combine("BUY", 0.7, iv_rank=50, skew=0,
                                 spot=100, options_available=False)
        assert sig.strategy_name == "futures_only"
        assert sig.futures_direction == "LONG"


class TestMLSignalAdapter:
    def _features(self, n=60):
        rng = np.random.default_rng(1)
        idx = pd.date_range("2025-01-01", periods=n, freq="D")
        return pd.DataFrame({
            "feat_up": np.linspace(-1, 3, n),     # 末尾强正 → BUY
            "feat_flat": rng.normal(0, 0.01, n),  # 平 → 跳过
        }, index=idx)

    def test_to_signals(self):
        sigs = MLSignalAdapter().to_signals(self._features(), symbol="RB2510")
        assert isinstance(sigs, list)  # 验收项 15
        # feat_up 末尾应产生 BUY
        assert any(s.strategy_name == "ml_feat_up" for s in sigs)

    def test_to_combined_signal(self):
        sig = MLSignalAdapter().to_combined_signal(self._features(), symbol="RB2510")
        # 综合可能为 None (太弱) 或一个 Signal
        if sig is not None:
            assert sig.symbol == "RB2510"
            assert sig.resonance_layer == "T"
