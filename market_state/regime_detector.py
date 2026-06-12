from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


class MarketRegime(Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    CRASH = "CRASH"
    RECOVERY = "RECOVERY"


@dataclass
class RegimeInfo:
    regime: MarketRegime
    confidence: float
    trend_strength: float
    volatility: str
    slope_20: float
    slope_200: float


class MarketRegimeDetector:
    def __init__(self, lookback_short: int = 20, lookback_long: int = 200):
        self.lookback_short = lookback_short
        self.lookback_long = lookback_long

    def _compute_slope(self, series: pd.Series) -> float:
        series = series.dropna()
        n = len(series)
        if n < 2:
            return 0.0
        X = np.arange(n).reshape(-1, 1)
        y = series.values.reshape(-1, 1)
        model = LinearRegression().fit(X, y)
        mean_price = series.mean()
        return (model.coef_[0, 0] / mean_price) * 100.0 if mean_price != 0 else 0.0

    def _compute_adx_strength(self, df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        tr = df["high"] - df["low"]
        atr = tr.rolling(window=self.lookback_short).mean()
        if pd.isna(atr.iloc[-1]):
            return 0.0
        mean_close = df["close"].mean()
        return min(1.0, atr.iloc[-1] / mean_close * 100.0) if mean_close != 0 else 0.0

    def _classify_volatility(self, df: pd.DataFrame) -> str:
        if len(df) < 20:
            return "normal"
        vol_series = df["close"].pct_change().rolling(20).std().dropna() * 100.0
        if len(vol_series) < 2:
            return "normal"
        current_vol = vol_series.iloc[-1]
        if pd.isna(current_vol):
            return "normal"
        p25, p75, p95 = vol_series.quantile(0.25), vol_series.quantile(0.75), vol_series.quantile(0.95)
        if current_vol > p95:
            return "extreme"
        elif current_vol > p75:
            return "high"
        elif current_vol < p25:
            return "low"
        return "normal"

    def detect(self, df: pd.DataFrame) -> RegimeInfo:
        if df.empty or "close" not in df:
            return RegimeInfo(MarketRegime.RANGING, 0.0, 0.0, "normal", 0.0, 0.0)
        df = df.dropna(subset=["close"])
        if len(df) < self.lookback_short:
            return RegimeInfo(MarketRegime.RANGING, 0.0, 0.0, "normal", 0.0, 0.0)

        short_close = df["close"].tail(self.lookback_short)
        slope_20 = self._compute_slope(short_close)
        n_long = min(self.lookback_long, len(df))
        slope_200 = self._compute_slope(df["close"].tail(n_long)) if n_long >= 20 else 0.0
        trend_strength = self._compute_adx_strength(df)
        volatility = self._classify_volatility(df)
        adx_high = trend_strength > 0.25

        if slope_200 > 1.0 and adx_high:
            regime, indicators = MarketRegime.BULL, [True, True]
        elif slope_200 < -1.0 and adx_high:
            regime, indicators = MarketRegime.BEAR, [True, True]
        elif volatility == "extreme":
            regime, indicators = MarketRegime.VOLATILE, [True]
        elif slope_200 > 0 and slope_20 < 0:
            regime, indicators = MarketRegime.RECOVERY, [True, True]
        elif slope_200 < 0 and slope_20 > 0:
            regime, indicators = MarketRegime.CRASH, [True, True]
        else:
            regime, indicators = MarketRegime.RANGING, [False]

        votes = list(indicators)
        if volatility == "extreme" and regime == MarketRegime.BULL:
            votes.append(False)
        if adx_high and regime == MarketRegime.RANGING:
            votes.append(True)
        if not adx_high and regime in (MarketRegime.BULL, MarketRegime.BEAR):
            votes.append(False)

        confidence = sum(votes) / len(votes) if votes else 0.0
        return RegimeInfo(regime=regime, confidence=round(confidence, 4),
                          trend_strength=round(trend_strength, 4), volatility=volatility,
                          slope_20=round(slope_20, 4), slope_200=round(slope_200, 4))
