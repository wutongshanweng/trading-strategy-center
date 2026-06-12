from typing import Dict
import numpy as np
import pandas as pd


class FundamentalAnalyzer:
    def __init__(self):
        self.basis_value = self.carry_cost = self.fair_value_price = None

    def basis(self, spot_price: float, futures_price: float) -> float:
        self.basis_value = float(spot_price - futures_price) if None not in (spot_price, futures_price) else np.nan
        return self.basis_value

    def cost_of_carry(self, interest_rate: float, storage_cost: float, time_to_expiry: float) -> float:
        if None in (interest_rate, storage_cost, time_to_expiry) or time_to_expiry <= 0:
            return np.nan
        self.carry_cost = float(interest_rate + storage_cost)
        return self.carry_cost

    def fair_value(self, spot: float, interest_rate: float, storage_cost: float, time_to_expiry: float) -> float:
        if spot is None or spot <= 0 or time_to_expiry is None or time_to_expiry <= 0:
            return np.nan
        self.fair_value_price = float(spot * np.exp((interest_rate + storage_cost) * time_to_expiry))
        return self.fair_value_price

    def analyze_futures(self, df_spot: pd.DataFrame, df_futures: pd.DataFrame) -> Dict:
        if df_spot is None or df_futures is None:
            return {}
        common = df_spot.index.intersection(df_futures.index)
        if len(common) == 0:
            return {}
        s = df_spot.loc[common, "close"].values.astype(float)
        f = df_futures.loc[common, "close"].values.astype(float)
        basis_s = s - f
        return {"mean_basis": float(np.mean(basis_s)), "current_basis": float(basis_s[-1]) if len(basis_s) > 0 else np.nan,
                "mean_basis_pct": float(np.mean(np.divide(basis_s, f, out=np.zeros_like(basis_s), where=f != 0))),
                "spot_future_corr": float(pd.Series(s).corr(pd.Series(f)))}
