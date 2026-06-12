import pandas as pd
from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register
from signals.indicators import SMA, ATR, ADX, RSI, BB


@register
class FilterMarketNoise(BaseStrategy):
    name = "layer_noise_filter"
    description = "Filters out low quality market conditions"
    timeframes = ["1d", "4h", "1h"]
    params = {"min_volatility": 0.005, "min_volume_ratio": 0.5}

    def compute(self, df):
        if "volume" not in df.columns or "close" not in df.columns:
            return Signal(strategy_name=self.name, direction=Direction.HOLD, confidence=0.0, price=df["close"].iloc[-1], reason="missing_columns")
        if len(df) < 20:
            return Signal(strategy_name=self.name, direction=Direction.HOLD, confidence=0.0, price=df["close"].iloc[-1])
        atr = ATR(df, 14)
        vol_ratio = atr / df["close"]
        vol_sma = SMA(df["volume"], 20)
        recent_vol_ratio = vol_ratio.iloc[-1]
        recent_volume = df["volume"].iloc[-1]
        recent_vol_sma = vol_sma.iloc[-1]
        if pd.isna(recent_vol_ratio) or pd.isna(recent_volume) or pd.isna(recent_vol_sma) or recent_vol_sma <= 0:
            return Signal(strategy_name=self.name, direction=Direction.HOLD, confidence=0.0, price=df["close"].iloc[-1], reason="insufficient_data")
        if recent_vol_ratio < self.params["min_volatility"]:
            return Signal(strategy_name=self.name, direction=Direction.HOLD, confidence=0.0, price=df["close"].iloc[-1], reason="low_vol_no_trade")
        if recent_volume < recent_vol_sma * self.params["min_volume_ratio"]:
            return Signal(strategy_name=self.name, direction=Direction.HOLD, confidence=0.0, price=df["close"].iloc[-1], reason="low_volume_no_trade")
        return Signal(strategy_name=self.name, direction=Direction.BUY, confidence=0.3, price=df["close"].iloc[-1], reason="pass_filter")


@register
class FilterTrendContext(BaseStrategy):
    name = "layer_trend_context"
    description = "Provides trend context for signals"
    timeframes = ["1d", "4h", "1h"]
    params = {"adx_strong": 25, "adx_weak": 15, "slope_threshold": 0.005}

    def compute(self, df):
        adx = ADX(df, 14)
        sma20 = SMA(df["close"], 20)
        if len(df) < 21:
            return Signal(strategy_name=self.name, direction=Direction.HOLD, confidence=0.0, price=df["close"].iloc[-1])
        recent_adx = adx.iloc[-1]
        slope = (sma20.iloc[-1] - sma20.iloc[-2]) / sma20.iloc[-2]
        price = df["close"].iloc[-1]
        if pd.isna(recent_adx) or pd.isna(slope):
            return Signal(strategy_name=self.name, direction=Direction.HOLD, confidence=0.0, price=price, reason="insufficient_data")
        if recent_adx > self.params["adx_strong"]:
            if slope > self.params["slope_threshold"]:
                return Signal(strategy_name=self.name, direction=Direction.BUY, confidence=0.7, price=price, reason="strong_trend_bull")
            elif slope < -self.params["slope_threshold"]:
                return Signal(strategy_name=self.name, direction=Direction.SELL, confidence=0.7, price=price, reason="strong_trend_bear")
            return Signal(strategy_name=self.name, direction=Direction.HOLD, confidence=0.0, price=price, reason="strong_trend_no_direction")
        if recent_adx > self.params["adx_weak"]:
            if slope > 0:
                return Signal(strategy_name=self.name, direction=Direction.BUY, confidence=0.4, price=price, reason="mild_bull")
            return Signal(strategy_name=self.name, direction=Direction.SELL, confidence=0.4, price=price, reason="mild_bear")
        return Signal(strategy_name=self.name, direction=Direction.HOLD, confidence=0.0, price=price, reason="no_trend")


@register
class FilterRiskGating(BaseStrategy):
    name = "layer_risk_gate"
    description = "Risk based signal gating using Bollinger Bands"
    timeframes = ["1d", "4h", "1h"]
    params = {"bb_width_threshold": 0.1, "bb_threshold": 0.02, "rsi_overbought": 70, "rsi_oversold": 30}

    def compute(self, df):
        bb = BB(df, 20, 2)
        rsi_vals = RSI(df["close"], 14)
        if len(df) < 20:
            return Signal(strategy_name=self.name, direction=Direction.HOLD, confidence=0.0, price=df["close"].iloc[-1])
        close = df["close"].iloc[-1]
        bb_upper = bb["upper"].iloc[-1]
        bb_mid = bb["mid"].iloc[-1]
        bb_lower = bb["lower"].iloc[-1]
        rsi_val = rsi_vals.iloc[-1]
        if pd.isna(bb_upper) or pd.isna(bb_lower) or pd.isna(rsi_val):
            return Signal(strategy_name=self.name, direction=Direction.HOLD, confidence=0.0, price=close, reason="insufficient_data")
        bandwidth = (bb_upper - bb_lower) / bb_mid
        if bandwidth > self.params["bb_width_threshold"]:
            return Signal(strategy_name=self.name, direction=Direction.HOLD, confidence=0.0, price=close, reason="high_risk_no_trade")
        range_to_lower = (close - bb_lower) / (bb_mid - bb_lower) if bb_mid != bb_lower else 1.0
        range_to_upper = (bb_upper - close) / (bb_upper - bb_mid) if bb_upper != bb_mid else 1.0
        if range_to_lower < self.params["bb_threshold"] / 0.5 and rsi_val < self.params["rsi_oversold"]:
            return Signal(strategy_name=self.name, direction=Direction.BUY, confidence=0.7, price=close, reason="bb_lower_reversal")
        if range_to_upper < self.params["bb_threshold"] / 0.5 and rsi_val > self.params["rsi_overbought"]:
            return Signal(strategy_name=self.name, direction=Direction.SELL, confidence=0.7, price=close, reason="bb_upper_reversal")
        return Signal(strategy_name=self.name, direction=Direction.HOLD, confidence=0.0, price=close, reason="no_risk_setup")
