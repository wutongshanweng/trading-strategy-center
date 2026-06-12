import numpy as np
from typing import Dict, Any
from scipy import stats
from .. import QuantModel


class CopulaModel(QuantModel):
    name = "Copula"

    def __init__(self):
        self.corr_matrix = None
        self._pseudo = None
        self._fitted = False

    def fit(self, df, **kwargs):
        numeric = df.select_dtypes(include=[np.number]).dropna()
        if numeric.shape[1] < 2:
            raise ValueError("Need at least 2 numeric columns")
        n, d = numeric.shape
        pseudo = np.empty_like(numeric.values)
        for i in range(d):
            pseudo[:, i] = stats.rankdata(numeric.values[:, i]) / (n + 1)
        normed = stats.norm.ppf(pseudo)
        self.corr_matrix = np.corrcoef(normed.T)
        self._pseudo = pseudo
        self._fitted = True

    def predict(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        return self.corr_matrix

    def tail_dependence(self, quantile: float = 0.95):
        if self._pseudo is None or self._pseudo.shape[1] < 2:
            return {"upper": 0.0, "lower": 0.0}
        p = self._pseudo
        upper = np.mean((p[:, 0] > quantile) & (p[:, 1] > quantile)) / max(1 - quantile, 1e-10)
        lower = np.mean((p[:, 0] < 1 - quantile) & (p[:, 1] < 1 - quantile)) / max(1 - quantile, 1e-10)
        return {"upper": float(min(upper, 1.0)), "lower": float(min(lower, 1.0))}

    def get_params(self) -> Dict[str, Any]:
        if not self._fitted:
            return {}
        return {"correlation_matrix": self.corr_matrix.tolist(),
                "tail_dependence": self.tail_dependence()}
