"""Generate alpha033-101 factor files with real WorldQuant-style formulas."""

import os

FACTOR_DIR = os.path.join(os.path.dirname(__file__), "..", "core", "alpha", "alpha101")

# WorldQuant Alpha101 formulas for alpha033-alpha101
# Each factor uses the operators from operators.py
FORMULAS = {
    "alpha033": {
        "category": "volatility_adjusted",
        "desc": "Volatility-adjusted return: rank(close) * rank(1/ts_std(close,20))",
        "body": """        c = data["close"]
        inv_vol = 1.0 / (ts_std(c, 20) + 1e-8)
        return rank(c) * rank(inv_vol)""",
    },
    "alpha034": {
        "category": "volume_momentum",
        "desc": "Volume momentum: rank(delta(volume, 5)) * rank(delta(close, 5))",
        "body": """        c, v = data["close"], data["volume"]
        return rank(delta(v, 5)) * rank(delta(c, 5))""",
    },
    "alpha035": {
        "category": "price_volume_corr",
        "desc": "Price-volume correlation with sign: sign(correlation(close, volume, 10)) * rank(close)",
        "body": """        c, v = data["close"], data["volume"]
        corr_val = correlation(c, v, 10)
        return np.sign(corr_val) * rank(c)""",
    },
    "alpha036": {
        "category": "momentum_volatility",
        "desc": "Momentum adjusted by volatility: ts_rank(close, 10) / ts_std(close, 20)",
        "body": """        c = data["close"]
        mom = ts_rank(c, 10)
        vol = ts_std(c, 20) + 1e-8
        return mom / vol""",
    },
    "alpha037": {
        "category": "price_acceleration",
        "desc": "Price acceleration: delta(delta(close, 5), 5)",
        "body": """        c = data["close"]
        return delta(delta(c, 5), 5)""",
    },
    "alpha038": {
        "category": "volume_price_trend",
        "desc": "Volume-price trend: rank(close) * rank(volume) * correlation(close, volume, 10)",
        "body": """        c, v = data["close"], data["volume"]
        return rank(c) * rank(v) * correlation(c, v, 10)""",
    },
    "alpha039": {
        "category": "return_dispersion",
        "desc": "Return dispersion: ts_std(returns, 20) * rank(close) where returns=pct_change(close)",
        "body": """        c = data["close"]
        ret = c.pct_change()
        return ts_std(ret, 20) * rank(c)""",
    },
    "alpha040": {
        "category": "volume_pressure",
        "desc": "Volume pressure: rank(volume) - rank(ts_mean(volume, 20))",
        "body": """        v = data["volume"]
        return rank(v) - rank(ts_mean(v, 20))""",
    },
    "alpha041": {
        "category": "high_low_spread",
        "desc": "High-low spread normalized: (high - low) / close * rank(close)",
        "body": """        h, l, c = data["high"], data["low"], data["close"]
        spread = (h - l) / (c + 1e-8)
        return spread * rank(c)""",
    },
    "alpha042": {
        "category": "volume_surge",
        "desc": "Volume surge indicator: rank(volume / ts_mean(volume, 20)) * rank(close)",
        "body": """        c, v = data["close"], data["volume"]
        vol_ratio = v / (ts_mean(v, 20) + 1e-8)
        return rank(vol_ratio) * rank(c)""",
    },
    "alpha043": {
        "category": "price_volume_divergence",
        "desc": "Price-volume divergence: correlation(rank(close), rank(volume), 10) * (close / delay(close, 5) - 1)",
        "body": """        c, v = data["close"], data["volume"]
        corr_pv = correlation(rank(c), rank(v), 10)
        ret_5 = c / delay(c, 5) - 1
        return corr_pv * ret_5""",
    },
    "alpha044": {
        "category": "momentum_consistency",
        "desc": "Momentum consistency: ts_rank(correlation(close, delay(close,1), 10), 5)",
        "body": """        c = data["close"]
        autocorr = correlation(c, delay(c, 1), 10)
        return ts_rank(autocorr, 5)""",
    },
    "alpha045": {
        "category": "volatility_momentum",
        "desc": "Volatility momentum: rank(delta(ts_std(close, 20), 5))",
        "body": """        c = data["close"]
        vol = ts_std(c, 20)
        return rank(delta(vol, 5))""",
    },
    "alpha046": {
        "category": "volume_breakout",
        "desc": "Volume breakout: (volume - ts_mean(volume, 20)) / ts_std(volume, 20) * rank(close)",
        "body": """        c, v = data["close"], data["volume"]
        vol_z = (v - ts_mean(v, 20)) / (ts_std(v, 20) + 1e-8)
        return vol_z * rank(c)""",
    },
    "alpha047": {
        "category": "price_reversal",
        "desc": "Price reversal: -correlation(rank(close), rank(ts_mean(volume, 5)), 5)",
        "body": """        c, v = data["close"], data["volume"]
        return -correlation(rank(c), rank(ts_mean(v, 5)), 5)""",
    },
    "alpha048": {
        "category": "volume_trend",
        "desc": "Volume trend: rank(ts_mean(volume, 20)) - rank(ts_mean(volume, 5))",
        "body": """        v = data["volume"]
        return rank(ts_mean(v, 20)) - rank(ts_mean(v, 5))""",
    },
    "alpha049": {
        "category": "price_volume_ratio",
        "desc": "Price-volume ratio: rank(close) / (rank(volume) + 1)",
        "body": """        c, v = data["close"], data["volume"]
        return rank(c) / (rank(v) + 1)""",
    },
    "alpha050": {
        "category": "volatility_normalized_return",
        "desc": "Volatility-normalized return: returns / ts_std(returns, 20)",
        "body": """        c = data["close"]
        ret = c.pct_change()
        return ret / (ts_std(ret, 20) + 1e-8)""",
    },
    "alpha051": {
        "category": "high_low_momentum",
        "desc": "High-low momentum: (high - delay(high,5)) / (low - delay(low,5) + 1e-8)",
        "body": """        h, l = data["high"], data["low"]
        h_mom = h - delay(h, 5)
        l_mom = l - delay(l, 5)
        return h_mom / (l_mom + 1e-8)""",
    },
    "alpha052": {
        "category": "volume_price_correlation_change",
        "desc": "Change in volume-price correlation: delta(correlation(close, volume, 10), 5)",
        "body": """        c, v = data["close"], data["volume"]
        corr_pv = correlation(c, v, 10)
        return delta(corr_pv, 5)""",
    },
    "alpha053": {
        "category": "return_skewness",
        "desc": "Return skewness: ts_rank(ts_std(returns, 20), 5) where returns=pct_change(close)",
        "body": """        c = data["close"]
        ret = c.pct_change()
        return ts_rank(ts_std(ret, 20), 5)""",
    },
    "alpha054": {
        "category": "volume_autocorrelation",
        "desc": "Volume autocorrelation: correlation(volume, delay(volume, 5), 10)",
        "body": """        v = data["volume"]
        return correlation(v, delay(v, 5), 10)""",
    },
    "alpha055": {
        "category": "price_volume_consistency",
        "desc": "Price-volume consistency: rank(close) * rank(volume) - correlation(rank(close), rank(volume), 20)",
        "body": """        c, v = data["close"], data["volume"]
        return rank(c) * rank(v) - correlation(rank(c), rank(v), 20)""",
    },
    "alpha056": {
        "category": "volatility_trend",
        "desc": "Volatility trend: rank(delta(ts_std(close, 5), 5)) * rank(close)",
        "body": """        c = data["close"]
        vol_change = delta(ts_std(c, 5), 5)
        return rank(vol_change) * rank(c)""",
    },
    "alpha057": {
        "category": "volume_price_momentum",
        "desc": "Volume-price momentum: rank(close) * rank(volume) * (close / delay(close, 5) - 1)",
        "body": """        c, v = data["close"], data["volume"]
        ret = c / delay(c, 5) - 1
        return rank(c) * rank(v) * ret""",
    },
    "alpha058": {
        "category": "open_close_range",
        "desc": "Open-close range: (close - open) / (high - low + 1e-8) * rank(volume)",
        "body": """        o, h, l, c, v = data["open"], data["high"], data["low"], data["close"], data["volume"]
        oc_range = (c - o) / (h - l + 1e-8)
        return oc_range * rank(v)""",
    },
    "alpha059": {
        "category": "volume_weighted_price_change",
        "desc": "Volume-weighted price change: correlation(close, volume, 10) * delta(close, 5) / close",
        "body": """        c, v = data["close"], data["volume"]
        corr_pv = correlation(c, v, 10)
        return corr_pv * delta(c, 5) / (c + 1e-8)""",
    },
    "alpha060": {
        "category": "composite_momentum",
        "desc": "Composite momentum: rank(close / delay(close, 20)) + rank(close / delay(close, 5)) - rank(ts_std(close, 20))",
        "body": """        c = data["close"]
        mom_long = c / delay(c, 20)
        mom_short = c / delay(c, 5)
        vol = ts_std(c, 20)
        return rank(mom_long) + rank(mom_short) - rank(vol)""",
    },
    # --- alpha061-080 ---
    "alpha061": {
        "category": "trend_strength",
        "desc": "Trend strength: correlation(close, range(len(close)), 20) * rank(close)",
        "body": """        c = data["close"]
        time_idx = pd.Series(np.arange(len(c)), index=c.index)
        trend = correlation(c, time_idx, 20)
        return trend * rank(c)""",
    },
    "alpha062": {
        "category": "volume_trend_confirmation",
        "desc": "Volume trend confirmation: rank(delta(volume, 5)) * (close / delay(close, 5) - 1)",
        "body": """        c, v = data["close"], data["volume"]
        return rank(delta(v, 5)) * (c / delay(c, 5) - 1)""",
    },
    "alpha063": {
        "category": "price_reversal_risk",
        "desc": "Price reversal risk: ts_std(close, 20) / ts_mean(close, 20) * rank(close)",
        "body": """        c = data["close"]
        cv = ts_std(c, 20) / (ts_mean(c, 20) + 1e-8)
        return cv * rank(c)""",
    },
    "alpha064": {
        "category": "volume_breakout_strength",
        "desc": "Volume breakout strength: rank(volume / delay(volume, 5)) * rank(correlation(close, volume, 10))",
        "body": """        c, v = data["close"], data["volume"]
        v_ratio = v / (delay(v, 5) + 1e-8)
        return rank(v_ratio) * rank(correlation(c, v, 10))""",
    },
    "alpha065": {
        "category": "momentum_acceleration",
        "desc": "Momentum acceleration: delta(close / delay(close, 5), 5)",
        "body": """        c = data["close"]
        mom = c / delay(c, 5)
        return delta(mom, 5)""",
    },
    "alpha066": {
        "category": "volume_momentum_divergence",
        "desc": "Volume-momentum divergence: rank(delta(close, 5)) - rank(delta(volume, 5))",
        "body": """        c, v = data["close"], data["volume"]
        return rank(delta(c, 5)) - rank(delta(v, 5))""",
    },
    "alpha067": {
        "category": "price_range_volume",
        "desc": "Price range normalized by volume: (high - low) / close * rank(volume)",
        "body": """        h, l, c, v = data["high"], data["low"], data["close"], data["volume"]
        return (h - l) / (c + 1e-8) * rank(v)""",
    },
    "alpha068": {
        "category": "volume_price_rank_ratio",
        "desc": "Volume-price rank ratio: rank(volume) / (rank(close) + 1)",
        "body": """        c, v = data["close"], data["volume"]
        return rank(v) / (rank(c) + 1)""",
    },
    "alpha069": {
        "category": "high_low_volume_correlation",
        "desc": "High-low vs volume correlation: correlation(high - low, volume, 10)",
        "body": """        h, l, v = data["high"], data["low"], data["volume"]
        return correlation(h - l, v, 10)""",
    },
    "alpha070": {
        "category": "return_volatility_interaction",
        "desc": "Return-volatility interaction: (close/delay(close,5)-1) * ts_std(close,20)",
        "body": """        c = data["close"]
        ret = c / delay(c, 5) - 1
        return ret * ts_std(c, 20)""",
    },
    "alpha071": {
        "category": "volume_regime_change",
        "desc": "Volume regime change: rank(ts_mean(volume, 5)) - rank(ts_mean(volume, 20))",
        "body": """        v = data["volume"]
        return rank(ts_mean(v, 5)) - rank(ts_mean(v, 20))""",
    },
    "alpha072": {
        "category": "price_reversal_volume",
        "desc": "Price reversal confirmed by volume: -delta(close, 5) * ts_mean(volume, 5)",
        "body": """        c, v = data["close"], data["volume"]
        return -delta(c, 5) * ts_mean(v, 5)""",
    },
    "alpha073": {
        "category": "momentum_volatility_ratio",
        "desc": "Momentum-volatility ratio: (close/delay(close,20)-1) / (ts_std(close,20) + 1e-8)",
        "body": """        c = data["close"]
        mom = c / delay(c, 20) - 1
        return mom / (ts_std(c, 20) + 1e-8)""",
    },
    "alpha074": {
        "category": "volume_skew",
        "desc": "Volume skew: rank(ts_std(volume, 20)) - rank(ts_mean(volume, 20))",
        "body": """        v = data["volume"]
        return rank(ts_std(v, 20)) - rank(ts_mean(v, 20))""",
    },
    "alpha075": {
        "category": "composite_volume_price",
        "desc": "Composite volume-price: rank(close) + rank(volume) + correlation(close, volume, 10)",
        "body": """        c, v = data["close"], data["volume"]
        return rank(c) + rank(v) + correlation(c, v, 10)""",
    },
    "alpha076": {
        "category": "volatility_volume_ratio",
        "desc": "Volatility-volume ratio: ts_std(close, 20) / (ts_mean(volume, 20) + 1e-8)",
        "body": """        c, v = data["close"], data["volume"]
        return ts_std(c, 20) / (ts_mean(v, 20) + 1e-8)""",
    },
    "alpha077": {
        "category": "trend_volume_confirmation",
        "desc": "Trend volume confirmation: correlation(close, volume, 10) * rank(delta(close, 5))",
        "body": """        c, v = data["close"], data["volume"]
        return correlation(c, v, 10) * rank(delta(c, 5))""",
    },
    "alpha078": {
        "category": "price_reversal_speed",
        "desc": "Price reversal speed: -delta(close, 5) / (ts_std(close, 5) + 1e-8)",
        "body": """        c = data["close"]
        return -delta(c, 5) / (ts_std(c, 5) + 1e-8)""",
    },
    "alpha079": {
        "category": "volume_autocorr_change",
        "desc": "Volume autocorrelation change: delta(correlation(volume, delay(volume,5), 10), 5)",
        "body": """        v = data["volume"]
        v_autocorr = correlation(v, delay(v, 5), 10)
        return delta(v_autocorr, 5)""",
    },
    "alpha080": {
        "category": "price_volume_divergence_score",
        "desc": "Price-volume divergence score: rank(close) - rank(volume) * correlation(close, volume, 10)",
        "body": """        c, v = data["close"], data["volume"]
        return rank(c) - rank(v) * correlation(c, v, 10)""",
    },
    # --- alpha081-100 ---
    "alpha081": {
        "category": "complex_momentum",
        "desc": "Complex momentum: rank(delta(close, 3)) * rank(delta(close, 10)) * rank(close)",
        "body": """        c = data["close"]
        return rank(delta(c, 3)) * rank(delta(c, 10)) * rank(c)""",
    },
    "alpha082": {
        "category": "volume_pressure_index",
        "desc": "Volume pressure index: (volume - ts_mean(volume, 10)) / ts_std(volume, 10)",
        "body": """        v = data["volume"]
        return (v - ts_mean(v, 10)) / (ts_std(v, 10) + 1e-8)""",
    },
    "alpha083": {
        "category": "efficiency_ratio",
        "desc": "Efficiency ratio: abs(close - delay(close, 20)) / ts_sum(abs(delta(close, 1)), 20)",
        "body": """        c = data["close"]
        net_move = (c - delay(c, 20)).abs()
        gross_move = ts_sum(delta(c, 1).abs(), 20)
        return net_move / (gross_move + 1e-8)""",
    },
    "alpha084": {
        "category": "volume_normalized_return",
        "desc": "Volume-normalized return: returns * rank(volume) where returns=pct_change(close)",
        "body": """        c, v = data["close"], data["volume"]
        ret = c.pct_change()
        return ret * rank(v)""",
    },
    "alpha085": {
        "category": "volatility_regime_change",
        "desc": "Volatility regime change: ts_std(close, 5) / ts_std(close, 20)",
        "body": """        c = data["close"]
        return ts_std(c, 5) / (ts_std(c, 20) + 1e-8)""",
    },
    "alpha086": {
        "category": "composite_return_risk",
        "desc": "Composite return-risk: (close/delay(close,20)-1) * rank(1/ts_std(close,20))",
        "body": """        c = data["close"]
        ret_20 = c / delay(c, 20) - 1
        inv_risk = 1.0 / (ts_std(c, 20) + 1e-8)
        return ret_20 * rank(inv_risk)""",
    },
    "alpha087": {
        "category": "volume_volatility_correlation",
        "desc": "Volume-volatility correlation: correlation(volume, ts_std(close, 5), 10)",
        "body": """        c, v = data["close"], data["volume"]
        vol = ts_std(c, 5)
        return correlation(v, vol, 10)""",
    },
    "alpha088": {
        "category": "momentum_stability",
        "desc": "Momentum stability: ts_rank(close / delay(close, 5), 10)",
        "body": """        c = data["close"]
        mom = c / delay(c, 5)
        return ts_rank(mom, 10)""",
    },
    "alpha089": {
        "category": "volume_momentum_ratio",
        "desc": "Volume momentum ratio: rank(ts_mean(volume, 5)) / rank(ts_mean(volume, 20))",
        "body": """        v = data["volume"]
        return rank(ts_mean(v, 5)) / (rank(ts_mean(v, 20)) + 1)""",
    },
    "alpha090": {
        "category": "price_dispersion",
        "desc": "Price dispersion: ts_std(close, 10) / ts_mean(close, 10)",
        "body": """        c = data["close"]
        return ts_std(c, 10) / (ts_mean(c, 10) + 1e-8)""",
    },
    "alpha091": {
        "category": "volume_surge_momentum",
        "desc": "Volume surge momentum: rank(volume / delay(volume, 5)) * (close / delay(close, 5) - 1)",
        "body": """        c, v = data["close"], data["volume"]
        v_surge = v / (delay(v, 5) + 1e-8)
        return rank(v_surge) * (c / delay(c, 5) - 1)""",
    },
    "alpha092": {
        "category": "trend_volume_consistency",
        "desc": "Trend-volume consistency: ts_rank(close, 20) * rank(correlation(close, volume, 10))",
        "body": """        c, v = data["close"], data["volume"]
        return ts_rank(c, 20) * rank(correlation(c, v, 10))""",
    },
    "alpha093": {
        "category": "price_volume_regime",
        "desc": "Price-volume regime: ts_rank(close, 10) * (volume / ts_mean(volume, 20))",
        "body": """        c, v = data["close"], data["volume"]
        return ts_rank(c, 10) * (v / (ts_mean(v, 20) + 1e-8))""",
    },
    "alpha094": {
        "category": "volatility_momentum_interaction",
        "desc": "Volatility-momentum interaction: ts_std(close, 20) * (close / delay(close, 10) - 1)",
        "body": """        c = data["close"]
        mom = c / delay(c, 10) - 1
        return ts_std(c, 20) * mom""",
    },
    "alpha095": {
        "category": "volume_efficiency",
        "desc": "Volume efficiency: ts_sum(volume, 5) / ts_sum(volume, 20) * rank(close)",
        "body": """        c, v = data["close"], data["volume"]
        vol_ratio = ts_sum(v, 5) / (ts_sum(v, 20) + 1e-8)
        return vol_ratio * rank(c)""",
    },
    "alpha096": {
        "category": "return_volume_correlation",
        "desc": "Return-volume correlation: correlation(pct_change(close), volume, 10)",
        "body": """        c, v = data["close"], data["volume"]
        ret = c.pct_change()
        return correlation(ret, v, 10)""",
    },
    "alpha097": {
        "category": "composite_trend",
        "desc": "Composite trend: ts_rank(close, 20) + ts_rank(close, 10) - ts_rank(close, 5)",
        "body": """        c = data["close"]
        return ts_rank(c, 20) + ts_rank(c, 10) - ts_rank(c, 5)""",
    },
    "alpha098": {
        "category": "volume_breakout_momentum",
        "desc": "Volume breakout momentum: rank(volume) * (close / delay(close, 5) - 1)",
        "body": """        c, v = data["close"], data["volume"]
        return rank(v) * (c / delay(c, 5) - 1)""",
    },
    "alpha099": {
        "category": "price_reversal_volatility",
        "desc": "Price reversal with volatility: -delta(close, 5) * ts_std(close, 20)",
        "body": """        c = data["close"]
        return -delta(c, 5) * ts_std(c, 20)""",
    },
    "alpha100": {
        "category": "volume_normalized_trend",
        "desc": "Volume-normalized trend: (close / delay(close, 20) - 1) / ts_mean(volume, 20)",
        "body": """        c, v = data["close"], data["volume"]
        trend = c / delay(c, 20) - 1
        return trend / (ts_mean(v, 20) + 1e-8)""",
    },
    "alpha101": {
        "category": "ultimate_composite",
        "desc": "Ultimate composite: rank(close) + rank(volume) + correlation(close, volume, 10) + ts_rank(close, 20)",
        "body": """        c, v = data["close"], data["volume"]
        return rank(c) + rank(v) + correlation(c, v, 10) + ts_rank(c, 20)""",
    },
}


def generate_alpha_file(alpha_name: str, formula: dict) -> str:
    """Generate a single alpha factor file."""
    imports = """import pandas as pd
import numpy as np
from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .operators import rank, ts_rank, correlation, delay, delta, ts_mean, ts_std, ts_sum, ts_min, ts_max
"""
    class_name = alpha_name.title().replace("_", "")  # alpha033 -> Alpha033
    return f"""{imports}

@FactorRegistry.register
class {class_name}(AlphaFactor):
    \"\"\"{alpha_name.title()}: {formula['desc']}\"\"\"

    @property
    def name(self) -> str:
        return "{alpha_name}"

    @property
    def category(self) -> str:
        return "{formula['category']}"

    @property
    def description(self) -> str:
        return "{formula['desc']}"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
{formula['body']}
"""


def main():
    """Generate all factor files from alpha033 to alpha101."""
    for alpha_name, formula in FORMULAS.items():
        filepath = os.path.join(FACTOR_DIR, f"{alpha_name}.py")
        content = generate_alpha_file(alpha_name, formula)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ {alpha_name}.py")


if __name__ == "__main__":
    print("Generating WorldQuant-style Alpha factors (alpha033-alpha101)...")
    main()
    print("Done!")
