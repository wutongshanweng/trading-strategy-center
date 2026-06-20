"""套利策略增强版 — 补充 arbitrage_carry.py 之外的套利变体。

延续 arbitrage_carry 的约定:跨品种/配对策略从 df 的 'close2' 列读取第二条腿,
无 'close2' 列则安全降级返回 None。
"""
from __future__ import annotations

import pandas as pd

from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register
from signals.indicators import ZSCORE


@register
class ArbVolSpread(BaseStrategy):
    name = "arb_vol_spread"
    description = "波动率价差套利:两腿已实现波动率之差的均值回归(需 close2 列)"
    timeframes = ["1d"]
    params = {"vol_window": 20, "z_window": 60, "entry_z": 2.0}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if "close2" not in df.columns:
            return None
        vw = self.params["vol_window"]
        v1 = df["close"].pct_change().rolling(vw).std()
        v2 = df["close2"].pct_change().rolling(vw).std()
        spread = (v1 - v2).dropna()
        if len(spread) < self.params["z_window"]:
            return None
        z = ZSCORE(spread, self.params["z_window"]).dropna()
        if z.empty:
            return None
        zv = float(z.iloc[-1])
        cv = float(df["close"].iloc[-1])
        entry = self.params["entry_z"]
        if zv > entry:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min((zv - entry) / 2 + 0.3, 1.0), price=cv,
                          reason=f"波动率价差 Z={zv:.2f} 偏高,做空价差",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          metadata={"vol_spread_z": zv})
        if zv < -entry:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min((-zv - entry) / 2 + 0.3, 1.0), price=cv,
                          reason=f"波动率价差 Z={zv:.2f} 偏低,做多价差",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          metadata={"vol_spread_z": zv})
        return None


@register
class ArbCorrelationBreak(BaseStrategy):
    name = "arb_correlation_break"
    description = "相关性破裂套利:两腿滚动相关性骤降时的价差回归机会(需 close2 列)"
    timeframes = ["1d"]
    params = {"corr_window": 30, "corr_floor": 0.3, "z_window": 60, "entry_z": 1.5}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if "close2" not in df.columns:
            return None
        cw = self.params["corr_window"]
        r1 = df["close"].pct_change()
        r2 = df["close2"].pct_change()
        corr = r1.rolling(cw).corr(r2)
        if corr.dropna().empty:
            return None
        corr_now = float(corr.dropna().iloc[-1])
        # 仅在当前相关性破裂(低于地板)时才认为价差回归可交易
        if corr_now > self.params["corr_floor"]:
            return None
        spread = (df["close"] - df["close2"]).dropna()
        if len(spread) < self.params["z_window"]:
            return None
        z = ZSCORE(spread, self.params["z_window"]).dropna()
        if z.empty:
            return None
        zv = float(z.iloc[-1])
        cv = float(df["close"].iloc[-1])
        entry = self.params["entry_z"]
        if zv > entry:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min((zv - entry) / 2 + 0.3, 1.0), price=cv,
                          reason=f"相关破裂(corr={corr_now:.2f}) 且价差 Z={zv:.2f} 偏高",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          metadata={"corr": corr_now, "spread_z": zv})
        if zv < -entry:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min((-zv - entry) / 2 + 0.3, 1.0), price=cv,
                          reason=f"相关破裂(corr={corr_now:.2f}) 且价差 Z={zv:.2f} 偏低",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          metadata={"corr": corr_now, "spread_z": zv})
        return None
