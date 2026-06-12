from typing import Dict
import numpy as np
import pandas as pd


def rolling_correlation(df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    if df is None or df.empty or df.shape[1] < 2:
        return pd.DataFrame()
    return pd.DataFrame({f"{df.columns[i]}_{df.columns[j]}": df.iloc[:, i].rolling(window).corr(df.iloc[:, j])
                         for i in range(len(df.columns)) for j in range(i + 1, len(df.columns))})


class CrossMarketAnalyzer:
    def __init__(self, window: int = 60):
        self.window = window
        self.results: Dict = {}

    def analyze(self, df_dict: Dict[str, pd.DataFrame]):
        self.results = {}
        for name, df in df_dict.items():
            if df is None or df.empty:
                continue
            corr = rolling_correlation(df, self.window)
            self.results[name] = {"rolling_corr": corr, "regime_shifts": self.detect_regime_shift(corr)}
        return self.results

    def detect_regime_shift(self, corr_series):
        if corr_series is None or len(corr_series) < 20:
            return {"num_shifts": 0}
        if isinstance(corr_series, pd.DataFrame):
            corr_series = corr_series.iloc[:, 0]
        shifts, min_w = pd.Series(False, index=corr_series.index), max(5, self.window // 4)
        for i in range(min_w, len(corr_series) - min_w):
            if abs(corr_series.iloc[i:i + min_w].mean() - corr_series.iloc[i - min_w:i].mean()) > 0.3:
                shifts.iloc[i] = True
        return {"num_shifts": int(shifts.sum())}
