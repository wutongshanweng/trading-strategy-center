"""
截面特征 — 横截面排名的相对强弱 (多标的同时打分)。

对每个时点计算所有标的的相对排名。data 需含 'date' 列。

用法:
    pipe.register_module(CrossSectionalFeatureSet())
"""

from __future__ import annotations

from typing import Callable, List, Tuple

import pandas as pd


class CrossSectionalFeatureSet:
    """截面特征 (横截面排名类)。"""

    def get_features(self) -> List[Tuple[str, Callable, str]]:
        return [
            ("cs_rank_momentum_5d", self._cs_rank_mom_5d, "cross_sectional"),
            ("cs_rank_momentum_20d", self._cs_rank_mom_20d, "cross_sectional"),
            ("cs_rank_volume", self._cs_rank_volume, "cross_sectional"),
            ("cs_rank_volatility", self._cs_rank_vol, "cross_sectional"),
            ("cs_zscore_momentum_5d", self._cs_z_mom_5d, "cross_sectional"),
        ]

    def _cs_rank_mom_5d(self, data: pd.DataFrame) -> pd.Series:
        if "date" in data.columns:
            mom = data.groupby("date")["close"].transform(lambda x: x.pct_change(5))
            return mom.groupby(data["date"]).rank(pct=True)
        return pd.Series(index=data.index, dtype=float)

    def _cs_rank_mom_20d(self, data: pd.DataFrame) -> pd.Series:
        if "date" in data.columns:
            mom = data.groupby("date")["close"].transform(lambda x: x.pct_change(20))
            return mom.groupby(data["date"]).rank(pct=True)
        return pd.Series(index=data.index, dtype=float)

    def _cs_rank_volume(self, data: pd.DataFrame) -> pd.Series:
        if "date" in data.columns:
            return data.groupby("date")["volume"].rank(pct=True)
        return pd.Series(index=data.index, dtype=float)

    def _cs_rank_vol(self, data: pd.DataFrame) -> pd.Series:
        if "date" in data.columns:
            vol = data.groupby("date")["close"].transform(
                lambda x: x.pct_change().rolling(20).std())
            return vol.groupby(data["date"]).rank(pct=True)
        return pd.Series(index=data.index, dtype=float)

    def _cs_z_mom_5d(self, data: pd.DataFrame) -> pd.Series:
        if "date" in data.columns:
            mom = data.groupby("date")["close"].transform(lambda x: x.pct_change(5))
            return mom.groupby(data["date"]).transform(
                lambda x: (x - x.mean()) / (x.std() + 1e-10))
        return pd.Series(index=data.index, dtype=float)
