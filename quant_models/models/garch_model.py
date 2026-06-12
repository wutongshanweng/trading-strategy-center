import numpy as np
from typing import Dict, Any
from arch import arch_model
from .. import QuantModel


class GARCHModel(QuantModel):
    name = "GARCH"

    def __init__(self, p: int = 1, q: int = 1):
        self.p = p
        self.q = q
        self._fitted_result = None
        self._fitted = False
        self.omega = self.alpha = self.beta = None

    def fit(self, df, **kwargs):
        close = df['close'].dropna().values
        if len(close) < 10:
            raise ValueError("Need at least 10 data points")
        returns = 100.0 * np.diff(np.log(close))
        am = arch_model(returns, vol='Garch', p=self.p, q=self.q)
        self._fitted_result = am.fit(disp='off')
        self.omega = float(self._fitted_result.params.get('omega', 0))
        self.alpha = float(self._fitted_result.params.get('alpha[1]', 0))
        self.beta = float(self._fitted_result.params.get('beta[1]', 0))
        self._fitted = True

    def predict(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        close = df['close'].dropna().values
        if len(close) < 2:
            return np.array([], dtype=float)
        n = min(len(close) - 1, len(self._fitted_result.conditional_volatility))
        return self._fitted_result.conditional_volatility[:n]

    def predict_volatility(self, horizon: int = 5):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        forecasts = self._fitted_result.forecast(horizon=horizon)
        return np.sqrt(forecasts.variance.values[-1])

    def get_params(self) -> Dict[str, Any]:
        return {"p": self.p, "q": self.q, "omega": self.omega, "alpha": self.alpha, "beta": self.beta}
