from typing import Dict
import numpy as np
import pandas as pd


class OrderFlowAnalyzer:
    def __init__(self):
        self.result = None

    def analyze(self, df: pd.DataFrame) -> Dict:
        if df is None or len(df) < 2 or "close" not in df.columns or "volume" not in df.columns:
            return {}
        df, d = df.copy(), df["close"].diff()
        df["tick"] = np.where(d > 0, 1, np.where(d < 0, -1, np.nan))
        df["tick"] = df["tick"].fillna(method="ffill").fillna(0)
        df["buy_volume"] = df["volume"] * (df["tick"] == 1).astype(int)
        df["sell_volume"] = df["volume"] * (df["tick"] == -1).astype(int)
        if (df["tick"] == 0).any():
            df.loc[df["tick"] == 0, ["buy_volume", "sell_volume"]] = df.loc[df["tick"] == 0, "volume"] * 0.5
        self.result = df
        return {"buy_volume": float(df["buy_volume"].sum()), "sell_volume": float(df["sell_volume"].sum()),
                "imbalance": float(df["buy_volume"].sum() - df["sell_volume"].sum())}

    def imbalance(self) -> float:
        return float(self.result["imbalance"].sum()) if self.result is not None else 0.0
