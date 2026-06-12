import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from sklearn.ensemble import RandomForestRegressor
from .. import QuantModel


class RandomForestModel(QuantModel):
    name = "RandomForest"

    def __init__(self, n_estimators: int = 100, max_depth: Optional[int] = None, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=random_state)
        self._fitted = False

    def _features(self, df):
        close = df['close'].dropna().values
        n = len(close)
        if n < 30:
            return np.empty((0, 5))
        volume = df['volume'].dropna().values if 'volume' in df.columns else np.ones(n)
        returns = np.diff(close) / close[:-1]
        returns = np.concatenate([[0], returns])
        vol = pd.Series(returns).rolling(10).std().fillna(0).values
        delta = np.diff(close)
        avg_gain = pd.Series(np.where(delta > 0, delta, 0)).rolling(14).mean().fillna(0).values
        avg_loss = pd.Series(np.where(delta < 0, -delta, 0)).rolling(14).mean().fillna(1e-10).values
        rsi = np.concatenate([[50], 100 - 100 / (1 + avg_gain / avg_loss)])
        ema12 = pd.Series(close).ewm(span=12).mean().values
        ema26 = pd.Series(close).ewm(span=26).mean().values
        macd = ema12 - ema26
        return np.column_stack([returns[:n], vol[:n], volume[:n], rsi[:n], macd[:n]])

    def fit(self, df, **kwargs):
        features = self._features(df)
        if features.shape[0] < 30:
            raise ValueError("Need at least 30 data points")
        close = df['close'].dropna().values[:features.shape[0]]
        target = np.diff(close) / close[:-1]
        self.model.fit(features[:-1], target)
        self._fitted = True

    def predict(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        features = self._features(df)
        if features.shape[0] < 2:
            return np.array([], dtype=float)
        return self.model.predict(features[:-1])

    def get_params(self) -> Dict[str, Any]:
        if not self._fitted:
            return {"n_estimators": self.n_estimators, "max_depth": self.max_depth}
        return {"n_estimators": self.n_estimators, "feature_importances_": self.model.feature_importances_.tolist()}
