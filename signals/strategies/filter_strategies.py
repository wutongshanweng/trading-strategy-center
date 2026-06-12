import pandas as pd
import numpy as np
from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register
from signals.indicators import SMA, ATR, ADX


@register
class FilterVolatility(BaseStrategy):
    name = "filter_volatility"
    description = "ATR-based volatility classification"
    timeframes = ["1d", "4h"]
    params = {"atr_period": 14, "high_threshold": 0.03, "low_threshold": 0.01}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        atr = ATR(df, self.params["atr_period"])
        atr_pct = (atr / df["close"]).dropna()
        if atr_pct.empty:
            return None
        val, cv = atr_pct.iloc[-1], df["close"].iloc[-1]
        if pd.isna(val):
            return None
        if val > self.params["high_threshold"]:
            reason, conf = "high_vol", min(val / 0.05, 1.0)
        elif val < self.params["low_threshold"]:
            reason, conf = "low_vol", 1.0
        else:
            reason, conf = "normal_vol", 0.5
        return Signal(symbol=symbol, direction=Direction.HOLD, confidence=conf,
                      price=float(cv), reason=reason,
                      strategy_name=self.name, timeframe=self.timeframes[0],
                      extra={"atr_pct": float(val)})


@register
class FilterTrendStrength(BaseStrategy):
    name = "filter_trend_strength"
    description = "ADX + SMA slope trend classification"
    timeframes = ["1d", "4h"]
    params = {"adx_period": 14, "sma_period": 20, "slope_period": 5, "slope_pct": 0.5}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        adx, pdi, ndi = ADX(df, self.params["adx_period"])
        sma = SMA(df["close"], self.params["sma_period"])
        slope = sma.diff(self.params["slope_period"]) / sma * 100
        adx_s, slope_s = adx.dropna(), slope.dropna()
        if adx_s.empty or slope_s.empty:
            return None
        adx_v, slope_v, cv = adx_s.iloc[-1], slope_s.iloc[-1], df["close"].iloc[-1]
        if pd.isna(adx_v) or pd.isna(slope_v):
            return None
        conf = min(adx_v / 100, 1.0)
        thresh = self.params["slope_pct"]
        if adx_v > 25 and slope_v > thresh:
            reason = "strong_uptrend"
        elif adx_v > 25 and slope_v < -thresh:
            reason = "strong_downtrend"
        elif adx_v > 25:
            reason = "trending_flat"
        elif slope_v > thresh:
            reason = "weak_uptrend"
        elif slope_v < -thresh:
            reason = "weak_downtrend"
        else:
            reason = "ranging"
        return Signal(symbol=symbol, direction=Direction.HOLD, confidence=conf,
                      price=float(cv), reason=reason,
                      strategy_name=self.name, timeframe=self.timeframes[0],
                      extra={"adx": float(adx_v), "slope_pct": float(slope_v)})


@register
class FilterRegime(BaseStrategy):
    name = "filter_regime"
    description = "Market regime classification (bull/bear/range/volatile)"
    timeframes = ["1d"]
    params = {"sma_long": 200, "atr_period": 14, "sma_vol": 20,
              "sma_slope_period": 20, "trend_threshold": 0.1,
              "vol_high": 0.025, "vol_low": 0.01, "vol_ratio_threshold": 1.3}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if len(df) < self.params["sma_long"]:
            return None
        sma200 = SMA(df["close"], self.params["sma_long"])
        sma_slope = sma200.diff(self.params["sma_slope_period"]) / sma200 * 100
        atr = ATR(df, self.params["atr_period"])
        atr_ratio = (atr / df["close"]).dropna()
        vol_sma = SMA(df["volume"], self.params["sma_vol"])
        vol_ratio = (df["volume"] / vol_sma.replace(0, np.nan)).dropna()
        slope_v = sma_slope.iloc[-1] if not pd.isna(sma_slope.iloc[-1]) else 0.0
        atr_v = atr_ratio.iloc[-1] if not atr_ratio.empty else 0.0
        vol_r = vol_ratio.iloc[-1] if not vol_ratio.empty else 1.0
        cv = float(df["close"].iloc[-1])
        if any(pd.isna(x) for x in [slope_v, atr_v, vol_r]):
            return None
        is_bull = slope_v > self.params["trend_threshold"]
        is_bear = slope_v < -self.params["trend_threshold"]
        is_high_vol = atr_v > self.params["vol_high"]
        is_low_vol = atr_v < self.params["vol_low"]
        heavy_vol = vol_r > self.params["vol_ratio_threshold"]
        if is_bull and not is_high_vol:
            regime, conf = "bull", min(abs(slope_v) / 2, 1.0)
        elif is_bear and not is_high_vol:
            regime, conf = "bear", min(abs(slope_v) / 2, 1.0)
        elif is_high_vol and heavy_vol:
            regime, conf = "volatile", min(atr_v / 0.05, 1.0)
        else:
            regime, conf = "range", 0.5
        return Signal(symbol=symbol, direction=Direction.HOLD, confidence=conf,
                      price=cv, reason=regime,
                      strategy_name=self.name, timeframe=self.timeframes[0],
                      extra={"sma200_slope_pct": float(slope_v), "atr_pct": float(atr_v), "vol_ratio": float(vol_r)})
