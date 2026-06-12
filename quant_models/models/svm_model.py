import numpy as np
import pandas as pd
from typing import Dict, Any
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from .. import QuantModel


class SVMModel(QuantModel):
    name = "SVM"

    def __init__(self, kernel: str = 'rbf', C: float = 1.0, epsilon: float = 0.1, threshold: float = 0.005):
        self.kernel = kernel
        self.C = C
        self.epsilon = epsilon
        self.threshold = threshold
        self.model = SVR(kernel=kernel, C=C, epsilon=epsilon)
        self.scaler = StandardScaler()
        self._fitted = False

    def _features(self, df):
        close = df['close'].dropna().values
        n = len(close)
        if n < 30:
            return np.empty((0, 6))
        volume = df['volume'].dropna().values if 'volume' in df.columns else np.ones(n)
        returns = np.diff(close) / close[:-1]
        returns = np.concatenate([[0], returns])
        vol = pd.Series(returns).rolling(10).std().fillna(0).values
        avg_gain = pd.Series(np.where(np.diff(close) > 0, np.diff(close), 0)).rolling(14).mean().fillna(0).values
        avg_loss = pd.Series(np.where(np.diff(close) < 0, -np.diff(close), 0)).rolling(14).mean().fillna(1e-10).values
        rsi = np.concatenate([[50], 100 - 100 / (1 + avg_gain / avg_loss)])
        ema12 = pd.Series(close).ewm(span=12).mean().values
        ema26 = pd.Series(close).ewm(span=26).mean().values
        sma20 = pd.Series(close).rolling(20).mean().fillna(method='bfill').fillna(close).values
        return np.column_stack([returns[:n], vol[:n], volume[:n], rsi[:n],
                                (ema12 - ema26)[:n], close[:n] / sma20[:n] - 1])

    def fit(self, df, **kwargs):
        features = self._features(df)
        if features.shape[0] < 30:
            raise ValueError("Need at least 30 data points")
        close = df['close'].dropna().values[:features.shape[0]]
        target = np.diff(close) / close[:-1]
        features_scaled = self.scaler.fit_transform(features[:-1])
        self.model.fit(features_scaled, target)
        self._fitted = True

    def predict(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        features = self._features(df)
        if features.shape[0] < 2:
            return np.array([], dtype=float)
        pred = self.model.predict(self.scaler.transform(features[:-1]))
        return np.where(pred > self.threshold, 1, np.where(pred < -self.threshold, -1, 0))

    def get_params(self) -> Dict[str, Any]:
        return {"kernel": self.kernel, "C": self.C, "epsilon": self.epsilon, "threshold": self.threshold}
