"""HAR-RV (Heterogeneous Autoregressive Realized Volatility) 模型。

Corsi (2009) 的经典已实现波动率预测模型:用日/周/月三个时间尺度的
已实现波动率(RV)线性预测下一期 RV,捕捉波动率的长记忆特性。

RV_{t+1} = c + b_d * RV_d + b_w * RV_w + b_m * RV_m + e
其中 RV_d = 当日 RV, RV_w = 过去5日均值, RV_m = 过去22日均值。
"""
from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd

from .. import QuantModel


def realized_variance(close: pd.Series) -> pd.Series:
    """用日对数收益平方近似日已实现方差(无日内数据时的退化估计)。"""
    log_ret = np.log(close / close.shift(1))
    return log_ret ** 2


class HARRVModel(QuantModel):
    """HAR-RV 波动率预测模型。"""

    name = "HAR-RV"

    def __init__(self, weekly: int = 5, monthly: int = 22):
        self.weekly = weekly
        self.monthly = monthly
        self.coef_: np.ndarray | None = None       # [c, b_d, b_w, b_m]
        self._fitted = False
        self._last_features: np.ndarray | None = None

    def _build_features(self, rv: pd.Series) -> pd.DataFrame:
        rv_d = rv
        rv_w = rv.rolling(self.weekly).mean()
        rv_m = rv.rolling(self.monthly).mean()
        feats = pd.DataFrame({
            "rv_d": rv_d,
            "rv_w": rv_w,
            "rv_m": rv_m,
            "target": rv.shift(-1),
        }).dropna()
        return feats

    def fit(self, df, **kwargs):
        close = df["close"].dropna()
        if len(close) < self.monthly + 5:
            raise ValueError(f"Need at least {self.monthly + 5} data points")
        rv = realized_variance(close).dropna()
        feats = self._build_features(rv)
        if len(feats) < 10:
            raise ValueError("Insufficient data after feature construction")
        X = np.column_stack([
            np.ones(len(feats)),
            feats["rv_d"].values,
            feats["rv_w"].values,
            feats["rv_m"].values,
        ])
        y = feats["target"].values
        # OLS 闭式解
        self.coef_, *_ = np.linalg.lstsq(X, y, rcond=None)
        # 缓存最近一组特征用于一步预测
        self._last_features = np.array([
            1.0,
            rv.iloc[-1],
            rv.tail(self.weekly).mean(),
            rv.tail(self.monthly).mean(),
        ])
        self._fitted = True
        return self

    def predict(self, df):
        """返回拟合期内的逐点预测 RV(年化波动率)。"""
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        close = df["close"].dropna()
        rv = realized_variance(close).dropna()
        feats = self._build_features(rv)
        if feats.empty:
            return np.array([], dtype=float)
        X = np.column_stack([
            np.ones(len(feats)),
            feats["rv_d"].values,
            feats["rv_w"].values,
            feats["rv_m"].values,
        ])
        pred_var = X @ self.coef_
        pred_var = np.maximum(pred_var, 0.0)
        return np.sqrt(pred_var * 252)  # 年化波动率

    def forecast_next(self) -> float:
        """一步向前预测下一期年化波动率。"""
        if not self._fitted or self._last_features is None:
            raise RuntimeError("Model not fitted yet")
        pred_var = max(float(self._last_features @ self.coef_), 0.0)
        return float(np.sqrt(pred_var * 252))

    def get_params(self) -> Dict[str, Any]:
        if not self._fitted:
            return {"weekly": self.weekly, "monthly": self.monthly}
        return {
            "weekly": self.weekly,
            "monthly": self.monthly,
            "const": float(self.coef_[0]),
            "beta_daily": float(self.coef_[1]),
            "beta_weekly": float(self.coef_[2]),
            "beta_monthly": float(self.coef_[3]),
        }
