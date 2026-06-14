"""Risk attribution: factor-based and asset-based."""

from __future__ import annotations

from typing import Any, Dict


class RiskAttribution:
    """Attribute risk to factors or assets."""

    def factor_attribution(
        self,
        exposures: Dict[str, float],
        factor_returns: Dict[str, float],
    ) -> Dict[str, Any]:
        """Decompose total risk into factor contributions."""
        factors = set(exposures.keys()) | set(factor_returns.keys())
        contributions = {}
        total = 0.0
        for f in factors:
            contrib = exposures.get(f, 0.0) * factor_returns.get(f, 0.0)
            contributions[f] = contrib
            total += contrib
        return {"factors": contributions, "total": total}

    def brinson_attribution(
        self,
        port_weights: Dict[str, float],
        bench_weights: Dict[str, float],
        port_returns: Dict[str, float],
        bench_returns: Dict[str, float],
    ) -> Dict[str, float]:
        """Brinson model: allocation + selection + interaction effects."""
        assets = set(port_weights) | set(bench_weights)
        alloc = sel = inter = 0.0
        for a in assets:
            pw = port_weights.get(a, 0.0)
            bw = bench_weights.get(a, 0.0)
            pr = port_returns.get(a, 0.0)
            br = bench_returns.get(a, 0.0)
            alloc += (pw - bw) * br
            sel += bw * (pr - br)
            inter += (pw - bw) * (pr - br)
        return {
            "allocation": alloc,
            "selection": sel,
            "interaction": inter,
            "total_active": alloc + sel + inter,
        }
