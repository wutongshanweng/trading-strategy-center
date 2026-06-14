"""扩展量化模型的单元测试。

覆盖:Heston(特征函数定价 vs 蒙特卡洛交叉验证)、SABR(Hagan 公式 + 校准)、
Vasicek/CIR(解析债券价格 + 参数估计回收)、HAR-RV(拟合/预测)、
组合优化(风险平价的风险贡献相等性、最小方差、HRP、逆波动率)、
风险模型(VaR/CVaR 的次序关系、EVT)。

测试以"可验证的数学性质"为断言核心,而非硬编码数值。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


# ----------------------------------------------------------------------
# Heston
# ----------------------------------------------------------------------
def test_heston_semianalytic_matches_monte_carlo():
    from quant_models.models.heston_model import (
        HestonParams, heston_price, heston_mc_price,
    )
    p = HestonParams(kappa=2.0, theta=0.04, xi=0.3, rho=-0.7, v0=0.04)
    S, K, T, r = 100.0, 100.0, 1.0, 0.02
    analytic = heston_price(S, K, T, r, p, "C")
    mc = heston_mc_price(S, K, T, r, p, "C", n_steps=100, n_paths=40000, seed=7)
    # 半解析与 MC 应接近(MC 噪声容差)
    assert abs(analytic - mc) < 0.6, f"analytic={analytic}, mc={mc}"
    assert analytic > 0


def test_heston_put_call_parity():
    from quant_models.models.heston_model import HestonParams, heston_price
    p = HestonParams(kappa=1.5, theta=0.05, xi=0.4, rho=-0.5, v0=0.05)
    S, K, T, r = 100.0, 105.0, 0.5, 0.03
    call = heston_price(S, K, T, r, p, "C")
    put = heston_price(S, K, T, r, p, "P")
    # C - P = S - K*e^{-rT}
    lhs = call - put
    rhs = S - K * np.exp(-r * T)
    assert abs(lhs - rhs) < 0.5, f"parity broken: {lhs} vs {rhs}"


def test_heston_feller_condition():
    from quant_models.models.heston_model import HestonParams
    ok = HestonParams(kappa=2.0, theta=0.04, xi=0.2, rho=-0.5, v0=0.04)
    bad = HestonParams(kappa=0.5, theta=0.04, xi=0.9, rho=-0.5, v0=0.04)
    assert ok.feller_satisfied()
    assert not bad.feller_satisfied()


# ----------------------------------------------------------------------
# SABR
# ----------------------------------------------------------------------
def test_sabr_atm_vol_positive():
    from quant_models.models.sabr_model import SABRParams, sabr_implied_vol
    p = SABRParams(alpha=0.3, beta=0.5, rho=-0.3, nu=0.4)
    vol = sabr_implied_vol(F=100.0, K=100.0, T=1.0, p=p)
    assert vol > 0 and np.isfinite(vol)


def test_sabr_calibration_recovers_smile():
    from quant_models.models.sabr_model import (
        SABRParams, sabr_implied_vol, calibrate_sabr,
    )
    F, T, beta = 100.0, 1.0, 0.5
    true_p = SABRParams(alpha=0.25, beta=beta, rho=-0.4, nu=0.5)
    strikes = np.array([80, 90, 100, 110, 120], dtype=float)
    market_vols = np.array([sabr_implied_vol(F, k, T, true_p) for k in strikes])
    fitted = calibrate_sabr(F, strikes, market_vols, T, beta=beta)
    refit_vols = np.array([sabr_implied_vol(F, k, T, fitted) for k in strikes])
    # 校准后重构的微笑应贴合原始市场报价
    assert np.max(np.abs(refit_vols - market_vols)) < 1e-3


# ----------------------------------------------------------------------
# Vasicek / CIR
# ----------------------------------------------------------------------
def test_vasicek_zcb_price_bounds():
    from quant_models.models.short_rate_models import VasicekParams, vasicek_zcb_price
    p = VasicekParams(kappa=0.5, theta=0.03, sigma=0.01, r0=0.03)
    price = vasicek_zcb_price(p, T=5.0)
    # 折现债券价格在 (0,1) 之间
    assert 0 < price < 1


def test_vasicek_parameter_estimation_recovers():
    from quant_models.models.short_rate_models import (
        VasicekParams, vasicek_simulate, estimate_vasicek,
    )
    true_p = VasicekParams(kappa=1.0, theta=0.04, sigma=0.01, r0=0.04)
    paths = vasicek_simulate(true_p, T=20.0, n_steps=20 * 252, n_paths=1, seed=42)
    rates = paths[0]
    est = estimate_vasicek(rates, dt=1 / 252)
    # 长期均值 theta 应被合理回收
    assert abs(est.theta - true_p.theta) < 0.02
    assert est.kappa > 0


def test_cir_stays_nonnegative():
    from quant_models.models.short_rate_models import CIRParams, cir_simulate
    p = CIRParams(kappa=1.0, theta=0.04, sigma=0.1, r0=0.04)
    paths = cir_simulate(p, T=5.0, n_steps=5 * 252, n_paths=200, seed=1)
    assert (paths >= 0).all(), "CIR rates must stay non-negative"


def test_cir_zcb_price_bounds():
    from quant_models.models.short_rate_models import CIRParams, cir_zcb_price
    p = CIRParams(kappa=0.5, theta=0.03, sigma=0.05, r0=0.03)
    price = cir_zcb_price(p, T=5.0)
    assert 0 < price < 1


# ----------------------------------------------------------------------
# HAR-RV
# ----------------------------------------------------------------------
@pytest.fixture
def price_df():
    rng = np.random.default_rng(123)
    n = 300
    ret = rng.normal(0.0003, 0.012, n)
    close = 100 * np.exp(np.cumsum(ret))
    idx = pd.date_range("2023-01-01", periods=n, freq="D")
    return pd.DataFrame({"close": close}, index=idx)


def test_har_rv_fit_predict(price_df):
    from quant_models.models.har_rv_model import HARRVModel
    m = HARRVModel()
    m.fit(price_df)
    preds = m.predict(price_df)
    assert len(preds) > 0
    assert (preds >= 0).all(), "annualized vol must be non-negative"
    nxt = m.forecast_next()
    assert nxt >= 0 and np.isfinite(nxt)


def test_har_rv_needs_enough_data():
    from quant_models.models.har_rv_model import HARRVModel
    tiny = pd.DataFrame({"close": [100, 101, 102]})
    with pytest.raises(ValueError):
        HARRVModel().fit(tiny)


# ----------------------------------------------------------------------
# 组合优化
# ----------------------------------------------------------------------
@pytest.fixture
def asset_returns():
    rng = np.random.default_rng(7)
    n = 500
    # 4 资产,不同波动率 + 一定相关性
    cov = np.array([
        [0.04, 0.01, 0.00, 0.005],
        [0.01, 0.09, 0.02, 0.00],
        [0.00, 0.02, 0.16, 0.01],
        [0.005, 0.00, 0.01, 0.01],
    ])
    L = np.linalg.cholesky(cov)
    z = rng.standard_normal((n, 4))
    rets = z @ L.T
    return pd.DataFrame(rets, columns=["A", "B", "C", "D"])


def test_weights_sum_to_one(asset_returns):
    from quant_models.models.portfolio_optimization import (
        inverse_vol_weights, min_variance_weights, risk_parity_weights,
        max_diversification_weights, hrp_weights,
    )
    for fn in (inverse_vol_weights, min_variance_weights,
               risk_parity_weights, max_diversification_weights, hrp_weights):
        w = fn(asset_returns)
        assert abs(w.sum() - 1.0) < 1e-6, f"{fn.__name__} weights sum={w.sum()}"
        assert (w >= -1e-9).all(), f"{fn.__name__} produced negative weight"


def test_risk_parity_equalizes_risk_contributions(asset_returns):
    from quant_models.models.portfolio_optimization import (
        risk_parity_weights, risk_contributions,
    )
    w = risk_parity_weights(asset_returns)
    rc = risk_contributions(w, asset_returns)
    # 风险贡献应近似相等(各占 1/n)
    assert rc.std() < 0.03, f"risk contributions not equalized: {rc.to_dict()}"


def test_min_variance_has_lower_variance(asset_returns):
    from quant_models.models.portfolio_optimization import (
        min_variance_weights, inverse_vol_weights,
    )
    cov = asset_returns.cov().values
    w_mv = min_variance_weights(asset_returns).values
    w_iv = inverse_vol_weights(asset_returns).values
    var_mv = w_mv @ cov @ w_mv
    var_iv = w_iv @ cov @ w_iv
    # 最小方差组合方差应 <= 逆波动率组合
    assert var_mv <= var_iv + 1e-9


def test_inverse_vol_favors_low_vol_asset(asset_returns):
    from quant_models.models.portfolio_optimization import inverse_vol_weights
    w = inverse_vol_weights(asset_returns)
    # D 波动率最低 -> 权重应最高
    assert w["D"] == w.max()


# ----------------------------------------------------------------------
# 风险模型
# ----------------------------------------------------------------------
@pytest.fixture
def loss_returns():
    rng = np.random.default_rng(99)
    return pd.Series(rng.standard_t(5, 2000) * 0.01)


def test_var_cvar_ordering(loss_returns):
    from quant_models.models.risk_models import historical_var, historical_cvar
    var95 = historical_var(loss_returns, 0.95)
    cvar95 = historical_cvar(loss_returns, 0.95)
    # CVaR(尾部均值损失)应不小于 VaR
    assert cvar95 >= var95 > 0


def test_var_increases_with_confidence(loss_returns):
    from quant_models.models.risk_models import historical_var
    var95 = historical_var(loss_returns, 0.95)
    var99 = historical_var(loss_returns, 0.99)
    assert var99 >= var95


def test_parametric_var_positive(loss_returns):
    from quant_models.models.risk_models import parametric_var
    v = parametric_var(loss_returns, 0.95)
    assert v > 0 and np.isfinite(v)
