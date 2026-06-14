"""Alert lifecycle manager."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List


class AlertManager:
    """Create, acknowledge, resolve, and query alerts."""

    def __init__(self):
        self._active: Dict[str, Dict] = {}
        self._history: List[Dict] = []

    def create_alert(
        self, rule: str, metric: str, value: float,
        threshold: float, severity: str,
    ) -> Dict[str, Any]:
        alert_id = str(uuid.uuid4())[:8]
        alert = {
            "id": alert_id,
            "rule": rule,
            "metric": metric,
            "value": value,
            "threshold": threshold,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "status": "active",
        }
        self._active[alert_id] = alert
        self._history.append(alert)
        return alert

    def resolve(self, alert_id: str) -> bool:
        if alert_id in self._active:
            self._active[alert_id]["status"] = "resolved"
            self._active[alert_id]["resolved_at"] = datetime.now().isoformat()
            del self._active[alert_id]
            return True
        return False

    def get_active(self) -> List[Dict]:
        return list(self._active.values())

    def get_history(self) -> List[Dict]:
        return list(self._history)
