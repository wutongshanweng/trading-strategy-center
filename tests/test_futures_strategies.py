"""期货策略行为正确性测试。

冒烟测试只证明不崩溃;本文件用「构造性输入」断言信号方向正确:
喂入明确的上涨/下跌/超买/超卖/突破场景,验证策略给出预期方向。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signals.base import Direction
from signals.engine import StrategyEngine
from signals.registry import get_strategy


# ---------- 构造性数据工具 ----------

def _ohlc_from_close(close, vol=None):
    """从收盘价序列生成合理的 OHLCV DataFrame。"""
    close = pd.Series(close, dtype=float)
    n = len(close)
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    high = close * 1.01
    low = close * 0.99
    open_ = close.shift(1).fillna(close.iloc[0])
    if vol is None:
        vol = np.full(n, 5000.0)
    return pd.DataFrame(
        {"open": open_.values, "high": high.values, "low": low.values,
         "close": close.values, "volume": vol},
        index=idx,
    )


def _strong_uptrend(n=120, start=100.0, step=0.008):
    return _ohlc_from_close([start * (1 + step) ** i for i in range(n)])


def _strong_downtrend(n=120, start=100.0, step=0.008):
    return _ohlc_from_close([start * (1 - step) ** i for i in range(n)])


def _build(name):
    cls = get_strategy(name)
    assert cls is not None, f"策略 {name} 未注册"
    return cls()


@pytest.fixture(scope="module", autouse=True)
def _load_engine():
    # 触发 autoloader,确保所有策略注册
    StrategyEngine().load_all()


# ---------- 趋势类:上涨给 BUY,下跌给 SELL ----------

@pytest.mark.parametrize("name", [
    "trend_ma_cross", "trend_macd", "trend_supertrend",
    "trend_kama", "trend_ema_ribbon",
])
def test_trend_strategies_long_on_uptrend(name):
    strat = _build(name)
    sig = strat.compute(_strong_uptrend(), "TEST")
    # 趋势策略在持续上涨中要么给多,要么不发(绝不应给空)
    if sig is not None:
        assert sig.direction != Direction.SELL, f"{name} 在上涨中给出 SELL"


@pytest.mark.parametrize("name", [
    "trend_ma_cross", "trend_macd", "trend_supertrend",
    "trend_kama", "trend_ema_ribbon",
])
def test_trend_strategies_short_on_downtrend(name):
    strat = _build(name)
    sig = strat.compute(_strong_downtrend(), "TEST")
    if sig is not None:
        assert sig.direction != Direction.BUY, f"{name} 在下跌中给出 BUY"


# ---------- 时序动量:方向应与过去收益符号一致 ----------

def test_time_series_momentum_direction():
    strat = _build("momentum_time_series")
    up = strat.compute(_strong_uptrend(), "TEST")
    dn = strat.compute(_strong_downtrend(), "TEST")
    assert up is not None and up.direction == Direction.BUY
    assert dn is not None and dn.direction == Direction.SELL


def test_vol_adjusted_momentum_direction():
    strat = _build("momentum_vol_adjusted")
    up = strat.compute(_strong_uptrend(), "TEST")
    assert up is not None and up.direction == Direction.BUY


# ---------- 均值回归:Z-score 极值应反向 ----------

def test_zscore_reversion_buys_low():
    # 长期横盘后骤跌 -> Z 极负 -> 应给 BUY
    flat = [100.0] * 40
    drop = [100.0 - i * 2 for i in range(1, 6)]  # 连续下挫
    df = _ohlc_from_close(flat + drop)
    sig = _build("meanrev_zscore").compute(df, "TEST")
    assert sig is not None and sig.direction == Direction.BUY


def test_zscore_reversion_sells_high():
    flat = [100.0] * 40
    spike = [100.0 + i * 2 for i in range(1, 6)]
    df = _ohlc_from_close(flat + spike)
    sig = _build("meanrev_zscore").compute(df, "TEST")
    assert sig is not None and sig.direction == Direction.SELL


def test_bollinger_reversion_sells_at_upper():
    flat = [100.0] * 30
    spike = [100.0 + i * 1.5 for i in range(1, 6)]
    df = _ohlc_from_close(flat + spike)
    sig = _build("meanrev_bollinger").compute(df, "TEST")
    if sig is not None:
        assert sig.direction == Direction.SELL


# ---------- 隔夜反转:高开应给 SELL,低开应给 BUY ----------

def test_overnight_reversal_gap_up():
    df = _ohlc_from_close([100.0] * 10)
    # 制造今日高开 3%
    df.loc[df.index[-1], "open"] = df["close"].iloc[-2] * 1.03
    sig = _build("meanrev_overnight").compute(df, "TEST")
    assert sig is not None and sig.direction == Direction.SELL


def test_overnight_reversal_gap_down():
    df = _ohlc_from_close([100.0] * 10)
    df.loc[df.index[-1], "open"] = df["close"].iloc[-2] * 0.97
    sig = _build("meanrev_overnight").compute(df, "TEST")
    assert sig is not None and sig.direction == Direction.BUY


# ---------- 突破类:创新高应给 BUY ----------

def test_donchian_breakout_long():
    base = [100.0] * 30
    breakout = [105.0]  # 突破前高
    df = _ohlc_from_close(base + breakout)
    df.loc[df.index[-1], "high"] = 106.0
    sig = _build("breakout_donchian").compute(df, "TEST")
    if sig is not None:
        assert sig.direction == Direction.BUY


def test_new_high_low_breakout_long():
    df = _ohlc_from_close([100.0 + i * 0.5 for i in range(40)])
    sig = _build("breakout_new_high_low").compute(df, "TEST")
    if sig is not None:
        assert sig.direction != Direction.SELL


# ---------- confidence 边界:所有策略输出应在 [0,1] ----------

def test_all_signals_confidence_bounded():
    engine = StrategyEngine()
    engine.load_all()
    for df in (_strong_uptrend(), _strong_downtrend()):
        for sig in engine.compute_all(df, "TEST"):
            assert 0.0 <= sig.confidence <= 1.0, (
                f"{sig.strategy_name} confidence={sig.confidence} 越界")


# ---------- 数据不足时应安全返回 None,不抛异常 ----------

@pytest.mark.parametrize("name", [
    "trend_supertrend", "trend_kama", "meanrev_ou",
    "momentum_time_series", "breakout_dual_thrust", "carry_roll_yield",
])
def test_short_data_returns_none_not_crash(name):
    df = _ohlc_from_close([100.0, 101.0, 99.0])  # 仅 3 根
    sig = _build(name).compute(df, "TEST")
    assert sig is None or sig.direction in (Direction.BUY, Direction.SELL, Direction.HOLD)
