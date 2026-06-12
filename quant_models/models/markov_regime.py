from typing import Dict, Any
import numpy as np
import pandas as pd
from .. import QuantModel


class MarkovRegimeModel(QuantModel):
    name = "MarkovRegime"

    def __init__(self, k_regimes: int = 2):
        self.k_regimes = k_regimes
        self._fitted_result = None
        self._fitted = False

    def fit(self, df, **kwargs):
        close = df['close'].dropna().values
        if len(close) < 30:
            raise ValueError("Need at least 30 data points")
        returns = pd.Series(np.diff(np.log(close)) * 100, name='returns')
        from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
        model = MarkovRegression(returns, k_regimes=self.k_regimes, trend='c')
        self._fitted_result = model.fit()
        self._fitted = True

    def predict(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        close = df['close'].dropna().values
        if len(close) < 2:
            return np.array([], dtype=float)
        returns = np.diff(np.log(close)) * 100
        probs = self._fitted_result.smoothed_marginal_probabilities
        if isinstance(probs, pd.DataFrame):
            probs = probs.iloc[:, 0].values
        n = min(len(returns), len(probs))
        return np.asarray(probs[:n])

    def get_params(self) -> Dict[str, Any]:
        if not self._fitted:
            return {"k_regimes": self.k_regimes}
        return {"k_regimes": self.k_regimes, "aic": float(self._fitted_result.aic),
                "bic": float(self._fitted_result.bic)}
