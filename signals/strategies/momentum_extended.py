"""动量类策略扩展。

对齐《架构升级建议》2.1 momentum/ 目录:时序动量 / 波动率调整动量 /
TSI / CMF / Force Index / EOM / 价格加速度 / 残差动量等。
全部沿用现有 BaseStrategy + @register 模式,返回单个 Signal。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register
from signals.indicators import (
    ROC, TSI, CHAIKIN_MONEY_FLOW, FORCE_INDEX, EASE_OF_MOVEMENT, ATR, SMA, EMA,
)


@register
class MomentumTimeSeries(BaseStrategy):
    name = "momentum_time_series"
    description = "时序动量 (Moskowitz):过去 N 期收益符号"
    timeframes = ["1d"]
    params = {"lookback": 60}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        lb = self.params["lookback"]
        s = df["close"].dropna()
        if len(s) < lb + 1:
            return None
        past_ret = s.iloc[-1] / s.iloc[-1 - lb] - 1
        cv = float(s.iloc[-1])
        conf = min(abs(past_ret) * 5, 1.0)
        if past_ret > 0:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=conf,
                          price=cv, reason=f"{lb}期动量 +{past_ret:.1%}",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        if past_ret < 0:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=conf,
                          price=cv, reason=f"{lb}期动量 {past_ret:.1%}",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        return None


@register
class MomentumVolAdjusted(BaseStrategy):
    name = "momentum_vol_adjusted"
    description = "波动率调整动量:收益/波动率(类 Sharpe 动量)"
    timeframes = ["1d"]
    params = {"lookback": 60, "vol_window": 20, "threshold": 0.5}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        lb, vw = self.params["lookback"], self.params["vol_window"]
        s = df["close"].dropna()
        if len(s) < lb + 1:
            return None
        ret = np.log(s / s.shift(1))
        past_ret = np.log(s.iloc[-1] / s.iloc[-1 - lb])
        vol = ret.tail(vw).std(ddof=0) * np.sqrt(vw)
        if vol <= 0:
            return None
        score = past_ret / vol
        cv = float(s.iloc[-1])
        if score > self.params["threshold"]:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min(abs(score) / 2, 1.0), price=cv,
                          reason=f"波动调整动量={score:.2f}", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if score < -self.params["threshold"]:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min(abs(score) / 2, 1.0), price=cv,
                          reason=f"波动调整动量={score:.2f}", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None


@register
class MomentumTSI(BaseStrategy):
    name = "momentum_tsi"
    description = "True Strength Index 零轴穿越"
    timeframes = ["1d", "4h"]
    params = {"long": 25, "short": 13}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        tsi = TSI(df["close"], self.params["long"], self.params["short"]).dropna()
        if len(tsi) < 2:
            return None
        curr, prev = float(tsi.iloc[-1]), float(tsi.iloc[-2])
        cv = float(df["close"].iloc[-1])
        if prev <= 0 < curr:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min(abs(curr) / 25 + 0.3, 1.0), price=cv,
                          reason=f"TSI 上穿零轴 {curr:.1f}", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if prev >= 0 > curr:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min(abs(curr) / 25 + 0.3, 1.0), price=cv,
                          reason=f"TSI 下穿零轴 {curr:.1f}", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None


@register
class MomentumCMF(BaseStrategy):
    name = "momentum_cmf"
    description = "蔡金资金流 CMF 多空"
    timeframes = ["1d", "4h"]
    params = {"period": 20, "threshold": 0.1}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if "volume" not in df.columns:
            return None
        cmf = CHAIKIN_MONEY_FLOW(df, self.params["period"]).dropna()
        if len(cmf) < 2:
            return None
        curr, prev = float(cmf.iloc[-1]), float(cmf.iloc[-2])
        cv = float(df["close"].iloc[-1])
        t = self.params["threshold"]
        if curr > t and prev <= t:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min(abs(curr) * 3, 1.0), price=cv,
                          reason=f"CMF={curr:.2f} 资金流入", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if curr < -t and prev >= -t:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min(abs(curr) * 3, 1.0), price=cv,
                          reason=f"CMF={curr:.2f} 资金流出", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None


@register
class MomentumForceIndex(BaseStrategy):
    name = "momentum_force_index"
    description = "Elder 强力指数零轴穿越"
    timeframes = ["1d", "4h"]
    params = {"period": 13}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if "volume" not in df.columns:
            return None
        fi = FORCE_INDEX(df, self.params["period"]).dropna()
        if len(fi) < 2:
            return None
        curr, prev = float(fi.iloc[-1]), float(fi.iloc[-2])
        cv = float(df["close"].iloc[-1])
        if prev <= 0 < curr:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=0.6,
                          price=cv, reason="Force Index 转正", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if prev >= 0 > curr:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=0.6,
                          price=cv, reason="Force Index 转负", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None


@register
class MomentumAcceleration(BaseStrategy):
    name = "momentum_acceleration"
    description = "价格加速度:动量的二阶导"
    timeframes = ["1d", "4h"]
    params = {"period": 10}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        p = self.params["period"]
        roc = ROC(df["close"], p).dropna()
        if len(roc) < 3:
            return None
        accel = roc.diff().dropna()
        if len(accel) < 1:
            return None
        a_now = float(accel.iloc[-1])
        m_now = float(roc.iloc[-1])
        cv = float(df["close"].iloc[-1])
        if m_now > 0 and a_now > 0:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min(abs(a_now) / 5, 1.0), price=cv,
                          reason=f"动量加速 a={a_now:.2f}", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if m_now < 0 and a_now < 0:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min(abs(a_now) / 5, 1.0), price=cv,
                          reason=f"动量加速向下 a={a_now:.2f}", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None
