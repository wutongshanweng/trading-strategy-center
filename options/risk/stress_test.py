"""期权组合情景压力测试。

对应《架构升级建议》风险层缺口:隔夜跳空压力测试(涨跌停 + IV +30% 联合)。
对一组期权腿在 (价格冲击 × IV 冲击) 网格上重估组合价值,输出 PnL 矩阵。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from options.pricing.black_scholes import bsm_price
from options.pricing.black76 import black76_price


@dataclass
class StressLeg:
    """压力测试中的一条腿。

    qty 带符号(买正卖负);entry_price 为开仓权利金(用于 PnL 基准)。
    """

    K: float
    T: float
    qty: float
    option_type: str = "C"      # 'C' / 'P'
    sigma: float = 0.2
    entry_price: Optional[float] = None
    multiplier: float = 1.0


@dataclass
class StressScenario:
    price_shock: float          # 标的相对变动,如 -0.10 表示跌 10%
    iv_shock: float             # IV 绝对加点 or 相对?这里用相对乘子,如 +0.30 表示 IV*1.30
    pnl: float


@dataclass
class StressResult:
    base_value: float
    scenarios: List[StressScenario] = field(default_factory=list)

    def worst(self) -> Optional[StressScenario]:
        if not self.scenarios:
            return None
        return min(self.scenarios, key=lambda s: s.pnl)

    def as_matrix(self) -> dict:
        return {
            f"px{ s.price_shock:+.0%}_iv{ s.iv_shock:+.0%}": round(s.pnl, 2)
            for s in self.scenarios
        }


def _price_leg(leg: StressLeg, spot: float, r: float,
               sigma: float, futures: bool, q: float) -> float:
    if futures:
        return black76_price(spot, leg.K, leg.T, r, sigma, leg.option_type)
    return bsm_price(spot, leg.K, leg.T, r, sigma, q, leg.option_type)


def portfolio_value(legs: List[StressLeg], spot: float, r: float,
                    futures: bool = False, q: float = 0.0,
                    sigma_mult: float = 1.0, spot_mult: float = 1.0) -> float:
    """重估组合在给定价格/IV 冲击下的总价值(带符号 qty 加权)。"""
    total = 0.0
    shocked_spot = spot * spot_mult
    for leg in legs:
        sigma = max(leg.sigma * sigma_mult, 1e-6)
        px = _price_leg(leg, shocked_spot, r, sigma, futures, q)
        total += px * leg.qty * leg.multiplier
    return total


def stress_test(
    legs: List[StressLeg], spot: float, r: float,
    price_shocks: Optional[List[float]] = None,
    iv_shocks: Optional[List[float]] = None,
    futures: bool = False, q: float = 0.0,
) -> StressResult:
    """在 (价格冲击 × IV 冲击) 网格上做压力测试。

    price_shocks: 相对变动列表,默认 [-0.10, -0.05, 0, +0.05, +0.10](模拟涨跌停区间)
    iv_shocks:    IV 相对乘子-1 列表,默认 [-0.30, 0, +0.30]
    PnL 相对当前 (spot, 原 IV) 的组合价值。
    """
    if price_shocks is None:
        price_shocks = [-0.10, -0.05, 0.0, 0.05, 0.10]
    if iv_shocks is None:
        iv_shocks = [-0.30, 0.0, 0.30]

    base = portfolio_value(legs, spot, r, futures, q, 1.0, 1.0)
    scenarios: List[StressScenario] = []
    for ps in price_shocks:
        for ivs in iv_shocks:
            val = portfolio_value(
                legs, spot, r, futures, q,
                sigma_mult=1.0 + ivs, spot_mult=1.0 + ps,
            )
            scenarios.append(StressScenario(ps, ivs, val - base))
    return StressResult(base_value=base, scenarios=scenarios)
