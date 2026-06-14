"""组合级希腊字母聚合 — 把多腿期权/期货持仓的 Greeks 加权汇总。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .analytical_greeks import Greeks, bsm_greeks, black76_greeks


@dataclass
class PositionGreeks:
    """单个持仓的 Greeks 及其名义信息。"""

    symbol: str
    qty: float                 # 带符号张数(买正卖负)
    multiplier: float          # 合约乘数
    greeks: Greeks


@dataclass
class PortfolioGreeks:
    """组合级 Greeks 汇总(已乘 qty * multiplier)。"""

    delta: float = 0.0
    gamma: float = 0.0
    vega: float = 0.0
    theta: float = 0.0
    rho: float = 0.0
    positions: List[PositionGreeks] = field(default_factory=list)

    def add(self, pos: PositionGreeks) -> None:
        w = pos.qty * pos.multiplier
        self.delta += pos.greeks.delta * w
        self.gamma += pos.greeks.gamma * w
        self.vega += pos.greeks.vega * w
        self.theta += pos.greeks.theta * w
        self.rho += pos.greeks.rho * w
        self.positions.append(pos)

    def as_dict(self) -> dict:
        return {
            "delta": self.delta,
            "gamma": self.gamma,
            "vega": self.vega,
            "theta": self.theta,
            "rho": self.rho,
        }


def aggregate_option_legs(
    legs: List[dict], spot: float, r: float, sigma: float,
    multiplier: float = 1.0, futures: bool = False, q: float = 0.0,
) -> PortfolioGreeks:
    """对一组期权腿计算组合 Greeks。

    每条 leg 形如:
        {"symbol", "K", "T", "qty"(带符号), "option_type"("C"/"P"),
         "sigma"(可选,覆盖默认), "multiplier"(可选)}
    """
    pg = PortfolioGreeks()
    for leg in legs:
        K = leg["K"]
        T = leg["T"]
        ot = leg.get("option_type", "C")
        leg_sigma = leg.get("sigma", sigma)
        mult = leg.get("multiplier", multiplier)
        g = (black76_greeks(spot, K, T, r, leg_sigma, ot) if futures
             else bsm_greeks(spot, K, T, r, leg_sigma, q, ot))
        pg.add(PositionGreeks(leg.get("symbol", ""), leg["qty"], mult, g))
    return pg


def add_futures_leg(pg: PortfolioGreeks, symbol: str, qty: float,
                    multiplier: float = 1.0) -> PortfolioGreeks:
    """把期货腿并入组合(期货 delta=1,其余为 0)。"""
    pg.add(PositionGreeks(symbol, qty, multiplier, Greeks(1.0, 0.0, 0.0, 0.0, 0.0)))
    return pg
