from typing import List, Dict
import numpy as np
import pandas as pd


class DivergenceDetector:
    def __init__(self, window: int = 14):
        self.window = window

    def detect(self, df: pd.DataFrame, method: str = "rsi") -> List[Dict]:
        if df is None or len(df) < 30:
            return []
        m = {"rsi": self._detect_rsi, "macd": self._detect_macd, "volume": self._detect_volume}
        return m.get(method, lambda x: [])(df)

    def _rsi(self, prices):
        delta = prices.diff()
        gain = delta.clip(lower=0).rolling(self.window, min_periods=1).mean()
        loss = (-delta.clip(upper=0)).rolling(self.window, min_periods=1).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))

    def _find_peaks(self, series, order=5):
        highs, lows = pd.Series(False, index=series.index), pd.Series(False, index=series.index)
        for i in range(order, len(series) - order):
            w = series.iloc[i - order:i + order + 1]
            highs.iloc[i] = (series.iloc[i] == w.max())
            lows.iloc[i] = (series.iloc[i] == w.min())
        return highs, lows

    def _detect_rsi(self, df):
        prices = df["close"]
        rsi = self._rsi(prices)
        ph, pl = self._find_peaks(prices)
        rh, rl = self._find_peaks(rsi)
        divergences = []
        for peaks, price_cond, rsi_cond, div_type in [
            (ph[ph].index, lambda p, c: prices[c] > prices[p], lambda p, c: rsi[c] < rsi[p], "bearish_rsi"),
            (pl[pl].index, lambda p, c: prices[c] < prices[p], lambda p, c: rsi[c] > rsi[p], "bullish_rsi"),
        ]:
            for i in range(1, len(peaks)):
                p, c = peaks[i - 1], peaks[i]
                if price_cond(p, c) and rsi_cond(p, c):
                    divergences.append({"type": div_type, "severity": float(abs(rsi[c] - rsi[p]) / (abs(rsi[p]) + 1e-10)),
                                        "start_idx": df.index.get_loc(p), "end_idx": df.index.get_loc(c)})
        return divergences

    def _detect_macd(self, df):
        prices = df["close"]
        ema12, ema26 = prices.ewm(span=12).mean(), prices.ewm(span=26).mean()
        hist = (ema12 - ema26) - (ema12 - ema26).ewm(span=9).mean()
        return self._generic_divergence(prices, hist, "macd")

    def _detect_volume(self, df):
        if "volume" not in df.columns:
            return []
        return self._generic_divergence(df["close"], df["volume"], "volume")

    def _generic_divergence(self, price, indicator, name):
        ph, pl = self._find_peaks(price)
        ih, il = self._find_peaks(indicator)
        divergences = []
        for peaks, price_cond, ind_cond, div_type in [
            (ph[ph].index, lambda p, c: price[c] > price[p], lambda p, c: indicator[c] < indicator[p], f"bearish_{name}"),
            (pl[pl].index, lambda p, c: price[c] < price[p], lambda p, c: indicator[c] > indicator[p], f"bullish_{name}"),
        ]:
            for i in range(1, len(peaks)):
                p, c = peaks[i - 1], peaks[i]
                if price_cond(p, c) and ind_cond(p, c):
                    divergences.append({"type": div_type, "severity": float(abs(indicator[c] - indicator[p]) / (abs(indicator[p]) + 1e-10))})
        return divergences
