from celery import Celery
from core.config.settings import get_settings

settings = get_settings()
celery_app = Celery("trading", broker=settings.celery_broker_url, backend=settings.celery_result_backend)
celery_app.conf.update(
    task_serializer="json", result_serializer="json", accept_content=["json"],
    task_track_started=True, task_acks_late=True, worker_prefetch_multiplier=1,
    task_queues={"backtest": {"routing_key": "backtest"}, "training": {"routing_key": "training"}, "reports": {"routing_key": "reports"}},
    task_routes={"tasks.backtest_tasks.*": {"queue": "backtest"}, "tasks.training_tasks.*": {"queue": "training"}},
)
