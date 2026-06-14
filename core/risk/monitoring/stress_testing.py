"""Portfolio stress testing."""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


class StressTesting:
    """Run hypothetical and historical stress scenarios on a portfolio."""

    def __init__(self, portfolio: Dict[str, Any]):
        """
        Args:
            portfolio: dict mapping symbol -> {"value": float, "beta": float, ...}
        """
        self.portfolio = portfolio

    def hypothetical_scenarios(self) -> List[Dict[str, Any]]:
        """Return a list of hypothetical stress scenarios."""
        return [
            {"name": "Market Drop 10%", "shock": -0.10, "impact": self._impact(-0.10)},
            {"name": "Market Drop 20%", "shock": -0.20, "impact": self._impact(-0.20)},
            {"name": "Market Drop 30%", "shock": -0.30, "impact": self._impact(-0.30)},
            {"name": "Volatility 2x", "vol_mult": 2.0},
            {"name": "Rate Rise 200bp", "rate_shock": 0.02},
            {"name": "Liquidity Crisis", "shock": -0.15, "impact": self._impact(-0.15)},
        ]

    def _impact(self, shock: float) -> float:
        """Estimate portfolio impact from a market-wide shock."""
        total = sum(p["value"] for p in self.portfolio.values())
        if total == 0:
            return 0.0
        return sum(
            p["value"] * shock * p.get("beta", 1.0)
            for p in self.portfolio.values()
        ) / total

    def reverse_stress_test(self, loss_threshold: float) -> List[Dict[str, Any]]:
        """Find ALL scenarios that would cause a loss >= threshold.

        Scans market decline scenarios from 5% to 50% and collects every
        scenario whose absolute impact exceeds the threshold.
        """
        scenarios = []
        for decline in np.arange(0.05, 0.55, 0.05):
            impact = self._impact(-decline)
            if abs(impact) >= loss_threshold:
                scenarios.append({
                    "name": f"Market Drop {decline*100:.0f}%",
                    "decline": float(decline),
                    "impact": float(impact),
                })
        return scenarios
