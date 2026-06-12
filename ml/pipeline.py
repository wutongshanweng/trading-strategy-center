from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from loguru import logger


@dataclass
class MLPipelineConfig:
    layers: List[str] = field(default_factory=lambda: ["hmm", "xgboost", "garch", "var"])
    lookback: int = 252
    train_split: float = 0.8
    retrain_frequency: int = 20


class MLPipeline:
    def __init__(self, config: MLPipelineConfig = None):
        self.config = config or MLPipelineConfig()
        self.models: Dict[str, Any] = {}
        self._trained = False

    async def train(self, df: pd.DataFrame, symbol: str = "") -> Dict[str, Any]:
        results = {}
        close = df["close"].dropna().values
        if len(close) < 50:
            return {"status": "insufficient_data"}
        returns = np.diff(np.log(close))

        if "hmm" in self.config.layers:
            try:
                from hmmlearn import hmm
                model = hmm.GaussianHMM(n_components=3, n_iter=100, random_state=42)
                model.fit(returns.reshape(-1, 1))
                self.models["hmm"] = model
                states = model.predict(returns.reshape(-1, 1))
                results["hmm"] = {"states": states[-1], "regime_probs": model.predict_proba(returns[-1:].reshape(-1, 1)).tolist()[0]}
            except Exception as e:
                results["hmm"] = {"error": str(e)}

        if "xgboost" in self.config.layers:
            try:
                from xgboost import XGBRegressor
                features = np.column_stack([returns[i-5:i] for i in range(5, len(returns))]).T if len(returns) > 5 else returns[:-1]
                target = returns[5:] if len(returns) > 5 else returns[1:]
                if len(features) > 10:
                    model = XGBRegressor(
                        n_estimators=100,
                        max_depth=6,
                        learning_rate=0.1,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        random_state=42
                    )
                    model.fit(features[:-5], target[:-5])
                    self.models["xgboost"] = model
                    pred = model.predict(features[-5:])
                    results["xgboost"] = {"pred_return": float(pred.mean())}
                else:
                    results["xgboost"] = {"error": "insufficient_data"}
            except Exception as e:
                results["xgboost"] = {"error": str(e)}

        if "garch" in self.config.layers:
            try:
                from arch import arch_model
                model = arch_model(returns * 100, vol="Garch", p=1, q=1)
                res = model.fit(disp="off")
                self.models["garch"] = res
                forecast = res.forecast(horizon=5)
                vol = float(np.sqrt(forecast.variance.values[-1]).mean())
                results["garch"] = {"volatility": vol, "omega": float(res.params.get("omega", 0)),
                                    "alpha": float(res.params.get("alpha[1]", 0)),
                                    "beta": float(res.params.get("beta[1]", 0))}
            except Exception as e:
                results["garch"] = {"error": str(e)}

        if "var" in self.config.layers:
            var_95 = float(np.percentile(returns, 5))
            var_99 = float(np.percentile(returns, 1))
            cvar_95 = float(returns[returns <= var_95].mean()) if any(returns <= var_95) else 0.0
            results["var"] = {"var_95": var_95, "var_99": var_99, "cvar_95": cvar_95}

        self._trained = True
        return results

    async def predict(self, df: pd.DataFrame) -> Dict[str, np.ndarray]:
        if not self._trained:
            return {"status": "not_trained"}
        close = df["close"].dropna().values
        if len(close) < 10:
            return {"status": "insufficient_data"}
        returns = np.diff(np.log(close))

        result = {}
        if "hmm" in self.models:
            states = self.models["hmm"].predict(returns.reshape(-1, 1))
            result["regime"] = states
        if "xgboost" in self.models:
            features = np.column_stack([returns[i-5:i] for i in range(5, len(returns))]).T if len(returns) > 5 else returns[1:]
            if len(features) > 0:
                result["price"] = self.models["xgboost"].predict(features[-1:])[-1]
        var_95 = np.percentile(returns, 5) if len(returns) > 20 else 0.0
        result["var_95"] = np.array([var_95])
        return result

    def get_pipeline_summary(self) -> Dict:
        return {"models_trained": list(self.models.keys()), "status": "trained" if self._trained else "idle"}
