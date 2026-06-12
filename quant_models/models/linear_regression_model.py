import numpy as np
from typing import Dict, Any
from sklearn.linear_model import LinearRegression
from .. import QuantModel


class LinearRegressionModel(QuantModel):
    name = "LinearRegression"

    def __init__(self, fit_intercept: bool = True):
        self.fit_intercept = fit_intercept
        self.model = LinearRegression(fit_intercept=fit_intercept)
        self._fitted = False
        self._slope = None
        self._intercept = None
        self._n = 0

    def fit(self, df, **kwargs):
        close = df['close'].dropna().values
        if len(close) < 2:
            raise ValueError("Need at least 2 close prices")
        self._n = len(close)
        X = np.arange(self._n).reshape(-1, 1)
        self.model.fit(X, close)
        self._slope = float(self.model.coef_[0])
        self._intercept = float(self.model.intercept_) if self.fit_intercept else 0.0
        self._fitted = True

    def predict(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        close = df['close'].dropna().values
        if len(close) == 0:
            return np.array([], dtype=float)
        X = np.arange(len(close)).reshape(-1, 1)
        return self.model.predict(X)

    def predict_next(self, n_steps: int = 5):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        X = np.arange(self._n, self._n + n_steps).reshape(-1, 1)
        return self.model.predict(X)

    def get_params(self) -> Dict[str, Any]:
        return {"fit_intercept": self.fit_intercept, "slope": self._slope, "intercept": self._intercept}
