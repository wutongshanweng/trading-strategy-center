import pandas as pd
import numpy as np
from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register
from signals.indicators import DONCHIAN, BB, SMA


@register
class BreakoutDonchian(BaseStrategy):
    name = "breakout_donchian"
    description = "Donchian channel breakout"
    timeframes = ["1d", "4h", "1h"]
    params = {"period": 20}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        upper, mid, lower = DONCHIAN(df, self.params["period"])
        upper_s, lower_s = upper.dropna(), lower.dropna()
        if upper_s.empty or lower_s.empty:
            return None
        uv, lv, cv = upper_s.iloc[-1], lower_s.iloc[-1], df["close"].iloc[-1]
        mid_v = mid.dropna().iloc[-1] if not mid.dropna().empty else None
        if any(pd.isna(x) for x in [uv, lv]) or mid_v is None:
            return None
        if cv > uv:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=min((cv - uv) / uv * 100 / 3, 1.0),
                          price=float(cv), reason=f"Donchian upside breakout",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(mid_v), take_profit=float(uv * 1.02))
        elif cv < lv:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=min((lv - cv) / lv * 100 / 3, 1.0),
                          price=float(cv), reason=f"Donchian downside breakout",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(mid_v), take_profit=float(uv * 0.98))
        return None


@register
class BreakoutVolatility(BaseStrategy):
    name = "breakout_volatility"
    description = "Bollinger Band squeeze breakout"
    timeframes = ["1d", "4h"]
    params = {"bb_period": 20, "bb_std": 2.0, "lookback": 100, "squeeze_pct": 0.2}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        upper, mid, lower = BB(df["close"], self.params["bb_period"], self.params["bb_std"])
        bandwidth = ((upper - lower) / mid.replace(0, np.nan)).dropna()
        if len(bandwidth) < self.params["lookback"] + 1:
            return None
        hist_bw = bandwidth.iloc[-self.params["lookback"]:-1]
        curr_bw = bandwidth.iloc[-1]
        if pd.isna(curr_bw) or hist_bw.empty:
            return None
        hist_median = hist_bw.median()
        if pd.isna(hist_median) or hist_median == 0:
            return None
        if curr_bw / hist_median < self.params["squeeze_pct"]:
            cv, uv, lv, mv = df["close"].iloc[-1], upper.iloc[-1], lower.iloc[-1], mid.iloc[-1]
            if cv > uv:
                return Signal(symbol=symbol, direction=Direction.BUY, confidence=min((cv - uv) / (uv - mv + 1e-10), 1.0),
                              price=float(cv), reason="Vol squeeze upside breakout",
                              strategy_name=self.name, timeframe=self.timeframes[0])
            elif cv < lv:
                return Signal(symbol=symbol, direction=Direction.SELL, confidence=min((lv - cv) / (mv - lv + 1e-10), 1.0),
                              price=float(cv), reason="Vol squeeze downside breakout",
                              strategy_name=self.name, timeframe=self.timeframes[0])
        return None


@register
class BreakoutVolume(BaseStrategy):
    name = "breakout_volume"
    description = "Price breakout with volume confirmation"
    timeframes = ["1d", "4h", "1h"]
    params = {"lookback": 20, "vol_mult": 1.5}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if "volume" not in df.columns:
            return None
        vol_sma_v = SMA(df["volume"], self.params["lookback"]).dropna()
        if vol_sma_v.empty:
            return None
        curr_vol, avg_vol, cv = df["volume"].iloc[-1], vol_sma_v.iloc[-1], df["close"].iloc[-1]
        if pd.isna(curr_vol) or pd.isna(avg_vol) or avg_vol == 0:
            return None
        vol_ratio = curr_vol / avg_vol
        if vol_ratio < self.params["vol_mult"]:
            return None
        recent_high = df["high"].iloc[-self.params["lookback"]:-1].max()
        recent_low = df["low"].iloc[-self.params["lookback"]:-1].min()
        if pd.isna(recent_high) or pd.isna(recent_low):
            return None
        conf = min((vol_ratio - 1) / 2, 1.0)
        if cv > recent_high:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=conf,
                          price=float(cv), reason=f"Volume breakout: {vol_ratio:.1f}x avg vol",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        elif cv < recent_low:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=conf,
                          price=float(cv), reason=f"Volume breakdown: {vol_ratio:.1f}x avg vol",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        return None
