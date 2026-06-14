"""期权层单元测试 — 定价 / Greeks / 波动率 / 策略 / 风险 / 分析。

覆盖 P0 期权能力,验证数值正确性与可导入性。
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest


# ---------- 定价 ----------
def test_bsm_call_put_parity():
    """看涨-看跌平价: C - P = S*e^{-qT} - K*e^{-rT}。"""
    from options.pricing.black_scholes import bsm_price

    S, K, T, r, sigma, q = 100.0, 100.0, 0.5, 0.03, 0.25, 0.0
    c = bsm_price(S, K, T, r, sigma, q, "C")
    p = bsm_price(S, K, T, r, sigma, q, "P")
    lhs = c - p
    rhs = S * math.exp(-q * T) - K * math.exp(-r * T)
    assert lhs == pytest.approx(rhs, abs=1e-6)


def test_bsm_intrinsic_at_expiry():
    """到期时退化为内在价值。"""
    from options.pricing.black_scholes import bsm_price

    assert bsm_price(110, 100, 0.0, 0.03, 0.2, 0.0, "C") == pytest.approx(10.0)
    assert bsm_price(90, 100, 0.0, 0.03, 0.2, 0.0, "P") == pytest.approx(10.0)


def test_bsm_vectorized_matches_scalar():
    from options.pricing.black_scholes import bsm_price, bsm_price_vec

    S, T, r, sigma = 100.0, 0.5, 0.03, 0.25
    strikes = np.array([90.0, 100.0, 110.0])
    vec = bsm_price_vec(S, strikes, T, r, sigma, 0.0, "C")
    for i, k in enumerate(strikes):
        assert vec[i] == pytest.approx(bsm_price(S, float(k), T, r, sigma, 0.0, "C"), abs=1e-9)


def test_black76_parity():
    """Black76 平价: C - P = e^{-rT}(F - K)。"""
    from options.pricing.black76 import black76_price

    F, K, T, r, sigma = 100.0, 100.0, 0.5, 0.03, 0.25
    c = black76_price(F, K, T, r, sigma, "C")
    p = black76_price(F, K, T, r, sigma, "P")
    assert c - p == pytest.approx(math.exp(-r * T) * (F - K), abs=1e-6)


def test_binomial_converges_to_bsm():
    """二叉树(欧式)随步数收敛到 BSM。"""
    from options.pricing.binomial_tree import crr_price
    from options.pricing.black_scholes import bsm_price

    S, K, T, r, sigma = 100.0, 105.0, 1.0, 0.03, 0.2
    tree = crr_price(S, K, T, r, sigma, n_steps=500, option_type="C", american=False)
    bsm = bsm_price(S, K, T, r, sigma, 0.0, "C")
    assert tree == pytest.approx(bsm, abs=0.05)


def test_american_put_ge_european():
    """美式看跌 >= 欧式看跌(提前行权权利有价值)。"""
    from options.pricing.binomial_tree import crr_price

    S, K, T, r, sigma = 100.0, 110.0, 1.0, 0.05, 0.3
    eu = crr_price(S, K, T, r, sigma, n_steps=300, option_type="P", american=False)
    am = crr_price(S, K, T, r, sigma, n_steps=300, option_type="P", american=True)
    assert am >= eu - 1e-9


# ---------- Greeks ----------
def test_bsm_greeks_signs():
    """基本符号: call delta>0, put delta<0, gamma>0, vega>0。"""
    from options.greeks.analytical_greeks import bsm_greeks

    cg = bsm_greeks(100, 100, 0.5, 0.03, 0.25, 0.0, "C")
    pg = bsm_greeks(100, 100, 0.5, 0.03, 0.25, 0.0, "P")
    assert 0 < cg.delta < 1
    assert -1 < pg.delta < 0
    assert cg.gamma > 0 and pg.gamma > 0
    assert cg.vega > 0 and pg.vega > 0
    # call/put delta 关系: delta_C - delta_P = e^{-qT}
    assert cg.delta - pg.delta == pytest.approx(1.0, abs=1e-6)


def test_numerical_greeks_match_analytical():
    from options.greeks.analytical_greeks import bsm_greeks
    from options.greeks.numerical_greeks import numerical_delta, numerical_vega

    S, K, T, r, sigma = 100.0, 100.0, 0.5, 0.03, 0.25
    ana = bsm_greeks(S, K, T, r, sigma, 0.0, "C")
    nd = numerical_delta(S, K, T, r, sigma, q=0.0, option_type="C")
    nv = numerical_vega(S, K, T, r, sigma, q=0.0, option_type="C")
    assert nd == pytest.approx(ana.delta, abs=1e-3)
    # vega:解析是对 1.0 vol,数值差分默认也应一致(允许量纲一致性误差)
    assert nv == pytest.approx(ana.vega, rel=0.05)


def test_portfolio_greeks_aggregation():
    """多腿组合 Greeks 加权汇总。"""
    from options.greeks.portfolio_greeks import aggregate_option_legs

    legs = [
        {"symbol": "X", "K": 100, "T": 0.5, "qty": 1, "option_type": "C"},
        {"symbol": "X", "K": 100, "T": 0.5, "qty": -1, "option_type": "P"},
    ]
    pg = aggregate_option_legs(legs, spot=100, r=0.03, sigma=0.25, multiplier=1.0)
    # long call + short put = 合成多头, delta 应接近 +1
    assert pg.delta == pytest.approx(1.0, abs=0.05)


# ---------- 波动率 ----------
def test_implied_vol_roundtrip():
    """用已知 sigma 定价再反求,应还原 sigma。"""
    from options.pricing.black_scholes import bsm_price
    from options.volatility.iv_solver import implied_vol_newton

    S, K, T, r, true_sigma = 100.0, 100.0, 0.5, 0.03, 0.27
    price = bsm_price(S, K, T, r, true_sigma, 0.0, "C")
    iv = implied_vol_newton(price, S, K, T, r, q=0.0, option_type="C")
    assert iv == pytest.approx(true_sigma, abs=1e-4)


def test_realized_vol_positive():
    from options.volatility.realized_vol import close_to_close, parkinson

    np.random.seed(0)
    n = 100
    close = pd.Series(100 * np.exp(np.cumsum(np.random.normal(0, 0.01, n))))
    high = close * 1.01
    low = close * 0.99
    ctc = close_to_close(close, n=20)
    park = parkinson(high, low, n=20)
    assert ctc.dropna().iloc[-1] > 0
    assert park.dropna().iloc[-1] > 0


def test_svi_fit_recovers_smile():
    """SVI 拟合一个合成微笑后,重估误差应很小。"""
    from options.volatility.svi_surface import fit_svi_slice, svi_total_variance

    k = np.linspace(-0.3, 0.3, 21)
    true = dict(a=0.04, b=0.4, rho=-0.3, m=0.0, sigma=0.1)
    w_true = svi_total_variance(k, **true)
    params = fit_svi_slice(k, w_true)
    w_fit = svi_total_variance(k, *params)
    assert np.max(np.abs(w_fit - w_true)) < 1e-3


def test_iv_rank_bounds():
    from options.volatility.iv_rank import iv_rank, iv_percentile

    s = pd.Series(np.linspace(0.1, 0.5, 252))
    assert iv_rank(s) == pytest.approx(100.0, abs=1e-6)  # 当前在最高位
    assert 0 <= iv_percentile(s) <= 100


# ---------- 策略 ----------
def test_strategies_registered():
    """导入策略包后注册表应包含 P0 策略。"""
    import options.strategies  # noqa: F401  触发注册
    from options.registry import list_strategies

    names = set(list_strategies())
    expected = {
        "long_call", "long_put", "covered_call", "protective_put",
        "short_straddle", "short_strangle", "iron_condor", "iron_butterfly",
        "long_straddle", "long_strangle", "calendar_spread",
    }
    assert expected.issubset(names), f"缺失: {expected - names}"


def test_iron_condor_risk_profile():
    """铁鹰最大盈利=净权利金、最大亏损有限且为正。"""
    import options.strategies  # noqa: F401
    from options.registry import get_strategy

    cls = get_strategy("iron_condor")
    strat = cls()
    expiry = datetime.utcnow() + timedelta(days=30)
    sig = strat.build(
        underlying="IF", spot=4000, expiry=expiry,
        short_put_prem=40, long_put_prem=20,
        short_call_prem=40, long_call_prem=20,
        quantity=1,
    )
    assert sig.expected_max_profit == pytest.approx(40.0)  # (40+40)-(20+20)
    assert sig.expected_max_loss > 0
    assert len(sig.legs) == 4
    assert len(sig.breakeven_points) == 2


def test_long_straddle_breakevens():
    import options.strategies  # noqa: F401
    from options.registry import get_strategy

    strat = get_strategy("long_straddle")()
    expiry = datetime.utcnow() + timedelta(days=30)
    sig = strat.build(underlying="X", spot=100, expiry=expiry,
                      call_premium=3, put_premium=3, strike=100)
    assert sig.expected_max_loss == pytest.approx(6.0)
    assert sorted(sig.breakeven_points) == pytest.approx([94.0, 106.0])


def test_covered_call_structure():
    import options.strategies  # noqa: F401
    from options.registry import get_strategy

    strat = get_strategy("covered_call")()
    expiry = datetime.utcnow() + timedelta(days=30)
    sig = strat.build(underlying="X", spot=100, expiry=expiry,
                      premium=2, strike=103, entry_price=100)
    assert len(sig.legs) == 1
    assert len(sig.futures_legs) == 1
    assert sig.expected_max_profit == pytest.approx(5.0)  # 103-100+2


# ---------- 风险 ----------
def test_greeks_limits_breach():
    from options.greeks.portfolio_greeks import PortfolioGreeks, PositionGreeks
    from options.greeks.analytical_greeks import Greeks
    from options.risk.greeks_limits import GreeksLimits, check_greeks_limits

    pg = PortfolioGreeks()
    pg.add(PositionGreeks("X", qty=10, multiplier=1.0,
                          greeks=Greeks(0.6, 0.02, 5.0, -1.0, 0.0)))
    # delta=6, 中性带 ±2 -> 违规
    limits = GreeksLimits(delta_band=2.0, gamma_max=1.0, vega_max=100.0)
    res = check_greeks_limits(pg, limits)
    assert not res.ok
    assert any(b.metric == "delta" for b in res.breaches)


def test_stress_test_matrix():
    from options.risk.stress_test import StressLeg, stress_test

    legs = [
        StressLeg(K=100, T=0.25, qty=-1, option_type="C", sigma=0.2),
        StressLeg(K=100, T=0.25, qty=-1, option_type="P", sigma=0.2),
    ]
    res = stress_test(legs, spot=100, r=0.03)
    # 卖跨式:IV 上升 + 大幅价格变动应产生亏损(PnL<0)
    worst = res.worst()
    assert worst is not None
    assert worst.pnl < 0
    assert len(res.scenarios) == 15  # 5 价格 × 3 IV


# ---------- 分析 ----------
def test_pcr_and_max_pain():
    from options.analysis import OptionChainRow, put_call_ratio, max_pain

    rows = [
        OptionChainRow(strike=95, call_oi=100, put_oi=300),
        OptionChainRow(strike=100, call_oi=200, put_oi=200),
        OptionChainRow(strike=105, call_oi=300, put_oi=100),
    ]
    pcr = put_call_ratio(rows, by="oi")
    assert pcr == pytest.approx(600 / 600)  # puts=600 calls=600
    mp = max_pain(rows)
    assert mp in (95.0, 100.0, 105.0)
