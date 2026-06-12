from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from quant_models.models.linear_regression_model import LinearRegressionModel
from quant_models.models.arima_model import ARIMAModel
from quant_models.models.garch_model import GARCHModel
from quant_models.models.hmm_model import HMModel
from quant_models.models.random_forest_model import RandomForestModel
from api.routes.data_routes import get_data_manager

router = APIRouter(prefix="/api/v1/models", tags=["ml"])

_MODELS = {
    "linear_regression": (LinearRegressionModel, {"fit_intercept"}),
    "arima": (ARIMAModel, {"order", "trend"}),
    "garch": (GARCHModel, {"p", "q"}),
    "hmm": (HMModel, {"n_components", "n_iter", "random_state"}),
    "random_forest": (RandomForestModel, {"n_estimators", "max_depth", "random_state"}),
}
_instances: Dict[str, Any] = {}


class TrainRequest(BaseModel):
    symbol: str
    timeframe: str = "1d"
    params: Optional[Dict[str, Any]] = None


class PredictRequest(BaseModel):
    symbol: str
    timeframe: str = "1d"


@router.get("")
async def list_models():
    return {"models": list(_MODELS.keys())}


@router.post("/{name}/train")
async def train_model(name: str, req: TrainRequest):
    if name not in _MODELS:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not found")
    cls, allowed_params = _MODELS[name]
    raw_params = req.params or {}
    filtered_params = {k: v for k, v in raw_params.items() if k in allowed_params}
    dm = get_data_manager()
    feed = await dm.get_data_feed(req.symbol, req.timeframe)
    model = cls(**filtered_params)
    model.fit(feed.df)
    _instances[f"{name}:{req.symbol}"] = model
    return {"model": name, "symbol": req.symbol, "status": "trained",
            "params": model.get_params()}


@router.post("/{name}/predict")
async def predict_model(name: str, req: PredictRequest):
    key = f"{name}:{req.symbol}"
    if key not in _instances:
        raise HTTPException(status_code=400, detail=f"Model '{name}' not trained for {req.symbol}")
    dm = get_data_manager()
    feed = await dm.get_data_feed(req.symbol, req.timeframe)
    model = _instances[key]
    preds = model.predict(feed.df)
    return {"model": name, "symbol": req.symbol, "predictions": preds.tolist()}
