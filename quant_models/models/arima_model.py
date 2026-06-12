import numpy as np
from typing import Dict, Any, Optional, Tuple
from statsmodels.tsa.arima.model import ARIMA
from .. import QuantModel


class ARIMAModel(QuantModel):
    name = "ARIMA"

    def __init__(self, order: Optional[Tuple[int, int, int]] = None):
        self.order = order
        self._fitted_result = None
        self._fitted = False
        self._n = 0

    def fit(self, df, **kwargs):
        series = df['close'].dropna().values
        if len(series) < 5:
            raise ValueError("Need at least 5 data points")
        self._n = len(series)
        order = self.order or (2, 1, 2)
        model = ARIMA(series, order=order)
        self._fitted_result = model.fit()
        self._fitted = True

    def predict(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        series = df['close'].dropna().values
        if len(series) == 0:
            return np.array([], dtype=float)
        n = min(len(series), len(self._fitted_result.fittedvalues))
        return self._fitted_result.fittedvalues[:n]

    def predict_next(self, n_steps: int = 5):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        return self._fitted_result.forecast(steps=n_steps).values

    def get_params(self) -> Dict[str, Any]:
        if not self._fitted:
            return {"order": self.order}
        return {"order": self.order, "aic": float(self._fitted_result.aic), "bic": float(self._fitted_result.bic)}
