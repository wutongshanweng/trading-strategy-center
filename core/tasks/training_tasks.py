"""Celery task: train ML models asynchronously."""

from __future__ import annotations

from typing import Any

from celery import Task
from loguru import logger

from .celery_app import celery_app


class TrainingTask(Task):
    autoretry_for = (Exception,)
    max_retries = 2
    default_retry_delay = 60


@celery_app.task(
    bind=True,
    base=TrainingTask,
    queue="training",
    acks_late=True,
)
def run_training_task(
    self,
    model_type: str,
    symbol: str,
    start_date: str = "",
    end_date: str = "",
    params: dict[str, Any] | None = None,
) -> dict:
    """Train a model (xgboost / lstm / hmm) asynchronously."""
    from ml.pipeline import MLPipeline
    from core.data.market_data_manager import MarketDataManager

    self.update_state(state="PROGRESS", meta={"progress": 0.1, "status": "loading data"})

    import asyncio
    mdm = MarketDataManager()
    df = asyncio.run(mdm.get_daily(symbol, start_date, end_date))

    self.update_state(state="PROGRESS", meta={"progress": 0.3, "status": "training"})

    pipeline = MLPipeline(params=params or {})
    result = pipeline.train(df)

    self.update_state(state="SUCCESS", meta={"progress": 1.0, "status": "done"})
    logger.info(f"Training complete: {model_type}@{symbol}")
    return {"model_type": model_type, "symbol": symbol, "result": str(result)}
