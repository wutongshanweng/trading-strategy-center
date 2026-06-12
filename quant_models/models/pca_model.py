import numpy as np
from typing import Dict, Any, Optional
from sklearn.decomposition import PCA
from .. import QuantModel


class PCAModel(QuantModel):
    name = "PCA"

    def __init__(self, n_components: Optional[int] = None, variance_ratio: float = 0.95):
        self.n_components = n_components
        self.variance_ratio = variance_ratio
        self.pca = None
        self._fitted = False

    def _extract_matrix(self, df):
        return df.select_dtypes(include=[np.number]).dropna().values

    def fit(self, df, **kwargs):
        data = self._extract_matrix(df)
        if data.shape[1] < 2:
            raise ValueError("Need at least 2 numeric columns")
        n = self.n_components or self.variance_ratio
        self.pca = PCA(n_components=min(n, data.shape[1]) if isinstance(n, int) else n)
        self.pca.fit(data)
        self._fitted = True

    def predict(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        data = self._extract_matrix(df)
        if data.shape[0] == 0:
            return np.array([])
        return self.pca.transform(data)

    def get_params(self) -> Dict[str, Any]:
        if not self._fitted:
            return {}
        return {"n_components_": int(self.pca.n_components_),
                "explained_variance_ratio_": self.pca.explained_variance_ratio_.tolist()}
