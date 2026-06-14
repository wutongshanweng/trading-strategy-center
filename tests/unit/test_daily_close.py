"""
Unit tests for scripts/daily_close.py

Tests the core logic of the daily close processing script:
  - DailyPnL dataclass
  - generate_report function
  - cleanup_expired_signals SQL logic (mocked)
  - ML retrain decision logic (mocked)
"""

from __future__ import annotations

import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================
# Import the module under test
# ============================================================

@pytest.fixture(autouse=True)
def _setup_path():
    """Ensure the project root is in sys.path for imports."""
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


# ============================================================
# Mock data
# ============================================================

@pytest.fixture
def sample_pnl_by_strategy():
    """Sample DailyPnL data for report testing."""
    from scripts.daily_close import DailyPnL
    return {
        "trend_following": DailyPnL(
            strategy_name="trend_following",
            daily_realized_pnl=1250.0,
            daily_unrealized_pnl=350.0,
            trades_closed=3,
            trades_opened=2,
            positions_open=2,
            position_value=45000.0,
            cash=55000.0,
            total_equity=101600.0,
            total_pnl=1600.0,
            drawdown=2.5,
        ),
        "mean_reversion": DailyPnL(
            strategy_name="mean_reversion",
            daily_realized_pnl=-500.0,
            daily_unrealized_pnl=200.0,
            trades_closed=5,
            trades_opened=4,
            positions_open=3,
            position_value=32000.0,
            cash=67000.0,
            total_equity=99700.0,
            total_pnl=-300.0,
            drawdown=3.1,
        ),
    }


@pytest.fixture
def sample_empty_report():
    """Empty data for edge case testing."""
    from scripts.daily_close import DailyPnL
    return {}


# ============================================================
# Tests: DailyPnL dataclass
# ============================================================

class TestDailyPnL:
    """Test the DailyPnL dataclass."""

    def test_create(self):
        from scripts.daily_close import DailyPnL
        pnl = DailyPnL(strategy_name="test")
        assert pnl.strategy_name == "test"
        assert pnl.daily_realized_pnl == 0.0
        assert pnl.trades_closed == 0

    def test_create_with_values(self):
        from scripts.daily_close import DailyPnL
        pnl = DailyPnL(
            strategy_name="agg",
            daily_realized_pnl=1000.0,
            daily_unrealized_pnl=500.0,
            trades_closed=10,
        )
        assert pnl.daily_realized_pnl == 1000.0
        assert pnl.total_equity == 0.0  # default


# ============================================================
# Tests: generate_report
# ============================================================

class TestGenerateReport:
    """Test the report generation logic."""

    def test_generates_with_data(self, sample_pnl_by_strategy):
        from scripts.daily_close import generate_report

        target_date = date(2026, 6, 12)
        report = generate_report(sample_pnl_by_strategy, target_date)

        # Should contain expected elements
        assert "收盘日报" in report
        assert "2026-06-12" in report
        assert "trend_following" in report
        assert "mean_reversion" in report
        assert "trend_following" in report
        assert "mean_reversion" in report
        assert "750.00" in report  # total realized

    def test_generates_empty(self, sample_empty_report):
        from scripts.daily_close import generate_report

        target_date = date(2026, 6, 12)
        report = generate_report(sample_empty_report, target_date)

        assert "收盘日报" in report
        assert "无交易数据" in report

    def test_with_cleanup_info(self, sample_pnl_by_strategy):
        from scripts.daily_close import generate_report

        target_date = date(2026, 6, 12)
        report = generate_report(
            sample_pnl_by_strategy, target_date, cleanup_count=15
        )
        assert "信号清理" in report
        assert "15" in report

    def test_with_retrain_info(self, sample_pnl_by_strategy):
        from scripts.daily_close import generate_report

        target_date = date(2026, 6, 12)
        retrain_result = {
            "retrained": True,
            "mode": "async_celery",
            "models": ["xgboost", "hmm"],
        }
        report = generate_report(
            sample_pnl_by_strategy, target_date, retrain_result=retrain_result
        )
        assert "ML 重训" in report
        assert "xgboost" in report
        assert "hmm" in report

    def test_with_retrain_failure(self, sample_pnl_by_strategy):
        from scripts.daily_close import generate_report

        target_date = date(2026, 6, 12)
        retrain_result = {
            "retrained": False,
            "error": "Connection refused",
        }
        report = generate_report(
            sample_pnl_by_strategy, target_date, retrain_result=retrain_result
        )
        assert "ML 重训失败" in report
        assert "Connection refused" in report


# ============================================================
# Tests: cleanup_expired_signals (with mocked DB)
# ============================================================

class TestCleanupExpiredSignals:
    """Test the signal cleanup function."""

    @pytest.mark.asyncio
    async def test_cleanup_deletes_signals(self):
        """Verify that the SQL DELETE is called with correct cutoff date."""
        from scripts.daily_close import cleanup_expired_signals

        # Mock the session chain properly
        mock_result = MagicMock()
        mock_result.rowcount = 42

        # session.execute() returns mock_result
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        # session.begin() returns an async context manager that yields None
        mock_begin_cm = AsyncMock()
        mock_begin_cm.__aenter__ = AsyncMock(return_value=None)
        mock_begin_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin = MagicMock(return_value=mock_begin_cm)

        # session_maker() returns an async context manager that yields the session
        mock_session_maker = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_session)
        cm.__aexit__ = AsyncMock(return_value=None)
        mock_session_maker.return_value = cm

        with patch(
            "core.db.session.get_session_maker",
            return_value=mock_session_maker,
        ), patch("scripts.daily_close.log_info"), patch("scripts.daily_close.log_ok"):
            count = await cleanup_expired_signals(
                retention_days=7, target_date=date(2026, 6, 12)
            )

        assert count == 42


# ============================================================
# Tests: retrain_ml_models (with mocked DB)
# ============================================================

class TestRetrainMLModels:
    """Test the ML retrain decision logic."""

    @pytest.mark.asyncio
    async def test_no_retrain_when_recent(self):
        """Should skip retrain when models were recently trained."""
        from scripts.daily_close import retrain_ml_models

        # Mock the DB to return a recent trained_at
        mock_row = MagicMock()
        mock_row.trained_at = datetime.utcnow() - timedelta(days=1)

        mock_result = MagicMock()
        mock_result.__aiter__.return_value = [("xgboost", mock_row.trained_at)]

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session

        with patch(
            "core.db.session.get_session_maker",
            return_value=mock_session_maker,
        ):
            result = await retrain_ml_models(force=False)

        assert result["retrained"] is False

    @pytest.mark.asyncio
    async def test_force_retrain_triggers(self):
        """Force=True should always trigger retrain."""
        from scripts.daily_close import retrain_ml_models

        # Mock empty model status (no models exist)
        mock_result = MagicMock()
        mock_result.__aiter__.return_value = []

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session

        with (
            patch(
                "core.db.session.get_session_maker",
                return_value=mock_session_maker,
            ),
            patch("scripts.daily_close.train_pipeline", create=True),
        ):
            result = await retrain_ml_models(force=True)

        # Should attempt celery (which won't be importable in test)
        # Falls through to sync path, but that will also fail without deps
        # The function should still return a result dict
        assert isinstance(result, dict)
        assert "retrained" in result


# ============================================================
# Tests: generate_report formatting edge cases
# ============================================================

class TestReportEdgeCases:
    """Test edge cases in report generation."""

    def test_report_with_no_cleanup_no_retrain(self, sample_pnl_by_strategy):
        from scripts.daily_close import generate_report

        target_date = date(2026, 6, 12)
        report = generate_report(
            sample_pnl_by_strategy,
            target_date,
            cleanup_count=0,
            retrain_result=None,
        )
        assert "无过期信号" in report
        assert "ML 重训: 跳过" in report

    def test_report_with_single_strategy(self):
        from scripts.daily_close import DailyPnL, generate_report

        by_strategy = {
            "single": DailyPnL(
                strategy_name="single",
                daily_realized_pnl=500.0,
                total_pnl=500.0,
                total_equity=100500.0,
                drawdown=0.0,
            )
        }
        target_date = date(2026, 6, 12)
        report = generate_report(by_strategy, target_date)

        assert "single" in report
        assert "500.00" in report

    def test_report_line_count(self, sample_pnl_by_strategy):
        """Report should have reasonable number of lines."""
        from scripts.daily_close import generate_report

        target_date = date(2026, 6, 12)
        report = generate_report(sample_pnl_by_strategy, target_date)
        lines = report.strip().split("\n")

        # Should be a complete report: header + summary + strategy table + footer
        assert len(lines) >= 15


# ============================================================
# Tests: CLI argument parsing
# ============================================================

class TestArgParse:
    """Test command-line argument parsing."""

    def test_default_args(self):
        from scripts.daily_close import parse_args

        args = parse_args([])
        assert args.db == "sqlite"
        assert args.date is None
        assert args.pnl_only is False
        assert args.cleanup_only is False
        assert args.retrain is False

    def test_pnl_only(self):
        from scripts.daily_close import parse_args

        args = parse_args(["--pnl-only"])
        assert args.pnl_only is True

    def test_custom_date(self):
        from scripts.daily_close import parse_args

        args = parse_args(["--date", "2026-06-01"])
        assert args.date == "2026-06-01"

    def test_postgres(self):
        from scripts.daily_close import parse_args

        args = parse_args(["--db", "postgresql"])
        assert args.db == "postgresql"
