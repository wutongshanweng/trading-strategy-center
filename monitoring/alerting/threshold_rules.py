"""Threshold-based alert rules engine."""

from __future__ import annotations

from typing import Any, Dict, List


class ThresholdRules:
    """Evaluate metric values against configurable thresholds."""

    def __init__(self):
        self.rules: List[Dict[str, Any]] = []

    def add_rule(
        self,
        name: str,
        metric: str,
        threshold: float,
        direction: str = "above",
        severity: str = "warning",
    ) -> None:
        self.rules.append({
            "name": name,
            "metric": metric,
            "threshold": threshold,
            "direction": direction,
            "severity": severity,
        })

    def evaluate(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        for r in self.rules:
            v = metrics.get(r["metric"])
            if v is None:
                continue
            triggered = (
                (r["direction"] == "above" and v > r["threshold"])
                or (r["direction"] == "below" and v < r["threshold"])
            )
            if triggered:
                alerts.append({
                    "rule": r["name"],
                    "metric": r["metric"],
                    "value": v,
                    "threshold": r["threshold"],
                    "severity": r["severity"],
                })
        return alerts
