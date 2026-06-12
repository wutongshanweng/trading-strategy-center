from tasks.celery_app import celery_app
from loguru import logger
import numpy as np
import pandas as pd


def _generate_training_data(symbol, lookback_days):
    np.random.seed(hash(f"train_{symbol}") % (2**31))
    dates = pd.date_range(end=pd.Timestamp.today(), periods=lookback_days)
    returns = np.random.normal(0.0005, 0.015, lookback_days)
    close = 100.0 * np.exp(np.cumsum(returns))
    return pd.DataFrame({
        "close": close,
        "volume": np.random.randint(10000, 1000000, lookback_days),
    }, index=dates)


@celery_app.task(name="train_pipeline", bind=True, max_retries=2)
def train_pipeline(self, symbol, lookback_days=365):
    try:
        logger.info(f"train_pipeline: {symbol} lookback={lookback_days}d")
        df = _generate_training_data(symbol, lookback_days)
        from ml.pipeline import MLPipeline
        pipe = MLPipeline()
        result = pipe.train(df, symbol)
        return {
            "status": "success", "symbol": symbol,
            "metrics": {
                str(k): float(v) if isinstance(v, (np.floating, np.integer)) else v
                for k, v in result.items()
            },
        }
    except Exception as e:
        logger.error(f"train_pipeline failed: {e}")
        countdown = min(60 * (2 ** self.request.retries), 3600)
        raise self.retry(exc=e, countdown=countdown)


@celery_app.task(name="train_all_models", bind=True, max_retries=2)
def train_all_models(self, symbol="SYNTHETIC", lookback_days=365):
    try:
        logger.info(f"train_all_models: {symbol} lookback={lookback_days}d")
        df = _generate_training_data(symbol, lookback_days)
        from quant_models.models.linear_regression_model import LinearRegressionModel
        from quant_models.models.arima_model import ARIMAModel
        from quant_models.models.garch_model import GARCHModel
        from quant_models.models.hmm_model import HMModel
        from quant_models.models.kalman_model import KalmanFilterModel
        from quant_models.models.hurst_model import HurstExponentModel
        from quant_models.models.wavelet_model import WaveletDenoiserModel
        from quant_models.models.pca_model import PCAModel
        from quant_models.models.cluster_model import ClusterModel
        from quant_models.models.copula_model import CopulaModel
        from quant_models.models.monte_carlo_model import MonteCarloModel
        from quant_models.models.markov_regime import MarkovRegimeModel
        from quant_models.models.random_forest_model import RandomForestModel
        from quant_models.models.svm_model import SVMModel
        models = [
            ("LinearRegression", LinearRegressionModel), ("ARIMA", ARIMAModel),
            ("GARCH", GARCHModel), ("HMM", HMModel), ("KalmanFilter", KalmanFilterModel),
            ("HurstExponent", HurstExponentModel), ("WaveletDenoiser", WaveletDenoiserModel),
            ("PCA", PCAModel), ("Cluster", ClusterModel), ("Copula", CopulaModel),
            ("MonteCarlo", MonteCarloModel), ("MarkovRegime", MarkovRegimeModel),
            ("RandomForest", RandomForestModel), ("SVM", SVMModel),
        ]
        results = {}
        for name, cls in models:
            try:
                model = cls()
                if hasattr(model, "fit"):
                    model.fit(df)
                elif hasattr(model, "train"):
                    model.train(df)
                results[name] = "trained"
            except Exception as e:
                results[name] = f"failed: {e}"
        return {"status": "success", "symbol": symbol, "models": results}
    except Exception as e:
        logger.error(f"train_all_models failed: {e}")
        countdown = min(60 * (2 ** self.request.retries), 3600)
        raise self.retry(exc=e, countdown=countdown)
