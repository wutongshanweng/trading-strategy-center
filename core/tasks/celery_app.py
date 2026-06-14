"""Celery application instance with queue routing and concurrency settings."""

from __future__ import annotations

from celery import Celery
from core.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "trading_strategy_center",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "core.tasks.backtest_tasks",
        "core.tasks.training_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    task_time_limit=3600,       # 1 hour max
    task_soft_time_limit=3000,   # 50 min soft limit
    worker_max_tasks_per_child=50,
    task_routes={
        "core.tasks.backtest_tasks.*": {"queue": "backtest"},
        "core.tasks.training_tasks.*": {"queue": "training"},
    },
    task_queues={
        "backtest": {"exchange": "default", "routing_key": "backtest"},
        "training": {"exchange": "default", "routing_key": "training"},
    },
)
