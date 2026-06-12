import numpy as np
import pandas as pd
from typing import Dict, Any
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from .. import QuantModel


class ClusterModel(QuantModel):
    name = "Cluster"

    def __init__(self, n_clusters: int = 4, method: str = 'kmeans', eps: float = 0.5, min_samples: int = 5):
        self.n_clusters = n_clusters
        self.method = method
        self.eps = eps
        self.min_samples = min_samples
        self.model = None
        self.scaler = StandardScaler()
        self._fitted = False

    def _build_features(self, df):
        close = df['close'].dropna().values
        if len(close) < 11:
            return np.empty((0, 2))
        returns = np.diff(np.log(close))
        vol = pd.Series(returns ** 2).rolling(10).mean().dropna().values
        returns = returns[-len(vol):]
        return np.column_stack([returns, vol])

    def fit(self, df, **kwargs):
        features = self._build_features(df)
        if features.shape[0] < 20:
            raise ValueError("Need at least 20 data points")
        features_scaled = self.scaler.fit_transform(features)
        if self.method == 'kmeans':
            self.model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        else:
            self.model = DBSCAN(eps=self.eps, min_samples=self.min_samples)
        self.model.fit(features_scaled)
        self._fitted = True

    def predict(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        features = self._build_features(df)
        if features.shape[0] == 0:
            return np.array([], dtype=int)
        features_scaled = self.scaler.transform(features)
        if self.method == 'kmeans':
            return self.model.predict(features_scaled)
        return self.model.fit_predict(features_scaled)

    def get_params(self) -> Dict[str, Any]:
        return {"method": self.method, "n_clusters": self.n_clusters}
