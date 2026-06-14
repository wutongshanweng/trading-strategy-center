"""Performance report generation."""

from __future__ import annotations

from typing import Any, Dict


class PerformanceReport:
    """Generate daily and weekly performance reports."""

    def daily(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "date": data.get("date"),
            "summary": {
                "pnl": data.get("pnl", 0),
                "sharpe": data.get("sharpe", 0),
                "max_drawdown": data.get("max_drawdown", 0),
            },
            "positions": data.get("positions", []),
        }

    def weekly(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "period": data.get("period"),
            "performance": {
                "total_return": data.get("total_return", 0),
                "sharpe": data.get("sharpe", 0),
            },
            "risk": {
                "max_drawdown": data.get("max_drawdown", 0),
                "var_95": data.get("var_95", 0),
            },
        }
