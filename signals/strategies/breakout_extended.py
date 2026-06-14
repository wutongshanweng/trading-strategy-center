"""突破类策略扩展。

对齐《架构升级建议》2.1 breakout/ 目录:Dual Thrust / R-Breaker /
开盘区间突破 / 窄幅N日突破 / 内包线突破 / 创新高新低等。
全部沿用现有 BaseStrategy + @register 模式,返回单个 Signal。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register
from signals.indicators import ATR, DONCHIAN


@register
class BreakoutDualThrust(BaseStrategy):
    name = "breakout_dual_thrust"
    description = "Dual Thrust:基于前N日区间的上下轨突破"
    timeframes = ["1d"]
    params = {"n": 4, "k1": 0.5, "k2": 0.5}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        n = self.params["n"]
        if len(df) < n + 1:
            return None
        window = df.iloc[-n - 1:-1]
        hh = window["high"].max()
        lc = window["close"].min()
        hc = window["close"].max()
        ll = window["low"].min()
        rng = max(hh - lc, hc - ll)
        today_open = float(df["open"].iloc[-1])
        cv = float(df["close"].iloc[-1])
        upper = today_open + self.params["k1"] * rng
        lower = today_open - self.params["k2"] * rng
        if cv > upper:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min((cv - upper) / max(rng, 1e-9), 1.0), price=cv,
                          reason="Dual Thrust 上轨突破", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=lower)
        if cv < lower:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min((lower - cv) / max(rng, 1e-9), 1.0), price=cv,
                          reason="Dual Thrust 下轨突破", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=upper)
        return None


@register
class BreakoutRBreaker(BaseStrategy):
    name = "breakout_r_breaker"
    description = "R-Breaker:基于前一日 HLC 的六档支撑阻力"
    timeframes = ["1d"]
    params = {"setup_coef": 0.35, "break_coef": 0.25}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if len(df) < 2:
            return None
        prev = df.iloc[-2]
        high, low, close = float(prev["high"]), float(prev["low"]), float(prev["close"])
        pivot = (high + low + close) / 3
        s = self.params["setup_coef"]
        b_ssetup = pivot + s * (high - low)      # 观察卖出价
        b_bsetup = pivot - s * (high - low)      # 观察买入价
        cv = float(df["close"].iloc[-1])
        rng = high - low
        if cv > b_ssetup:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min((cv - b_ssetup) / max(rng, 1e-9), 1.0), price=cv,
                          reason="R-Breaker 突破观察卖出价(顺势做多)",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=pivot)
        if cv < b_bsetup:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min((b_bsetup - cv) / max(rng, 1e-9), 1.0), price=cv,
                          reason="R-Breaker 跌破观察买入价(顺势做空)",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=pivot)
        return None


@register
class BreakoutNR7(BaseStrategy):
    name = "breakout_nr7"
    description = "NR7 窄幅日突破:7日最窄区间后的方向突破"
    timeframes = ["1d"]
    params = {"n": 7}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        n = self.params["n"]
        if len(df) < n + 1:
            return None
        rng = (df["high"] - df["low"])
        window = rng.iloc[-n - 1:-1]
        prev_range = rng.iloc[-2]
        if prev_range > window.min() * 1.0001:  # 前一日须为最窄
            return None
        prev = df.iloc[-2]
        cv = float(df["close"].iloc[-1])
        if cv > float(prev["high"]):
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=0.65,
                          price=cv, reason="NR7 向上突破", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=float(prev["low"]))
        if cv < float(prev["low"]):
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=0.65,
                          price=cv, reason="NR7 向下突破", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=float(prev["high"]))
        return None


@register
class BreakoutInsideBar(BaseStrategy):
    name = "breakout_inside_bar"
    description = "内包线突破:母线包含子线后的方向选择"
    timeframes = ["1d", "4h"]
    params = {}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if len(df) < 3:
            return None
        mother = df.iloc[-3]
        inside = df.iloc[-2]
        is_inside = (float(inside["high"]) < float(mother["high"]) and
                     float(inside["low"]) > float(mother["low"]))
        if not is_inside:
            return None
        cv = float(df["close"].iloc[-1])
        if cv > float(mother["high"]):
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=0.6,
                          price=cv, reason="内包线向上突破母线", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=float(inside["low"]))
        if cv < float(mother["low"]):
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=0.6,
                          price=cv, reason="内包线向下突破母线", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=float(inside["high"]))
        return None


@register
class BreakoutNewHighLow(BaseStrategy):
    name = "breakout_new_high_low"
    description = "创 N 日新高/新低突破"
    timeframes = ["1d", "4h"]
    params = {"period": 55}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        p = self.params["period"]
        if len(df) < p + 1:
            return None
        prior_high = df["high"].iloc[-p - 1:-1].max()
        prior_low = df["low"].iloc[-p - 1:-1].min()
        cv = float(df["close"].iloc[-1])
        atr = ATR(df, 14).dropna()
        stop_dist = float(atr.iloc[-1]) * 2 if not atr.empty else cv * 0.03
        if cv > prior_high:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=0.7,
                          price=cv, reason=f"创{p}日新高", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=cv - stop_dist)
        if cv < prior_low:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=0.7,
                          price=cv, reason=f"创{p}日新低", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=cv + stop_dist)
        return None
