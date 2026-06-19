"""
期权希腊值/IV 计算 — 用于 akshare 不直接提供 Greeks 的合约 (主要是商品期权)。

商品期权标的是期货, 用 Black76 (futures=True):
- 用期权市场价反解隐含波动率 (IV)
- 用该 IV 算 Delta/Gamma/Vega/Theta/Rho + 理论价/内在价值/时间价值

纯函数, 不触库不触网, 便于单测。编排 (取标的期货价/到期日) 由采集器负责。
"""

from __future__ import annotations

import math
from typing import Optional

from options.greeks.analytical_greeks import black76_greeks, bsm_greeks
from options.volatility.iv_solver import implied_vol_newton

# 中国无风险利率近似 (年化), 用于贴现/IV 求解
DEFAULT_RISK_FREE = 0.02


def compute_option_greeks(
    market_price: float, underlying: float, strike: float, t_years: float,
    option_type: str, r: float = DEFAULT_RISK_FREE, is_futures: bool = True,
) -> Optional[dict]:
    """从期权市场价反解 IV 并算全套希腊值。

    market_price: 期权当日收盘价 (权利金)
    underlying:   标的价 (商品期权=标的期货价 F; ETF/股票期权=现货 S)
    strike:       行权价 K
    t_years:      到期时间 (年), 必须 > 0
    option_type:  'call'/'put' 或 'C'/'P'
    is_futures:   True 用 Black76 (商品/股指期权), False 用 BSM (ETF/股票期权)

    返回 dict(iv, delta, gamma, vega, theta, rho, theoretical_price,
    intrinsic_value, time_value); 无法定价 (价外无时间价值/数据非法) 时返回 None。
    """
    cp = "C" if str(option_type).upper().startswith("C") else "P"
    if not (market_price > 0 and underlying > 0 and strike > 0 and t_years > 0):
        return None

    iv = implied_vol_newton(
        market_price, underlying, strike, t_years, r,
        option_type=cp, futures=is_futures,
    )
    if iv is None or math.isnan(iv) or iv <= 0:
        return None

    g = (black76_greeks(underlying, strike, t_years, r, iv, cp) if is_futures
         else bsm_greeks(underlying, strike, t_years, r, iv, 0.0, cp))

    intrinsic = max(underlying - strike, 0.0) if cp == "C" else max(strike - underlying, 0.0)
    if is_futures:
        intrinsic *= math.exp(-r * t_years)  # 期货期权内在价值贴现
    time_value = market_price - intrinsic

    return {
        "iv": round(iv, 4),
        "delta": round(g.delta, 4),
        "gamma": round(g.gamma, 6),
        "vega": round(g.vega_pct, 4),       # 每 1% vol 影响, 与表注释一致
        "theta": round(g.theta_daily, 4),   # 每日时间衰减
        "rho": round(g.rho / 100.0, 4),     # 每 1% 利率影响
        "theoretical_price": round(market_price, 4),  # 反解 IV => 理论价≈市场价
        "intrinsic_value": round(intrinsic, 4),
        "time_value": round(time_value, 4),
    }
