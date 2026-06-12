import pandas as pd
from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register
from signals.indicators import CCI, OBV, SMA


@register
class MomentumRoc(BaseStrategy):
    name = "momentum_roc"
    description = "Rate of Change momentum"
    timeframes = ["1d", "4h", "1h"]
    params = {"period": 12}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        close = df["close"]
        roc = ((close / close.shift(self.params["period"])) - 1) * 100
        roc = roc.dropna()
        if len(roc) < 2:
            return None
        curr, prev, cv = roc.iloc[-1], roc.iloc[-2], close.iloc[-1]
        if pd.isna(curr) or pd.isna(prev):
            return None
        conf = min(abs(curr) / 100, 1.0)
        if curr > 0 and curr > prev:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=conf,
                          price=float(cv), reason=f"ROC positive accelerating: {curr:.2f}%",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        elif curr < 0 and curr < prev:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=conf,
                          price=float(cv), reason=f"ROC negative declining: {curr:.2f}%",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        return None


@register
class MomentumCci(BaseStrategy):
    name = "momentum_cci"
    description = "CCI momentum with divergence"
    timeframes = ["1d", "4h", "1h"]
    params = {"period": 20, "overbought": 100, "oversold": -100, "div_lookback": 10}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        cci = CCI(df, self.params["period"]).dropna()
        if len(cci) < self.params["div_lookback"]:
            return None
        cci_v, cv = cci.iloc[-1], df["close"].iloc[-1]
        if pd.isna(cci_v):
            return None
        lookback = self.params["div_lookback"]
        recent_cci = cci.iloc[-lookback:]
        recent_close = df["close"].iloc[-lookback:]
        mid = lookback // 2
        first_cci = recent_cci.iloc[:mid]
        second_cci = recent_cci.iloc[mid:]
        first_close = recent_close.iloc[:mid]
        second_close = recent_close.iloc[mid:]
        bullish_div = (second_close.min() < first_close.min() and second_cci.min() > first_cci.min())
        bearish_div = (second_close.max() > first_close.max() and second_cci.max() < first_cci.max())
        if cci_v > self.params["overbought"]:
            if bearish_div:
                return Signal(symbol=symbol, direction=Direction.SELL, confidence=min((cci_v - self.params["overbought"]) / 200 + 0.3, 1.0),
                              price=float(cv), reason=f"CCI bearish divergence: {cci_v:.1f}",
                              strategy_name=self.name, timeframe=self.timeframes[0])
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=min((cci_v - self.params["overbought"]) / 200, 0.8),
                          price=float(cv), reason=f"CCI bullish momentum: {cci_v:.1f}",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        elif cci_v < self.params["oversold"]:
            if bullish_div:
                return Signal(symbol=symbol, direction=Direction.BUY, confidence=min((self.params["oversold"] - cci_v) / 200 + 0.3, 1.0),
                              price=float(cv), reason=f"CCI bullish divergence: {cci_v:.1f}",
                              strategy_name=self.name, timeframe=self.timeframes[0])
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=min((self.params["oversold"] - cci_v) / 200, 0.8),
                          price=float(cv), reason=f"CCI bearish momentum: {cci_v:.1f}",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        return None


@register
class MomentualObv(BaseStrategy):
    name = "momentum_obv"
    description = "OBV divergence detection"
    timeframes = ["1d", "4h"]
    params = {"lookback": 20}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if "volume" not in df.columns:
            return None
        obv = OBV(df)
        close = df["close"]
        if len(obv) < self.params["lookback"] or len(close) < self.params["lookback"]:
            return None
        n, mid = self.params["lookback"], self.params["lookback"] // 2
        first_obv = obv.iloc[-n:-mid]
        second_obv = obv.iloc[-mid:]
        first_close = close.iloc[-n:-mid]
        second_close = close.iloc[-mid:]
        cv = close.iloc[-1]
        bearish_div = (second_close.max() > first_close.max() and second_obv.max() < first_obv.max())
        bullish_div = (second_close.min() < first_close.min() and second_obv.min() > first_obv.min())
        if bearish_div:
            diff_pct = (second_obv.max() - first_obv.max()) / abs(first_obv.max()) * 100 if first_obv.max() != 0 else 0
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=min(abs(diff_pct) / 5, 1.0) if first_obv.max() != 0 else 0.6,
                          price=float(cv), reason="OBV bearish divergence",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        if bullish_div:
            diff_pct = (second_obv.min() - first_obv.min()) / abs(first_obv.min()) * 100 if first_obv.min() != 0 else 0
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=min(abs(diff_pct) / 5, 1.0) if first_obv.min() != 0 else 0.6,
                          price=float(cv), reason="OBV bullish divergence",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        return None
