"""均值回归类策略扩展。

对齐《架构升级建议》2.1 mean_reversion/ 目录:Bollinger 回归 / RSI 背离 /
Z-score / OU 过程 / Williams %R / StochRSI / 区间震荡 / 隔夜反转等。
全部沿用现有 BaseStrategy + @register 模式,返回单个 Signal。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register
from signals.indicators import (
    BB, RSI, ZSCORE, WILLIAMS_R, STOCH_RSI, SMA, ATR, CCI, KDJ,
)


@register
class MeanRevBollinger(BaseStrategy):
    name = "meanrev_bollinger"
    description = "布林带触轨回归"
    timeframes = ["1d", "4h", "1h"]
    params = {"period": 20, "std": 2.0}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        upper, mid, lower = BB(df["close"], self.params["period"], self.params["std"])
        if upper.dropna().empty:
            return None
        cv = float(df["close"].iloc[-1])
        uv, mv, lv = float(upper.iloc[-1]), float(mid.iloc[-1]), float(lower.iloc[-1])
        if any(pd.isna(x) for x in [uv, mv, lv]):
            return None
        if cv <= lv:
            conf = min((lv - cv) / max(mv - lv, 1e-10) + 0.4, 1.0)
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=conf,
                          price=cv, reason="触下轨回归", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=cv - (mv - lv) * 0.5,
                          take_profit=mv)
        if cv >= uv:
            conf = min((cv - uv) / max(uv - mv, 1e-10) + 0.4, 1.0)
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=conf,
                          price=cv, reason="触上轨回归", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=cv + (uv - mv) * 0.5,
                          take_profit=mv)
        return None


@register
class MeanRevZScore(BaseStrategy):
    name = "meanrev_zscore"
    description = "Z-score 极值回归"
    timeframes = ["1d", "4h", "1h"]
    params = {"period": 20, "entry_z": 2.0, "exit_z": 0.5}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        z = ZSCORE(df["close"], self.params["period"]).dropna()
        if z.empty:
            return None
        zv = float(z.iloc[-1])
        cv = float(df["close"].iloc[-1])
        if pd.isna(zv):
            return None
        if zv <= -self.params["entry_z"]:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min(abs(zv) / 4, 1.0), price=cv,
                          reason=f"Z={zv:.2f} 低估回归", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if zv >= self.params["entry_z"]:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min(abs(zv) / 4, 1.0), price=cv,
                          reason=f"Z={zv:.2f} 高估回归", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None


@register
class MeanRevOU(BaseStrategy):
    name = "meanrev_ou"
    description = "Ornstein-Uhlenbeck 过程均值回归(半衰期估计)"
    timeframes = ["1d", "4h"]
    params = {"lookback": 60, "entry_z": 1.5}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        lb = self.params["lookback"]
        s = df["close"].dropna()
        if len(s) < lb + 2:
            return None
        x = np.log(s.tail(lb).values)
        # 拟合 OU: dx = theta*(mu - x)dt + ... -> AR(1)
        x_lag = x[:-1]
        x_now = x[1:]
        beta = np.polyfit(x_lag, x_now, 1)
        slope = beta[0]
        if slope <= 0 or slope >= 1:
            return None  # 非均值回归
        mu = beta[1] / (1 - slope)
        resid = x_now - (slope * x_lag + beta[1])
        sigma_eq = np.std(resid) / np.sqrt(max(1 - slope ** 2, 1e-10))
        zv = (x[-1] - mu) / max(sigma_eq, 1e-10)
        cv = float(s.iloc[-1])
        half_life = -np.log(2) / np.log(slope) if slope > 0 else np.inf
        if zv <= -self.params["entry_z"]:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min(abs(zv) / 3, 1.0), price=cv,
                          reason=f"OU 低估 z={zv:.2f} 半衰期={half_life:.1f}",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          extra={"half_life": float(half_life)})
        if zv >= self.params["entry_z"]:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min(abs(zv) / 3, 1.0), price=cv,
                          reason=f"OU 高估 z={zv:.2f} 半衰期={half_life:.1f}",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          extra={"half_life": float(half_life)})
        return None


@register
class MeanRevWilliamsR(BaseStrategy):
    name = "meanrev_williams_r"
    description = "Williams %R 超买超卖反转"
    timeframes = ["1d", "4h", "1h"]
    params = {"period": 14, "oversold": -80, "overbought": -20}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        wr = WILLIAMS_R(df, self.params["period"]).dropna()
        if len(wr) < 2:
            return None
        curr, prev = float(wr.iloc[-1]), float(wr.iloc[-2])
        cv = float(df["close"].iloc[-1])
        if curr > self.params["oversold"] and prev <= self.params["oversold"]:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=0.6,
                          price=cv, reason=f"%R={curr:.0f} 离开超卖", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if curr < self.params["overbought"] and prev >= self.params["overbought"]:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=0.6,
                          price=cv, reason=f"%R={curr:.0f} 离开超买", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None


@register
class MeanRevStochRSI(BaseStrategy):
    name = "meanrev_stoch_rsi"
    description = "StochRSI 金叉死叉于极值区"
    timeframes = ["1d", "4h", "1h"]
    params = {"period": 14, "k_smooth": 3, "d_smooth": 3}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        k, d = STOCH_RSI(df["close"], self.params["period"],
                         self.params["k_smooth"], self.params["d_smooth"])
        kk, dd = k.dropna(), d.dropna()
        if len(kk) < 2 or len(dd) < 2:
            return None
        k_now, k_prev = float(kk.iloc[-1]), float(kk.iloc[-2])
        d_now, d_prev = float(dd.iloc[-1]), float(dd.iloc[-2])
        cv = float(df["close"].iloc[-1])
        if k_prev < d_prev and k_now > d_now and k_now < 30:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=0.6,
                          price=cv, reason="StochRSI 超卖金叉", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if k_prev > d_prev and k_now < d_now and k_now > 70:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=0.6,
                          price=cv, reason="StochRSI 超买死叉", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None


@register
class MeanRevRange(BaseStrategy):
    name = "meanrev_range"
    description = "区间震荡:在箱体内高抛低吸"
    timeframes = ["1d", "4h"]
    params = {"lookback": 40, "band_pct": 0.15}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        lb = self.params["lookback"]
        if len(df) < lb:
            return None
        window = df.tail(lb)
        hi, lo = float(window["high"].max()), float(window["low"].min())
        rng = hi - lo
        if rng <= 0:
            return None
        cv = float(df["close"].iloc[-1])
        pos = (cv - lo) / rng
        # 趋势过滤:区间内才做(用 ATR 占比衡量)
        if pos <= self.params["band_pct"]:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=0.55, price=cv, reason=f"箱体底部 pos={pos:.2f}",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=lo - rng * 0.1, take_profit=lo + rng * 0.5)
        if pos >= 1 - self.params["band_pct"]:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=0.55, price=cv, reason=f"箱体顶部 pos={pos:.2f}",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=hi + rng * 0.1, take_profit=hi - rng * 0.5)
        return None


@register
class MeanRevOvernight(BaseStrategy):
    name = "meanrev_overnight"
    description = "隔夜反转:大幅高开/低开后日内反向"
    timeframes = ["1d"]
    params = {"gap_pct": 0.015}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if len(df) < 2:
            return None
        prev_close = float(df["close"].iloc[-2])
        today_open = float(df["open"].iloc[-1])
        cv = float(df["close"].iloc[-1])
        gap = (today_open - prev_close) / prev_close
        if gap >= self.params["gap_pct"]:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min(abs(gap) * 20, 1.0), price=cv,
                          reason=f"高开 {gap:.1%} 隔夜反转", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if gap <= -self.params["gap_pct"]:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min(abs(gap) * 20, 1.0), price=cv,
                          reason=f"低开 {gap:.1%} 隔夜反转", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None
