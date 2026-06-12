import pandas as pd
import numpy as np
from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register
from signals.indicators import SMA, MACD, ADX


@register
class TrendMaCross(BaseStrategy):
    name = "trend_ma_cross"
    description = "Golden cross / death cross (MA5 x MA20)"
    timeframes = ["1d", "4h", "1h"]
    params = {"fast": 5, "slow": 20}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        fast = SMA(df["close"], self.params["fast"])
        slow = SMA(df["close"], self.params["slow"])
        diff = (fast - slow).dropna()
        if len(diff) < 2:
            return None
        curr, prev = diff.iloc[-1], diff.iloc[-2]
        close = df["close"].iloc[-1]
        if pd.isna(curr) or pd.isna(prev):
            return None
        if prev < 0 and curr > 0:
            slope = abs(curr - prev) / max(abs(prev), 1e-10)
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=min(slope, 1.0),
                          price=float(close), reason=f"Golden cross MA{self.params['fast']}×MA{self.params['slow']}",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(close * 0.97), take_profit=float(close * 1.05))
        elif prev > 0 and curr < 0:
            slope = abs(curr - prev) / max(abs(prev), 1e-10)
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=min(slope, 1.0),
                          price=float(close), reason=f"Death cross MA{self.params['fast']}×MA{self.params['slow']}",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(close * 1.03), take_profit=float(close * 0.95))
        return None


@register
class TrendMacd(BaseStrategy):
    name = "trend_macd"
    description = "MACD line crosses signal line"
    timeframes = ["1d", "4h", "1h"]
    params = {"fast": 12, "slow": 26, "signal": 9}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        macd_line, signal_line, histogram = MACD(df["close"], self.params["fast"], self.params["slow"], self.params["signal"])
        diff = (macd_line - signal_line).dropna()
        if len(diff) < 2:
            return None
        curr, prev = diff.iloc[-1], diff.iloc[-2]
        close = df["close"].iloc[-1]
        if pd.isna(curr) or pd.isna(prev):
            return None
        if prev < 0 and curr > 0:
            conf = min(abs(histogram.iloc[-1]) / 10 + 0.3, 1.0) if not pd.isna(histogram.iloc[-1]) else 0.6
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=conf,
                          price=float(close), reason="MACD bullish cross",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(close * 0.97), take_profit=float(close * 1.05))
        elif prev > 0 and curr < 0:
            conf = min(abs(histogram.iloc[-1]) / 10 + 0.3, 1.0) if not pd.isna(histogram.iloc[-1]) else 0.6
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=conf,
                          price=float(close), reason="MACD bearish cross",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(close * 1.03), take_profit=float(close * 0.95))
        return None


@register
class TrendAdx(BaseStrategy):
    name = "trend_adx"
    description = "ADX trend strength with direction"
    timeframes = ["1d", "4h", "1h"]
    params = {"period": 14, "threshold": 25}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        adx, pdi, ndi = ADX(df, self.params["period"])
        adx_s, pdi_s, ndi_s = adx.dropna(), pdi.dropna(), ndi.dropna()
        if adx_s.empty or pdi_s.empty or ndi_s.empty:
            return None
        adx_v, pdi_v, ndi_v = adx_s.iloc[-1], pdi_s.iloc[-1], ndi_s.iloc[-1]
        close = df["close"].iloc[-1]
        if any(pd.isna(x) for x in [adx_v, pdi_v, ndi_v]):
            return None
        if adx_v < self.params["threshold"]:
            return None
        conf = min(adx_v / 100, 1.0)
        if pdi_v > ndi_v:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=conf,
                          price=float(close), reason=f"ADX={adx_v:.1f} +DI>{ndi_v:.1f} uptrend",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        else:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=conf,
                          price=float(close), reason=f"ADX={adx_v:.1f} -DI>{pdi_v:.1f} downtrend",
                          strategy_name=self.name, timeframe=self.timeframes[0])


@register
class TrendIchimoku(BaseStrategy):
    name = "trend_ichimoku"
    description = "Simplified Ichimoku Cloud"
    timeframes = ["1d", "4h"]
    params = {"tenkan": 9, "kijun": 26, "senkou_b": 52}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        high, low, close = df["high"], df["low"], df["close"]
        tenkan = (high.rolling(self.params["tenkan"]).max() + low.rolling(self.params["tenkan"]).min()) / 2
        kijun = (high.rolling(self.params["kijun"]).max() + low.rolling(self.params["kijun"]).min()) / 2
        senkou_a = (tenkan + kijun) / 2
        senkou_b = (high.rolling(self.params["senkou_b"]).max() + low.rolling(self.params["senkou_b"]).min()) / 2
        frames = [x.dropna() for x in [tenkan, kijun, senkou_a, senkou_b]]
        if any(f.empty for f in frames):
            return None
        t, k, sa, sb = frames[0].iloc[-1], frames[1].iloc[-1], frames[2].iloc[-1], frames[3].iloc[-1]
        cv = float(close.iloc[-1])
        if any(pd.isna(x) for x in [t, k, sa, sb]):
            return None
        cloud_top, cloud_bot = max(sa, sb), min(sa, sb)
        if t > k and cv > cloud_top:
            conf = min((t - k) / max(k, 1e-10) * 5, 1.0)
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=conf,
                          price=cv, reason="Ichimoku bullish TK cross + above cloud",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(cloud_bot), take_profit=cv * 1.05)
        elif t < k and cv < cloud_bot:
            conf = min((k - t) / max(k, 1e-10) * 5, 1.0)
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=conf,
                          price=cv, reason="Ichimoku bearish TK cross + below cloud",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(cloud_top), take_profit=cv * 0.95)
        return None
