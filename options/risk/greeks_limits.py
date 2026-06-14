"""组合 Greeks 风险限额检查。

对应《架构升级建议》风险层缺口:Delta 中性带、Gamma/Vega 上限。
输入组合级 Greeks(已乘 qty*multiplier),输出违规清单。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from options.greeks.portfolio_greeks import PortfolioGreeks


@dataclass
class GreeksLimits:
    """组合 Greeks 限额配置。

    None 表示该项不限制。delta_band 为中性带半宽([-band, +band] 视为合规)。
    """

    delta_band: Optional[float] = None      # |delta| 上限(中性带)
    gamma_max: Optional[float] = None       # |gamma| 上限
    vega_max: Optional[float] = None        # |vega| 上限
    theta_min: Optional[float] = None       # theta 下限(通常为负,防止过度负 theta)


@dataclass
class LimitBreach:
    metric: str
    value: float
    limit: float
    message: str


@dataclass
class GreeksCheckResult:
    ok: bool
    breaches: List[LimitBreach] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "breaches": [
                {"metric": b.metric, "value": b.value, "limit": b.limit, "message": b.message}
                for b in self.breaches
            ],
        }


def check_greeks_limits(pg: PortfolioGreeks, limits: GreeksLimits) -> GreeksCheckResult:
    """检查组合 Greeks 是否在限额内,返回违规列表。"""
    breaches: List[LimitBreach] = []

    if limits.delta_band is not None and abs(pg.delta) > limits.delta_band:
        breaches.append(LimitBreach(
            "delta", pg.delta, limits.delta_band,
            f"Delta {pg.delta:.2f} 超出中性带 ±{limits.delta_band:.2f}",
        ))

    if limits.gamma_max is not None and abs(pg.gamma) > limits.gamma_max:
        breaches.append(LimitBreach(
            "gamma", pg.gamma, limits.gamma_max,
            f"Gamma {pg.gamma:.4f} 超出上限 {limits.gamma_max:.4f}",
        ))

    if limits.vega_max is not None and abs(pg.vega) > limits.vega_max:
        breaches.append(LimitBreach(
            "vega", pg.vega, limits.vega_max,
            f"Vega {pg.vega:.2f} 超出上限 {limits.vega_max:.2f}",
        ))

    if limits.theta_min is not None and pg.theta < limits.theta_min:
        breaches.append(LimitBreach(
            "theta", pg.theta, limits.theta_min,
            f"Theta {pg.theta:.2f} 低于下限 {limits.theta_min:.2f}",
        ))

    return GreeksCheckResult(ok=len(breaches) == 0, breaches=breaches)
