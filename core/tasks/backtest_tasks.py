"""Celery task: run vectorized backtest asynchronously."""

from __future__ import annotations

from typing import Any

from celery import Task
from loguru import logger

from .celery_app import celery_app


class BacktestTask(Task):
    """Base task for backtesting with progress tracking."""

    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = 30

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Backtest task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    bind=True,
    base=BacktestTask,
    queue="backtest",
    acks_late=True,
    reject_on_worker_lost=True,
)
def run_backtest_task(
    self,
    strategy: str,
    symbol: str,
    start_date: str,
    end_date: str,
    params: dict[str, Any] | None = None,
) -> dict:
    """Run a vectorized backtest and return performance metrics."""
    from backtest.vectorized_engine import VectorizedBacktest
    from core.data.market_data_manager import MarketDataManager

    self.update_state(state="PROGRESS", meta={"progress": 0.1, "status": "fetching data"})

    mdm = MarketDataManager()
    # Use the synchronous mock for now — wire real data later
    import asyncio
    df = asyncio.run(mdm.get_daily(symbol, start_date, end_date))

    self.update_state(state="PROGRESS", meta={"progress": 0.4, "status": "running backtest"})

    bt = VectorizedBacktest(
        strategy=strategy,
        symbol=symbol,
        data=df,
        params=params or {},
    )
    result = bt.run()

    self.update_state(state="PROGRESS", meta={"progress": 1.0, "status": "done"})
    logger.info(f"Backtest complete: {strategy}@{symbol} Sharpe={result.get('sharpe_ratio', 'N/A')}")
    return result
