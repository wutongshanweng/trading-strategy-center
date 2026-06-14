"""Market-regime-based position sizing."""

from __future__ import annotations


class RegimeBasedPosition:
    """Scale position size according to detected market regime."""

    REGIMES = {
        "QUIET": 1.0,
        "TRENDING": 1.2,
        "VOLATILE": 0.6,
        "CRISIS": 0.2,
    }

    def get_position_size(self, regime: str) -> float:
        """Return the position multiplier for a given regime."""
        return self.REGIMES.get(regime, 1.0)
