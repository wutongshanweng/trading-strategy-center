"""Kelly criterion for optimal position sizing."""

from __future__ import annotations


class KellyCriterion:
    """Calculate optimal bet size using Kelly formula."""

    def __init__(self, risk_free: float = 0.02):
        self.risk_free = risk_free

    def calculate(self, win_rate: float, win_loss_ratio: float) -> float:
        """Full Kelly fraction: f* = (p*b - q) / b."""
        q = 1 - win_rate
        b = win_loss_ratio
        if b <= 0:
            return 0.0
        f = (win_rate * b - q) / b
        return max(0.0, min(f, 0.5))

    def fractional(
        self, win_rate: float, win_loss_ratio: float, fraction: float = 0.5
    ) -> float:
        """Fractional Kelly (conservative)."""
        return self.calculate(win_rate, win_loss_ratio) * fraction
