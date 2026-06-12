import numpy as np
from typing import Dict, Any
from .. import QuantModel


class MonteCarloModel(QuantModel):
    name = "MonteCarlo"

    def __init__(self, n_paths: int = 1000, n_steps: int = 252, seed: int = 42):
        self.n_paths = n_paths
        self.n_steps = n_steps
        self.seed = seed
        self.mu = self.sigma = self.last_price = None
        self._fitted = False

    def fit(self, df, **kwargs):
        close = df['close'].dropna().values
        if len(close) < 20:
            raise ValueError("Need at least 20 data points")
        returns = np.diff(np.log(close))
        self.mu = float(returns.mean())
        self.sigma = float(returns.std())
        self.last_price = float(close[-1])
        self._fitted = True

    def predict(self, df):
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        s0 = float(df['close'].dropna().iloc[-1])
        dt = 1.0 / 252
        rng = np.random.default_rng(self.seed)
        drift = (self.mu - 0.5 * self.sigma ** 2) * dt
        diffusion = self.sigma * np.sqrt(dt) * rng.normal(0, 1, size=(self.n_paths, self.n_steps))
        return s0 * np.exp(np.cumsum(drift + diffusion, axis=1))

    def summary(self):
        return {"expected_return": float(np.exp(self.mu * self.n_steps / 252) - 1),
                "expected_vol": float(self.sigma * np.sqrt(self.n_steps / 252)),
                "last_price": self.last_price}

    def get_params(self) -> Dict[str, Any]:
        return {"mu": self.mu, "sigma": self.sigma, "last_price": self.last_price,
                "n_paths": self.n_paths, "n_steps": self.n_steps}
