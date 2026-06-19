"""Factor Management System.

Provides SQLite-backed storage, versioning, monitoring, and retirement
for alpha factors.
"""

import io
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger


# ---------------------------------------------------------------------------
# FactorStore – persistence layer
# ---------------------------------------------------------------------------


class FactorStore:
    """SQLite-backed factor storage with versioning.

    Supports context manager protocol::

        with FactorStore(":memory:") as store:
            store.save_factor("f", data)
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def _create_tables(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS factors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version INTEGER NOT NULL,
                data_json TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
            """
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_factors_name ON factors(name)"
        )
        self.conn.commit()

    # -- public API -------------------------------------------------------

    def save_factor(
        self,
        factor_name: str,
        factor_data: pd.Series,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Persist a factor version.  Returns the new version number."""
        version = self._next_version(factor_name)
        self.conn.execute(
            """
            INSERT INTO factors (name, version, data_json, metadata, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (
                factor_name,
                version,
                factor_data.to_json(),
                json.dumps(metadata or {}),
                datetime.now().isoformat(),
            ),
        )
        self.conn.commit()
        logger.debug(f"Saved {factor_name} v{version}")
        return version

    def load_factor(
        self,
        factor_name: str,
        version: Optional[int] = None,
    ) -> pd.Series:
        """Load a factor by name (latest by default) or specific version."""
        if version is not None:
            cur = self.conn.execute(
                "SELECT data_json FROM factors "
                "WHERE name=? AND version=? AND is_active=1",
                (factor_name, version),
            )
        else:
            cur = self.conn.execute(
                "SELECT data_json FROM factors "
                "WHERE name=? AND is_active=1 "
                "ORDER BY version DESC LIMIT 1",
                (factor_name,),
            )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"Factor '{factor_name}' not found")
        return pd.read_json(io.StringIO(row[0]), typ="series")

    def get_factor_history(
        self,
        factor_name: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Return recent versions for a factor."""
        cur = self.conn.execute(
            "SELECT version, data_json, created_at FROM factors "
            "WHERE name=? AND is_active=1 "
            "ORDER BY created_at DESC LIMIT ?",
            (factor_name, limit),
        )
        history: List[Dict[str, Any]] = []
        for ver, data_json, created_at in cur.fetchall():
            history.append(
                {
                    "version": ver,
                    "data": pd.read_json(io.StringIO(data_json), typ="series"),
                    "created_at": created_at,
                }
            )
        return history

    def deactivate_factor(self, factor_name: str) -> None:
        """Mark all versions of a factor as inactive."""
        self.conn.execute(
            "UPDATE factors SET is_active=0 WHERE name=?",
            (factor_name,),
        )
        self.conn.commit()

    def log_retirement(
        self, factor_name: str, reason: str, timestamp: Optional[datetime] = None
    ) -> None:
        """Record a retirement event (metadata-only)."""
        ts = (timestamp or datetime.now()).isoformat()
        self.conn.execute(
            "INSERT INTO factors (name, version, data_json, metadata, created_at, is_active) "
            "VALUES (?, 0, ?, ?, ?, 0)",
            (factor_name, "{}", json.dumps({"retirement_reason": reason}), ts),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # -- internal ---------------------------------------------------------

    def _next_version(self, factor_name: str) -> int:
        cur = self.conn.execute(
            "SELECT MAX(version) FROM factors WHERE name=?",
            (factor_name,),
        )
        row = cur.fetchone()
        return (row[0] or 0) + 1


# ---------------------------------------------------------------------------
# FactorVersioning
# ---------------------------------------------------------------------------


class FactorVersioning:
    """Manage factor versions through the store."""

    def __init__(self, store: FactorStore):
        self.store = store

    def create_version(
        self,
        factor_name: str,
        data: pd.Series,
        description: str = "",
    ) -> int:
        metadata = {"description": description, "created_by": "system"}
        return self.store.save_factor(factor_name, data, metadata)

    def compare_versions(
        self,
        factor_name: str,
        v1: int,
        v2: int,
    ) -> Dict[str, Any]:
        data1 = self.store.load_factor(factor_name, v1)
        data2 = self.store.load_factor(factor_name, v2)
        common = data1.index.intersection(data2.index)
        if len(common) < 2:
            return {"correlation": 0.0, "mean_diff": 0.0, "std_diff": 0.0}
        d1 = data1.loc[common]
        d2 = data2.loc[common]
        return {
            "correlation": float(d1.corr(d2)),
            "mean_diff": float((d1 - d2).mean()),
            "std_diff": float((d1 - d2).std()),
        }


# ---------------------------------------------------------------------------
# FactorMonitoring
# ---------------------------------------------------------------------------


class FactorMonitoring:
    """Monitor factor health via metrics derived from stored data."""

    def __init__(self, store: FactorStore):
        self.store = store

    def monitor_factor(
        self,
        factor_name: str,
        lookback: int = 20,
    ) -> Dict[str, Any]:
        history = self.store.get_factor_history(factor_name, lookback)
        if not history:
            return {"metrics": {}, "status": "no_data"}

        latest = history[0]["data"]
        metrics: Dict[str, Any] = {
            "latest_version": history[0]["version"],
            "num_versions": len(history),
            "mean": float(latest.mean()) if not latest.empty else 0.0,
            "std": float(latest.std()) if not latest.empty else 0.0,
            "autocorr": float(latest.autocorr()) if len(latest) > 1 else 0.0,
        }

        anomalies: List[str] = []
        if abs(metrics["std"]) > 100:
            anomalies.append("high_volatility")
        if len(history) >= 2:
            v0 = history[0]["data"]
            v1 = history[1]["data"]
            common = v0.index.intersection(v1.index)
            if len(common) > 5:
                corr = float(v0.loc[common].corr(v1.loc[common]))
                if corr < 0.5:
                    anomalies.append("low_version_correlation")

        status = "warning" if anomalies else "normal"
        return {"metrics": metrics, "anomalies": anomalies, "status": status}


# ---------------------------------------------------------------------------
# FactorRetirement
# ---------------------------------------------------------------------------


class FactorRetirement:
    """Determine when to retire a factor based on monitoring signals."""

    def __init__(
        self,
        store: FactorStore,
        monitoring: FactorMonitoring,
        min_versions: int = 3,
        max_autocorr_decay: float = 0.5,
    ):
        self.store = store
        self.monitoring = monitoring
        self.min_versions = min_versions
        self.max_autocorr_decay = max_autocorr_decay

    def check_retirement(self, factor_name: str) -> bool:
        """Return True if the factor should be retired."""
        result = self.monitoring.monitor_factor(factor_name)
        metrics = result.get("metrics", {})

        num_versions = metrics.get("num_versions", 0)
        if num_versions >= self.min_versions:
            autocorr = metrics.get("autocorr", 1.0)
            if autocorr < self.max_autocorr_decay:
                return True

        if result.get("status") == "no_data":
            return True

        return False

    def retire(self, factor_name: str, reason: str = "performance_degradation") -> None:
        self.store.deactivate_factor(factor_name)
        self.store.log_retirement(factor_name, reason)
        logger.info(f"Retired factor '{factor_name}': {reason}")


# ---------------------------------------------------------------------------
# Phase 2 扩展: 因子衰减检测 / 行业中性化 / 研究报告 (子模块, 见各文件)
# ---------------------------------------------------------------------------
from .factor_decay import (  # noqa: E402
    FactorDecayDetector,
    FactorHealth,
    FactorHealthReport,
)
from .industry_neutral import IndustryNeutralizer  # noqa: E402
from .report_generator import (  # noqa: E402
    FactorReportGenerator,
    FactorResearchReport,
    FactorRanking,
)
