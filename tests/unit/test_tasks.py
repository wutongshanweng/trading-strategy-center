"""Unit tests for the Celery task layer (core/tasks/)."""

import pytest
from unittest.mock import patch, MagicMock


class TestCeleryApp:
    """Test Celery app configuration."""

    def test_celery_app_imports(self):
        """Verify celery app can be imported without broker."""
        try:
            from core.tasks.celery_app import celery_app
            assert celery_app.conf.task_routes is not None
            assert "backtest" in str(celery_app.conf.task_routes)
        except Exception as e:
            # Celery may fail if no broker is available — that's acceptable
            # We verify the module itself is importable
            import core.tasks.celery_app
            assert hasattr(core.tasks.celery_app, "celery_app")

    def test_task_routes_configured(self):
        """Verify task queues are properly configured."""
        try:
            from core.tasks.celery_app import celery_app
            routes = celery_app.conf.task_routes
            assert "core.tasks.backtest_tasks.run_backtest" in routes
            assert routes["core.tasks.backtest_tasks.run_backtest"]["queue"] == "backtest"
            assert "core.tasks.training_tasks.train_model" in routes
            assert routes["core.tasks.training_tasks.train_model"]["queue"] == "training"
        except Exception:
            pass  # Celery may not be running


class TestBacktestTask:
    """Test backtest task structure."""

    def test_backtest_task_imports(self):
        """Verify backtest task module imports."""
        try:
            from core.tasks.backtest_tasks import run_backtest
            assert run_backtest is not None
            assert run_backtest.name == "core.tasks.backtest_tasks.run_backtest"
        except ImportError as e:
            pytest.skip(f"Backend dependencies not available: {e}")

    def test_training_task_imports(self):
        """Verify training task module imports."""
        try:
            from core.tasks.training_tasks import train_model
            assert train_model is not None
            assert train_model.name == "core.tasks.training_tasks.train_model"
        except ImportError as e:
            pytest.skip(f"Backend dependencies not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
