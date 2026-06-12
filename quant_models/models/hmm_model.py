import numpy as np
from typing import Dict, Any
from hmmlearn import hmm
from .. import QuantModel


class HMModel(QuantModel):
    name = "HMM"

    def __init__(self, n_states: int = 3, n_iter: int = 100, random_state: int = 42):
        self.n_states = n_states
        self.n_iter = n_iter
        self.random_state = random_state
        self.model = None
        self._fitted = False

    def fit(self, df, **kwargs):
        close = df['close'].dropna().values
        if len(close) < 20:
            raise ValueError("Need at least 20 data points")
        returns = np.diff(np.log(close)).reshape(-1, 1)
        self.model = hmm.GaussianHMM(n_components=self.n_states, n_iter=self.n_iter,
                                     random_state=self.random_state)
        self.model.fit(returns)
        self._fitted = True

    def predict(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        close = df['close'].dropna().values
        if len(close) < 2:
            return np.array([], dtype=int)
        returns = np.diff(np.log(close)).reshape(-1, 1)
        return self.model.predict(returns)

    def predict_proba(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        close = df['close'].dropna().values
        if len(close) < 2:
            return np.empty((0, self.n_states))
        returns = np.diff(np.log(close)).reshape(-1, 1)
        return self.model.predict_proba(returns)

    def get_params(self) -> Dict[str, Any]:
        if not self._fitted:
            return {"n_states": self.n_states}
        return {"n_states": self.n_states, "transmat": self.model.transmat_.tolist(),
                "means": self.model.means_.flatten().tolist()}
