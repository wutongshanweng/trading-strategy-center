"""Return attribution: Brinson model."""

from __future__ import annotations

from typing import Dict


class ReturnAttribution:
    """Brinson-style allocation / selection / interaction attribution."""

    def brinson(
        self,
        port_weights: Dict[str, float],
        bench_weights: Dict[str, float],
        port_returns: Dict[str, float],
        bench_returns: Dict[str, float],
    ) -> Dict[str, float]:
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
