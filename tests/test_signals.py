import pytest
import pandas as pd
import numpy as np
from signals.base import Signal, Direction, BaseStrategy
from signals.indicators import (
    SMA, RSI, MACD, ATR, BB, KDJ, AROON, CCI, OBV, VWAP, DONCHIAN, ADX,
    SUPERTREND, WILLIAMS_R, MFI, TRIX, AROON_OSCILLATOR,
)
from signals.registry import register, get_strategy, list_strategies, get_all_strategies
from signals.engine import StrategyEngine


@pytest.fixture
def ohlcv_df():
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    price = 100.0
    prices = []
    for _ in range(100):
        price *= 1 + np.random.normal(0.0005, 0.015)
        prices.append(price)
    return pd.DataFrame({"open": [p * 0.99 for p in prices], "high": [p * 1.02 for p in prices],
                          "low": [p * 0.98 for p in prices], "close": prices, "volume": np.random.randint(1000, 10000, 100)}, index=dates)


class TestIndicators:
    def test_sma_shape(self, ohlcv_df):
        r = SMA(ohlcv_df["close"], 5)
        assert len(r) == 100 and r.iloc[:4].isna().all() and not r.iloc[4:].isna().any()

    def test_rsi_bounds(self, ohlcv_df):
        r = RSI(ohlcv_df["close"], 14).dropna()
        assert r.between(0, 100).all()

    def test_macd_three_series(self, ohlcv_df):
        a, b, c = MACD(ohlcv_df["close"])
        assert all(isinstance(x, pd.Series) for x in (a, b, c))

    def test_atr_positive(self, ohlcv_df):
        assert (ATR(ohlcv_df, 14).dropna() > 0).all()

    def test_supertrend(self, ohlcv_df):
        st, direction = SUPERTREND(ohlcv_df, period=10, multiplier=3.0)
        assert isinstance(st, pd.Series)
        assert isinstance(direction, pd.Series)
        assert len(st) == len(ohlcv_df)
        assert set(direction.dropna().unique()).issubset({-1, 1})

    def test_williams_r_bounds(self, ohlcv_df):
        wr = WILLIAMS_R(ohlcv_df, 14).dropna()
        assert wr.between(-100, 0).all()

    def test_mfi_bounds(self, ohlcv_df):
        mfi = MFI(ohlcv_df, 14).dropna()
        assert mfi.between(0, 100).all()

    def test_trix(self, ohlcv_df):
        result = TRIX(ohlcv_df["close"], 15)
        assert isinstance(result, pd.Series)
        assert len(result) == len(ohlcv_df)

    def test_aroon_oscillator(self, ohlcv_df):
        result = AROON_OSCILLATOR(ohlcv_df, 14)
        assert isinstance(result, pd.Series)
        assert len(result) == len(ohlcv_df)
        assert result.dropna().between(-100, 100).all()


class TestSignal:
    def test_create(self):
        s = Signal(symbol="BTC", direction=Direction.BUY, confidence=0.85)
        assert s.symbol == "BTC" and s.confidence == 0.85

    def test_defaults(self):
        s = Signal(symbol="ETH", direction=Direction.HOLD, confidence=0.0)
        assert s.timeframe == "1d" and s.reason == ""

    def test_score_default(self):
        s = Signal(symbol="BTC", direction=Direction.BUY, confidence=0.85)
        assert s.score == 0.0

    def test_score_with_value(self):
        s = Signal(symbol="BTC", direction=Direction.BUY, confidence=0.85, score=7.5)
        assert s.score == 7.5

    def test_new_fields_defaults(self):
        s = Signal(symbol="BTC", direction=Direction.BUY, confidence=0.85)
        assert s.score == 0.0
        assert s.source_system == ""
        assert s.resonance_layer == ""
        assert s.metadata == {}

    def test_new_fields_with_values(self):
        s = Signal(
            symbol="BTC",
            direction=Direction.BUY,
            confidence=0.85,
            source_system="momentum_engine",
            resonance_layer="primary",
            metadata={"key": "value", "score": 0.9}
        )
        assert s.source_system == "momentum_engine"
        assert s.resonance_layer == "primary"
        assert s.metadata == {"key": "value", "score": 0.9}

    def test_extra_field_backward_compatible(self):
        s = Signal(
            symbol="BTC",
            direction=Direction.BUY,
            confidence=0.85,
            extra={"old_key": "old_value"}
        )
        assert s.extra == {"old_key": "old_value"}
        assert s.metadata == {}

    def test_optional_price_and_timestamp(self):
        s = Signal(symbol="BTC", direction=Direction.BUY, confidence=0.85)
        assert s.price is None
        assert s.timestamp is not None


class TestRegistry:
    def test_register_and_get(self):
        @register
        class T(BaseStrategy):
            name = "_test_reg"
            description = ""
            def compute(self, df, symbol=""): pass
        assert get_strategy("_test_reg") is T

    def test_list(self):
        assert isinstance(list_strategies(), list)

    def test_unknown(self):
        assert get_strategy("_nonexistent_xyz") is None


class TestEngine:
    def test_load_compute(self, ohlcv_df):
        e = StrategyEngine(); e.load_all()
        assert e.count > 0
        r = e.compute_all(ohlcv_df, "TEST")
        assert isinstance(r, list) and all(isinstance(x, Signal) for x in r)

    def test_named_unknown(self, ohlcv_df):
        assert StrategyEngine().compute_named("_no_exist", ohlcv_df) is None


class TestAutoloaderRegression:
    """锁定 autoloader 修复:防止 load_all() 退回到"零策略"状态。

    历史缺陷:signals/strategies/__init__.py 曾为空,没有任何地方 import
    策略模块触发 @register,导致 load_all() 在生产环境实际加载 0 个策略。
    旧测试只断言 count>0,而 TestRegistry 临时注册的 _test_reg 让该断言
    意外通过,掩盖了缺陷。这里用强断言锁死。
    """

    # 各大类至少应存在的代表性策略(autoloader 必须把它们注册进来)
    EXPECTED = [
        # 既有策略
        "trend_ma_cross", "trend_macd", "trend_adx", "trend_ichimoku",
        "breakout_donchian", "breakout_volatility", "breakout_volume",
        "momentum_roc", "momentum_cci", "momentum_obv",
        "reversal_rsi", "reversal_kdj", "reversal_bollinger",
        "filter_volatility", "filter_trend_strength", "filter_regime",
        # 新增扩展策略
        "trend_supertrend", "trend_kama", "trend_keltner_breakout",
        "trend_parabolic_sar", "trend_vortex", "trend_ttm_squeeze",
        "meanrev_zscore", "meanrev_ou", "meanrev_stoch_rsi",
        "momentum_time_series", "momentum_tsi", "momentum_vol_adjusted",
        "breakout_dual_thrust", "breakout_r_breaker", "breakout_nr7",
        "arb_pairs_zscore", "arb_ratio_spread", "arb_basis",
        "carry_roll_yield", "carry_term_structure_slope",
        "seasonality_monthly", "seasonality_day_of_week",
    ]

    def test_autoloader_registers_real_strategies(self):
        """直接 import 策略包后,注册表必须包含全部预期策略。"""
        import importlib
        import signals.strategies
        importlib.reload(signals.strategies)
        names = set(get_all_strategies().keys())
        missing = [n for n in self.EXPECTED if n not in names]
        assert not missing, f"autoloader 漏注册策略: {missing}"

    def test_engine_loads_many_strategies(self):
        """引擎实例化后应加载大量策略,而非退回零策略。"""
        e = StrategyEngine()
        e.load_all()
        # 远高于 1,确保不是只靠 TestRegistry 的临时策略
        assert e.count >= 40, f"仅加载 {e.count} 个策略,疑似 autoloader 失效"

    def test_all_loaded_strategies_instantiable(self):
        """每个注册的策略类都应能无参实例化并具备 compute 方法。"""
        for name, cls in get_all_strategies().items():
            inst = cls()
            assert hasattr(inst, "compute"), f"{name} 缺少 compute 方法"

    def test_all_strategies_run_without_crash(self, ohlcv_df):
        """全量策略在标准 OHLCV 上 compute 不得抛异常。"""
        e = StrategyEngine()
        e.load_all()
        for name in list(e._strategies.keys()):
            inst = e._strategies[name]
            try:
                result = inst.compute(ohlcv_df, "TEST")
            except Exception as exc:  # noqa: BLE001
                raise AssertionError(f"策略 {name} compute 抛异常: {exc}") from exc
            assert result is None or isinstance(result, Signal)
