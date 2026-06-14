"""SQLite-backed time-series storage for metrics."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional


class TimeSeriesDB:
    """Lightweight time-series store using SQLite.

    Supports context manager protocol::

        with TimeSeriesDB("metrics.db") as db:
            db.insert("cpu", 85.2)
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._closed = False
        self._create_tables()

    def _create_tables(self) -> None:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS metrics "
            "(ts TEXT, name TEXT, value REAL, tags TEXT)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_m_name ON metrics(name)"
        )
        self.conn.commit()

    def insert(self, name: str, value: float, tags: Optional[Dict] = None) -> None:
        self.conn.execute(
            "INSERT INTO metrics VALUES (?,?,?,?)",
            (datetime.now().isoformat(), name, value,
             json.dumps(tags) if tags else None),
        )
        self.conn.commit()

    def query(self, name: str, limit: int = 100) -> List[Dict[str, Any]]:
        cur = self.conn.execute(
            "SELECT ts,value,tags FROM metrics WHERE name=? "
            "ORDER BY ts DESC LIMIT ?",
            (name, limit),
        )
        return [
            {"timestamp": r[0], "value": r[1],
             "tags": json.loads(r[2]) if r[2] else None}
            for r in cur.fetchall()
        ]

    def close(self) -> None:
        if not self._closed:
            self.conn.close()
            self._closed = True

    def __enter__(self) -> "TimeSeriesDB":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
