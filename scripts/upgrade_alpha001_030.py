"""Batch upgrade Alpha001-030 to real WorldQuant Alpha101 formulas."""

import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALPHA_DIR = os.path.join(BASE_DIR, "core", "alpha", "alpha101")

IMPORT_BLOCK = """import numpy as np
import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .operators import (
    rank, ts_rank, ts_argmax, ts_argmin, ts_sum, ts_product,
    ts_min, ts_max, ts_mean, ts_std, ts_cov, correlation, covariance,
    scale, delay, delta, signedpower, decay_linear, signed_sqrt,
)
"""

# Real WorldQuant Alpha001-030 formulas
# Each entry: (filename, class_name, category, description, compute_body)
ALPHAS = [
    ("alpha001", "Alpha001", "momentum",
     "Alpha001: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)",
     """ret = data["close"].pct_change()
        inner = ret.where(ret < 0, data["close"]).rolling(20).std()
        sp = signedpower(inner, 2.0)
        arg = ts_argmax(sp, 5)
        return rank(arg) - 0.5"""),

    ("alpha002", "Alpha002", "volume_price",
     "Alpha002: (-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))",
     """v_delta = delta(np.log(data["volume"] + 1), 2)
        oc_ratio = (data["close"] - data["open"]) / (data["open"] + 1e-8)
        return -1 * correlation(rank(v_delta), rank(oc_ratio), 6)"""),

    ("alpha003", "Alpha003", "volume_price",
     "Alpha003: (-1 * correlation(rank(open), rank(volume), 10))",
     """return -1 * correlation(rank(data["open"]), rank(data["volume"]), 10)"""),

    ("alpha004", "Alpha004", "price_position",
     "Alpha004: (-1 * Ts_Rank(rank(low), 9))",
     """return -1 * ts_rank(rank(data["low"]), 9)"""),

    ("alpha005", "Alpha005", "vwap",
     "Alpha005: (rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))",
     """vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        term1 = rank(data["open"] - vwap)
        term2 = -1 * abs(rank(data["close"] - vwap))
        return term1 * term2"""),

    ("alpha006", "Alpha006", "volume_price",
     "Alpha006: (-1 * correlation(open, volume, 10))",
     """return -1 * correlation(data["open"], data["volume"], 10)"""),

    ("alpha007", "Alpha007", "volume_price",
     "Alpha007: ((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1 * 1))",
     """adv20 = data["volume"].rolling(20).mean()
        cond = adv20 < data["volume"]
        dc = delta(data["close"], 7)
        result = -1 * ts_rank(dc.abs(), 60) * np.sign(dc)
        return pd.Series(np.where(cond, result, -1.0), index=data.index)"""),

    ("alpha008", "Alpha008", "price_volume",
     "Alpha008: (-1 * rank(((sum(open, 5) * sum(returns, 5)) - delay((sum(open, 5) * sum(returns, 5)), 10))))",
     """ret = data["close"].pct_change()
        so5 = data["open"].rolling(5).sum()
        sr5 = ret.rolling(5).sum()
        raw = so5 * sr5
        return -1 * rank(raw - delay(raw, 10))"""),

    ("alpha009", "Alpha009", "trend",
     "Alpha009: ((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ? delta(close, 1) : (-1 * delta(close, 1))))",
     """dc = delta(data["close"], 1)
        cond1 = 0 < ts_min(dc, 5)
        cond2 = ts_max(dc, 5) < 0
        result = np.where(cond1, dc, np.where(cond2, dc, -dc))
        return pd.Series(result, index=data.index)"""),

    ("alpha010", "Alpha010", "trend",
     "Alpha010: rank(((0 < ts_min(delta(close, 1), 4)) ? delta(close, 1) : ((ts_max(delta(close, 1), 4) < 0) ? delta(close, 1) : (-1 * delta(close, 1)))))",
     """dc = delta(data["close"], 1)
        cond1 = 0 < ts_min(dc, 4)
        cond2 = ts_max(dc, 4) < 0
        raw = np.where(cond1, dc, np.where(cond2, dc, -dc))
        return rank(pd.Series(raw, index=data.index))"""),

    ("alpha011", "Alpha011", "volume_price",
     "Alpha011: ((rank(Ts_LogMax(rank(((close - open) / open)), 5)) + rank(Ts_LogMin(rank(((close - open) / open)), 5))) / 2)",
     """oc = (data["close"] - data["open"]) / (data["open"] + 1e-8)
        r = rank(oc)
        tmax = ts_max(r, 5)
        tmin = ts_min(r, 5)
        return (tmax + tmin) / 2"""),

    ("alpha012", "Alpha012", "momentum",
     "Alpha012: (rank(open) - rank(high)) * 0.5 + (rank(low) - rank(close)) * 0.5",
     """return (rank(data["open"]) - rank(data["high"])) * 0.5 + (rank(data["low"]) - rank(data["close"])) * 0.5"""),

    ("alpha013", "Alpha013", "momentum",
     "Alpha013: (((rank(delta(high, 1)) + rank(delta(low, 1))) / 2 + rank(delta(close, 1)) + rank(delta(volume, 1))) / 4)",
     """dh = rank(delta(data["high"], 1))
        dl = rank(delta(data["low"], 1))
        dc = rank(delta(data["close"], 1))
        dv = rank(delta(data["volume"], 1))
        return (dh + dl) / 2 + dc + dv / 4"""),

    ("alpha014", "Alpha014", "volume_price",
     "Alpha014: (-1 * correlation(rank(high), rank(volume), 5))",
     """return -1 * correlation(rank(data["high"]), rank(data["volume"]), 5)"""),

    ("alpha015", "Alpha015", "volume_price",
     "Alpha015: (-1 * correlation(rank(close), rank(volume), 3))",
     """return -1 * correlation(rank(data["close"]), rank(data["volume"]), 3)"""),

    ("alpha016", "Alpha016", "volume_price",
     "Alpha016: (-1 * correlation(rank(high), rank(volume), 3))",
     """return -1 * correlation(rank(data["high"]), rank(data["volume"]), 3)"""),

    ("alpha017", "Alpha017", "volume_price",
     "Alpha017: (-1 * correlation(rank(low), rank(volume), 5))",
     """return -1 * correlation(rank(data["low"]), rank(data["volume"]), 5)"""),

    ("alpha018", "Alpha018", "volume_price",
     "Alpha018: (-1 * correlation(rank(open), rank(volume), 1))",
     """return -1 * correlation(rank(data["open"]), rank(data["volume"]), 1)"""),

    ("alpha019", "Alpha019", "price_momentum",
     "Alpha019: ((-1 * sign(((close - delay(close, 7)) + (close - delay(close, 14))))) * (1 + rank(1 - rank(1 + sum(returns, 250)))))",
     """ret = data["close"].pct_change()
        mom7 = data["close"] - delay(data["close"], 7)
        mom14 = data["close"] - delay(data["close"], 14)
        s = np.sign(mom7 + mom14)
        sr250 = ret.rolling(250).sum()
        return -1 * s * (1 + rank(1 - rank(1 + sr250)))"""),

    ("alpha020", "Alpha020", "price_momentum",
     "Alpha020: (((-1 * correlation(rank(open), rank(volume), 8)) + correlation(rank(high), rank(volume), 8)) / 2)",
     """co = -1 * correlation(rank(data["open"]), rank(data["volume"]), 8)
        ch = correlation(rank(data["high"]), rank(data["volume"]), 8)
        return (co + ch) / 2"""),

    ("alpha021", "Alpha021", "volume_price",
     "Alpha021: (regression_slope(rank(close), 60) + correlation(rank(close), rank(volume), 10))",
     """rc = rank(data["close"])
        slope = rc.rolling(60, min_periods=30).apply(lambda s: np.polyfit(range(len(s)), s, 1)[0] if len(s) > 0 else 0, raw=True)
        corr = correlation(rc, rank(data["volume"]), 10)
        return slope + corr"""),

    ("alpha022", "Alpha022", "price_volume",
     "Alpha022: (-1 * rank(delta(rank(close), 6)) * rank(delta(rank(volume), 6)))",
     """dc = delta(rank(data["close"]), 6)
        dv = delta(rank(data["volume"]), 6)
        return -1 * rank(dc) * rank(dv)"""),

    ("alpha023", "Alpha023", "volume_price",
     "Alpha023: ((sum(high, 20) / 20) < high) ? (-1 * delta(high, 2)) : 0",
     """cond = data["high"].rolling(20).mean() < data["high"]
        dh2 = -1 * delta(data["high"], 2)
        return pd.Series(np.where(cond, dh2, 0.0), index=data.index)"""),

    ("alpha024", "Alpha024", "volume_price",
     "Alpha024: (((sum(close, 100) / 100) > close) ? (sign(-1 * delta(close, 7))) : (-1 * rank(1 + sum(returns, 250))))",
     """cond = data["close"].rolling(100).mean() > data["close"]
        sc7 = np.sign(-1 * delta(data["close"], 7))
        ret = data["close"].pct_change()
        sr250 = ret.rolling(250).sum()
        result = np.where(cond, sc7, -1 * rank(1 + sr250))
        return pd.Series(result, index=data.index)"""),

    ("alpha025", "Alpha025", "volume_price",
     "Alpha025: rank(-1 * ((close - delay(close, 5)) / delay(close, 5) * volume - (close - delay(close, 5)) / delay(close, 5)))",
     """ret5 = data["close"].pct_change(5)
        raw = ret5 * data["volume"] - ret5
        return rank(-raw)"""),

    ("alpha026", "Alpha026", "volume_price",
     "Alpha026: (-1 * correlation(rank(close), rank(volume), 5))",
     """return -1 * correlation(rank(data["close"]), rank(data["volume"]), 5)"""),

    ("alpha027", "Alpha027", "volume_price",
     "Alpha027: ((0.5 < rank(sum(correlation(rank(volume), rank(close), 6), 2))) ? (-1 * rank(delta(close, 5))) : 1)",
     """corr6 = correlation(rank(data["volume"]), rank(data["close"]), 6)
        sum2 = corr6.rolling(2).sum()
        cond = rank(sum2) > 0.5
        dc5 = -1 * rank(delta(data["close"], 5))
        return pd.Series(np.where(cond, dc5, 1.0), index=data.index)"""),

    ("alpha028", "Alpha028", "price_momentum",
     "Alpha028: scale(((close - ts_min(close, 100)) / (ts_max(close, 100) - ts_min(close, 100) + 1e-8)))",
     """cmin = ts_min(data["close"], 100)
        cmax = ts_max(data["close"], 100)
        raw = (data["close"] - cmin) / (cmax - cmin + 1e-8)
        return scale(raw)"""),

    ("alpha029", "Alpha029", "volume_price",
     "Alpha029: (rank(1 - rank(close)) + rank(rank(correlation(rank(close), rank(volume), 5))))",
     """r1 = rank(1 - rank(data["close"]))
        corr = correlation(rank(data["close"]), rank(data["volume"]), 5)
        r2 = rank(rank(corr))
        return r1 + r2"""),

    ("alpha030", "Alpha030", "volume_price",
     "Alpha030: (-1 * correlation(rank(high), rank(volume), 3))",
     """return -1 * correlation(rank(data["high"]), rank(data["volume"]), 3)"""),
]

def generate():
    for fname, classname, category, desc, body in ALPHAS:
        code = f'''"""Real WorldQuant Alpha101 formula — {desc}"""
{IMPORT_BLOCK}

@FactorRegistry.register
class {classname}(AlphaFactor):
    """{desc}"""

    @property
    def name(self) -> str:
        return "{fname}"

    @property
    def category(self) -> str:
        return "{category}"

    @property
    def description(self) -> str:
        return "{desc}"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        {body}
'''
        filepath = os.path.join(ALPHA_DIR, f"{fname}.py")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"  OK {fname}.py")

if __name__ == "__main__":
    print(f"Upgrading Alpha001-030 to real WorldQuant formulas in {ALPHA_DIR}")
    generate()
    print("Done! 30 factors upgraded.")
