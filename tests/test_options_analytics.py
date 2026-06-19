"""compute_option_greeks 单测 — 合成输入, 不触网/不触库。"""

import math

from options.pricing.black76 import black76_price
from options.pricing.black_scholes import bsm_price
from data_center.options_analytics import compute_option_greeks


def test_recovers_iv_for_futures_option():
    """先用已知 IV 算理论价, 再反解应还原该 IV。"""
    F, K, T, r, true_iv = 2800.0, 2700.0, 0.25, 0.02, 0.22
    price = black76_price(F, K, T, r, true_iv, "C")
    res = compute_option_greeks(price, F, K, T, "call", r, is_futures=True)
    assert res is not None
    assert abs(res["iv"] - true_iv) < 1e-3


def test_recovers_iv_for_etf_option():
    S, K, T, r, true_iv = 3.0, 2.9, 0.5, 0.02, 0.18
    price = bsm_price(S, K, T, r, true_iv, 0.0, "C")
    res = compute_option_greeks(price, S, K, T, "C", r, is_futures=False)
    assert res is not None
    assert abs(res["iv"] - true_iv) < 1e-3


def test_call_delta_sign_and_range():
    F, K, T, r = 2800.0, 2700.0, 0.25, 0.02
    price = black76_price(F, K, T, r, 0.22, "C")
    res = compute_option_greeks(price, F, K, T, "call", r)
    assert 0.0 <= res["delta"] <= 1.0
    assert res["gamma"] >= 0.0
    assert res["vega"] >= 0.0


def test_put_delta_negative():
    F, K, T, r = 2700.0, 2800.0, 0.25, 0.02
    price = black76_price(F, K, T, r, 0.25, "P")
    res = compute_option_greeks(price, F, K, T, "P", r)
    assert -1.0 <= res["delta"] <= 0.0


def test_itm_call_has_intrinsic_value():
    """实值看涨: 内在价值 > 0, 时间价值 = 权利金 - 内在价值。"""
    F, K, T, r = 3000.0, 2700.0, 0.25, 0.02
    price = black76_price(F, K, T, r, 0.2, "C")
    res = compute_option_greeks(price, F, K, T, "call", r)
    assert res["intrinsic_value"] > 0
    assert abs(res["time_value"] - (price - res["intrinsic_value"])) < 1e-2


def test_invalid_inputs_return_none():
    assert compute_option_greeks(0.0, 2800, 2700, 0.25, "C") is None
    assert compute_option_greeks(50, 2800, 2700, 0.0, "C") is None
    assert compute_option_greeks(50, -1, 2700, 0.25, "C") is None
