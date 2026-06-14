"""趋势类策略扩展(CTA 主力)。

对齐《架构升级建议》2.1 trend/ 目录:SuperTrend / KAMA / Keltner /
Parabolic SAR / Vortex / Aroon / TTM Squeeze / 多周期趋势等。
全部沿用现有 BaseStrategy + @register 模式,返回单个 Signal。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register
from signals.indicators import (
    SMA, EMA, ATR, SUPERTREND, KAMA, KELTNER, PARABOLIC_SAR,
    VORTEX, AROON, AROON_OSCILLATOR, TTM_SQUEEZE, DI_PLUS_MINUS, DONCHIAN,
)


@register
class TrendSupertrend(BaseStrategy):
    name = "trend_supertrend"
    description = "SuperTrend (ATR 通道) 跟踪趋势"
    timeframes = ["1d", "4h", "1h"]
    params = {"period": 10, "multiplier": 3.0}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        st, direction = SUPERTREND(df, self.params["period"], self.params["multiplier"])
        d = direction.dropna()
        if len(d) < 2:
            return None
        curr, prev = d.iloc[-1], d.iloc[-2]
        close = float(df["close"].iloc[-1])
        st_clean = st.dropna()
        if st_clean.empty:
            return None
        st_v = float(st_clean.iloc[-1])
        if curr == 1 and prev == -1:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=0.7,
                          price=close, reason="SuperTrend 翻多", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=st_v, take_profit=close * 1.06)
        if curr == -1 and prev == 1:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=0.7,
                          price=close, reason="SuperTrend 翻空", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=st_v, take_profit=close * 0.94)
        return None


@register
class TrendKama(BaseStrategy):
    name = "trend_kama"
    description = "Kaufman 自适应均线方向"
    timeframes = ["1d", "4h"]
    params = {"period": 10, "fast": 2, "slow": 30, "slope_lb": 3}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        kama = KAMA(df["close"], self.params["period"], self.params["fast"], self.params["slow"]).dropna()
        lb = self.params["slope_lb"]
        if len(kama) < lb + 1:
            return None
        slope = (kama.iloc[-1] - kama.iloc[-1 - lb]) / max(abs(kama.iloc[-1 - lb]), 1e-10)
        close = float(df["close"].iloc[-1])
        if slope > 0.002 and close > kama.iloc[-1]:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=min(abs(slope) * 50, 1.0),
                          price=close, reason=f"KAMA 上行 slope={slope:.4f}", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=float(kama.iloc[-1]))
        if slope < -0.002 and close < kama.iloc[-1]:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=min(abs(slope) * 50, 1.0),
                          price=close, reason=f"KAMA 下行 slope={slope:.4f}", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=float(kama.iloc[-1]))
        return None


@register
class TrendKeltnerBreakout(BaseStrategy):
    name = "trend_keltner_breakout"
    description = "Keltner 通道突破"
    timeframes = ["1d", "4h", "1h"]
    params = {"period": 20, "mult": 2.0}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        upper, mid, lower = KELTNER(df, self.params["period"], self.params["mult"])
        if upper.dropna().empty:
            return None
        close = float(df["close"].iloc[-1])
        uv, mv, lv = float(upper.iloc[-1]), float(mid.iloc[-1]), float(lower.iloc[-1])
        if close > uv:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=min((close - uv) / (uv - mv + 1e-10), 1.0),
                          price=close, reason="Keltner 上轨突破", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=mv)
        if close < lv:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=min((lv - close) / (mv - lv + 1e-10), 1.0),
                          price=close, reason="Keltner 下轨突破", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=mv)
        return None


@register
class TrendParabolicSar(BaseStrategy):
    name = "trend_parabolic_sar"
    description = "抛物线 SAR 翻转"
    timeframes = ["1d", "4h", "1h"]
    params = {"af_step": 0.02, "af_max": 0.2}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        sar = PARABOLIC_SAR(df, self.params["af_step"], self.params["af_max"])
        if len(sar) < 2:
            return None
        close = float(df["close"].iloc[-1])
        prev_close = float(df["close"].iloc[-2])
        sar_v, sar_prev = float(sar.iloc[-1]), float(sar.iloc[-2])
        # SAR 由上方翻到下方 = 转多
        if sar_prev > prev_close and sar_v < close:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=0.65,
                          price=close, reason="SAR 翻多", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=sar_v)
        if sar_prev < prev_close and sar_v > close:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=0.65,
                          price=close, reason="SAR 翻空", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=sar_v)
        return None


@register
class TrendVortex(BaseStrategy):
    name = "trend_vortex"
    description = "涡旋指标 VI+ / VI- 交叉"
    timeframes = ["1d", "4h"]
    params = {"period": 14}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        vi_p, vi_m = VORTEX(df, self.params["period"])
        diff = (vi_p - vi_m).dropna()
        if len(diff) < 2:
            return None
        curr, prev = diff.iloc[-1], diff.iloc[-2]
        close = float(df["close"].iloc[-1])
        if prev < 0 and curr > 0:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=min(abs(curr) * 2, 1.0),
                          price=close, reason="Vortex VI+ 上穿 VI-", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if prev > 0 and curr < 0:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=min(abs(curr) * 2, 1.0),
                          price=close, reason="Vortex VI- 上穿 VI+", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None


@register
class TrendAroon(BaseStrategy):
    name = "trend_aroon"
    description = "Aroon 振荡器趋势"
    timeframes = ["1d", "4h"]
    params = {"period": 25, "threshold": 50}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        osc = AROON_OSCILLATOR(df, self.params["period"]).dropna()
        if osc.empty:
            return None
        v = float(osc.iloc[-1])
        close = float(df["close"].iloc[-1])
        if v > self.params["threshold"]:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=min(v / 100, 1.0),
                          price=close, reason=f"Aroon 强上行 {v:.0f}", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if v < -self.params["threshold"]:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=min(abs(v) / 100, 1.0),
                          price=close, reason=f"Aroon 强下行 {v:.0f}", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None


@register
class TrendTtmSqueeze(BaseStrategy):
    name = "trend_ttm_squeeze"
    description = "TTM 挤压释放方向突破"
    timeframes = ["1d", "4h"]
    params = {"period": 20, "bb_mult": 2.0, "kc_mult": 1.5}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        squeeze_on, momentum = TTM_SQUEEZE(df, self.params["period"], self.params["bb_mult"], self.params["kc_mult"])
        if len(squeeze_on.dropna()) < 2 or momentum.dropna().empty:
            return None
        close = float(df["close"].iloc[-1])
        # 挤压刚释放(上一根挤压、当前解除)且动量为正/负
        just_fired = bool(squeeze_on.iloc[-2]) and not bool(squeeze_on.iloc[-1])
        mom = float(momentum.iloc[-1])
        if just_fired and mom > 0:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=0.7,
                          price=close, reason="TTM 挤压释放-多", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if just_fired and mom < 0:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=0.7,
                          price=close, reason="TTM 挤压释放-空", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None


@register
class TrendDmi(BaseStrategy):
    name = "trend_dmi"
    description = "DMI +DI/-DI 多空趋势"
    timeframes = ["1d", "4h", "1h"]
    params = {"period": 14}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        pdi, ndi = DI_PLUS_MINUS(df, self.params["period"])
        diff = (pdi - ndi).dropna()
        if len(diff) < 2:
            return None
        curr, prev = diff.iloc[-1], diff.iloc[-2]
        close = float(df["close"].iloc[-1])
        if prev < 0 and curr > 0:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=min(abs(curr) / 30, 1.0),
                          price=close, reason="+DI 上穿 -DI", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if prev > 0 and curr < 0:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=min(abs(curr) / 30, 1.0),
                          price=close, reason="-DI 上穿 +DI", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None


@register
class TrendEmaRibbon(BaseStrategy):
    name = "trend_ema_ribbon"
    description = "均线带 (5/10/20/60) 多头排列"
    timeframes = ["1d", "4h"]
    params = {"periods": [5, 10, 20, 60]}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        ps = self.params["periods"]
        emas = [EMA(df["close"], p) for p in ps]
        vals = [e.dropna().iloc[-1] for e in emas if not e.dropna().empty]
        if len(vals) < len(ps):
            return None
        close = float(df["close"].iloc[-1])
        if all(vals[i] > vals[i + 1] for i in range(len(vals) - 1)):
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=0.65,
                          price=close, reason="EMA 多头排列", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=float(vals[-1]))
        if all(vals[i] < vals[i + 1] for i in range(len(vals) - 1)):
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=0.65,
                          price=close, reason="EMA 空头排列", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=float(vals[-1]))
        return None


@register
class TrendChandelierExit(BaseStrategy):
    name = "trend_chandelier_exit"
    description = "吊灯止损跟踪(ATR 高点回撤)"
    timeframes = ["1d", "4h"]
    params = {"period": 22, "mult": 3.0}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        atr = ATR(df, self.params["period"]).dropna()
        if atr.empty:
            return None
        n = self.params["period"]
        highest = df["high"].rolling(n).max().iloc[-1]
        lowest = df["low"].rolling(n).min().iloc[-1]
        atr_v = float(atr.iloc[-1])
        long_stop = highest - self.params["mult"] * atr_v
        short_stop = lowest + self.params["mult"] * atr_v
        close = float(df["close"].iloc[-1])
        prev_close = float(df["close"].iloc[-2])
        if prev_close < long_stop and close > long_stop:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=0.6,
                          price=close, reason="吊灯多头触发", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=float(long_stop))
        if prev_close > short_stop and close < short_stop:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=0.6,
                          price=close, reason="吊灯空头触发", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=float(short_stop))
        return None


@register
class TrendMultiTimeframe(BaseStrategy):
    name = "trend_multi_timeframe"
    description = "多周期趋势共振(短中长 EMA 一致)"
    timeframes = ["1d"]
    params = {"short": 10, "mid": 30, "long": 60}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        p = self.params
        e_s = EMA(df["close"], p["short"]).dropna()
        e_m = EMA(df["close"], p["mid"]).dropna()
        e_l = EMA(df["close"], p["long"]).dropna()
        if e_s.empty or e_m.empty or e_l.empty:
            return None
        s, m, l = float(e_s.iloc[-1]), float(e_m.iloc[-1]), float(e_l.iloc[-1])
        close = float(df["close"].iloc[-1])
        if s > m > l and close > s:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=0.75,
                          price=close, reason="多周期共振多头", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=m)
        if s < m < l and close < s:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=0.75,
                          price=close, reason="多周期共振空头", strategy_name=self.name,
                          timeframe=self.timeframes[0], stop_loss=m)
        return None
