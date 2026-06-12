import pandas as pd
from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register
from signals.indicators import RSI, KDJ, BB


@register
class ReversalRsi(BaseStrategy):
    name = "reversal_rsi"
    description = "RSI oversold/overbought reversal"
    timeframes = ["1d", "4h", "1h"]
    params = {"period": 14, "oversold": 25, "overbought": 75}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        rsi = RSI(df["close"], self.params["period"]).dropna()
        if rsi.empty:
            return None
        rsi_v, close = rsi.iloc[-1], df["close"].iloc[-1]
        if pd.isna(rsi_v):
            return None
        if rsi_v < self.params["oversold"]:
            dist = (self.params["oversold"] - rsi_v) / self.params["oversold"]
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=min(dist, 1.0),
                          price=float(close), reason=f"RSI oversold: {rsi_v:.1f}",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(close * 0.96), take_profit=float(close * 1.06))
        elif rsi_v > self.params["overbought"]:
            dist = (rsi_v - self.params["overbought"]) / (100 - self.params["overbought"])
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=min(dist, 1.0),
                          price=float(close), reason=f"RSI overbought: {rsi_v:.1f}",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(close * 1.04), take_profit=float(close * 0.94))
        return None


@register
class ReversalKdj(BaseStrategy):
    name = "reversal_kdj"
    description = "KDJ stochastic reversal"
    timeframes = ["1d", "4h", "1h"]
    params = {"period": 9, "k_smooth": 3, "d_smooth": 3}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        k, d, j = KDJ(df, self.params["period"], self.params["k_smooth"], self.params["d_smooth"])
        k, d, j = k.dropna(), d.dropna(), j.dropna()
        if len(j) < 2 or k.empty or d.empty:
            return None
        j_v, j_p = j.iloc[-1], j.iloc[-2]
        k_v, k_p = k.iloc[-1], k.iloc[-2]
        d_v, d_p = d.iloc[-1], d.iloc[-2]
        close = df["close"].iloc[-1]
        if any(pd.isna(x) for x in [j_v, j_p, k_v, k_p, d_v, d_p]):
            return None
        kd_bull = k_p < d_p and k_v > d_v
        kd_bear = k_p > d_p and k_v < d_v
        if j_v < 0:
            conf = min(abs(j_v) / 100 + (0.3 if kd_bull else 0), 1.0)
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=conf,
                          price=float(close), reason=f"KDJ oversold J={j_v:.1f}",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        elif j_v > 100:
            conf = min((j_v - 100) / 100 + (0.3 if kd_bear else 0), 1.0)
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=conf,
                          price=float(close), reason=f"KDJ overbought J={j_v:.1f}",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        return None


@register
class ReversalBollinger(BaseStrategy):
    name = "reversal_bollinger"
    description = "Bollinger Band touch + RSI confirmation"
    timeframes = ["1d", "4h", "1h"]
    params = {"bb_period": 20, "bb_std": 2.0, "rsi_period": 14}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        upper, mid, lower = BB(df["close"], self.params["bb_period"], self.params["bb_std"])
        rsi = RSI(df["close"], self.params["rsi_period"])
        upper_s, lower_s, rsi_s = upper.dropna(), lower.dropna(), rsi.dropna()
        if upper_s.empty or lower_s.empty or rsi_s.empty:
            return None
        cv, uv, lv, rv = df["close"].iloc[-1], upper_s.iloc[-1], lower_s.iloc[-1], rsi_s.iloc[-1]
        mv = mid.dropna().iloc[-1] if not mid.dropna().empty else None
        if any(pd.isna(x) for x in [cv, uv, lv, rv]) or mv is None:
            return None
        if cv <= lv and rv < 30:
            conf = min((30 - rv) / 30 + 0.2, 1.0)
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=conf,
                          price=float(cv), reason=f"BB lower touch + RSI={rv:.1f}",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(lv * 0.98), take_profit=float(mv))
        elif cv >= uv and rv > 70:
            conf = min((rv - 70) / 30 + 0.2, 1.0)
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=conf,
                          price=float(cv), reason=f"BB upper touch + RSI={rv:.1f}",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(uv * 1.02), take_profit=float(mv))
        return None
