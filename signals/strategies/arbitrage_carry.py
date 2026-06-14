"""套利 / Carry / 期限结构 / 季节性策略。

对齐《架构升级建议》2.1 arbitrage/ carry_term_structure/ seasonality/ 目录。

注意:套利类策略需要两条腿。为兼容现有 compute(df, symbol) 单帧接口,
约定:配对/价差策略从 df 的 'close2' 列读取第二条腿价格(由上层在
构造跨品种数据时注入)。若无 'close2' 列则返回 None(安全降级)。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register
from signals.indicators import ZSCORE


# ============================================================
# 配对 / 价差套利(需要 close2 列)
# ============================================================

@register
class ArbPairsZScore(BaseStrategy):
    name = "arb_pairs_zscore"
    description = "配对交易:价差 Z-score 均值回归(需 close2 列)"
    timeframes = ["1d", "4h"]
    params = {"window": 60, "entry_z": 2.0, "exit_z": 0.5, "use_log": True}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if "close2" not in df.columns:
            return None
        a, b = df["close"], df["close2"]
        if self.params["use_log"]:
            spread = np.log(a.replace(0, np.nan)) - np.log(b.replace(0, np.nan))
        else:
            spread = a - b
        z = ZSCORE(spread, self.params["window"]).dropna()
        if z.empty:
            return None
        zv = float(z.iloc[-1])
        cv = float(a.iloc[-1])
        entry = self.params["entry_z"]
        if zv > entry:
            # 价差过高 -> 做空腿1(买腿2)
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min((zv - entry) / 2 + 0.3, 1.0), price=cv,
                          reason=f"配对价差 Z={zv:.2f} 偏高,做空价差",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          metadata={"zscore": zv, "leg": "short_a_long_b"})
        if zv < -entry:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min((-zv - entry) / 2 + 0.3, 1.0), price=cv,
                          reason=f"配对价差 Z={zv:.2f} 偏低,做多价差",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          metadata={"zscore": zv, "leg": "long_a_short_b"})
        return None


@register
class ArbRatioSpread(BaseStrategy):
    name = "arb_ratio_spread"
    description = "比价套利:两品种比值的均值回归(需 close2 列)"
    timeframes = ["1d"]
    params = {"window": 60, "entry_z": 2.0}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if "close2" not in df.columns:
            return None
        ratio = df["close"] / df["close2"].replace(0, np.nan)
        z = ZSCORE(ratio, self.params["window"]).dropna()
        if z.empty:
            return None
        zv = float(z.iloc[-1])
        cv = float(df["close"].iloc[-1])
        entry = self.params["entry_z"]
        if zv > entry:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min((zv - entry) / 2 + 0.3, 1.0), price=cv,
                          reason=f"比价 Z={zv:.2f} 偏高", strategy_name=self.name,
                          timeframe=self.timeframes[0], metadata={"ratio_z": zv})
        if zv < -entry:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min((-zv - entry) / 2 + 0.3, 1.0), price=cv,
                          reason=f"比价 Z={zv:.2f} 偏低", strategy_name=self.name,
                          timeframe=self.timeframes[0], metadata={"ratio_z": zv})
        return None


@register
class ArbBasis(BaseStrategy):
    name = "arb_basis"
    description = "期现基差套利:基差 = 期货-现货,均值回归(需 close2=现货)"
    timeframes = ["1d"]
    params = {"window": 60, "entry_z": 1.8}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if "close2" not in df.columns:
            return None
        basis = df["close"] - df["close2"]   # 期货 - 现货
        z = ZSCORE(basis, self.params["window"]).dropna()
        if z.empty:
            return None
        zv = float(z.iloc[-1])
        cv = float(df["close"].iloc[-1])
        entry = self.params["entry_z"]
        if zv > entry:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min((zv - entry) / 2 + 0.3, 1.0), price=cv,
                          reason=f"基差 Z={zv:.2f} 偏高(期货贵),做空基差",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          metadata={"basis_z": zv})
        if zv < -entry:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min((-zv - entry) / 2 + 0.3, 1.0), price=cv,
                          reason=f"基差 Z={zv:.2f} 偏低(期货贱),做多基差",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          metadata={"basis_z": zv})
        return None


# ============================================================
# Carry / 期限结构(需 close_far 列:远月合约价)
# ============================================================

@register
class CarryRollYield(BaseStrategy):
    name = "carry_roll_yield"
    description = "展期收益:近月vs远月,Backwardation做多/Contango做空(需 close_far 列)"
    timeframes = ["1d"]
    params = {"days_to_far": 30, "threshold": 0.005}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if "close_far" not in df.columns:
            return None
        near = float(df["close"].iloc[-1])
        far = float(df["close_far"].iloc[-1])
        if far <= 0 or near <= 0:
            return None
        # 年化 roll yield ≈ (near/far - 1) * (365/days)
        ann = (near / far - 1.0) * (365.0 / self.params["days_to_far"])
        th = self.params["threshold"]
        if ann > th:
            # 近 > 远 = Backwardation,通常做多
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min(abs(ann) * 5, 1.0), price=near,
                          reason=f"Backwardation 年化roll={ann:.1%},做多",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          metadata={"roll_yield": ann})
        if ann < -th:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min(abs(ann) * 5, 1.0), price=near,
                          reason=f"Contango 年化roll={ann:.1%},做空",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          metadata={"roll_yield": ann})
        return None


@register
class CarryTermStructureSlope(BaseStrategy):
    name = "carry_term_structure_slope"
    description = "期限结构斜率动量:近远月价差变化方向(需 close_far 列)"
    timeframes = ["1d"]
    params = {"lookback": 10}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if "close_far" not in df.columns:
            return None
        spread = df["close"] - df["close_far"]
        lb = self.params["lookback"]
        if len(spread.dropna()) < lb + 1:
            return None
        change = float(spread.iloc[-1] - spread.iloc[-1 - lb])
        near = float(df["close"].iloc[-1])
        if change > 0:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=0.55,
                          price=near, reason="期限结构走向 Backwardation(价差上行)",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        if change < 0:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=0.55,
                          price=near, reason="期限结构走向 Contango(价差下行)",
                          strategy_name=self.name, timeframe=self.timeframes[0])
        return None


# ============================================================
# 季节性(基于日期特征,纯单帧)
# ============================================================

@register
class SeasonalityMonthly(BaseStrategy):
    name = "seasonality_monthly"
    description = "月度季节性:历史同月平均收益方向"
    timeframes = ["1d"]
    params = {"min_years": 3, "threshold": 0.01}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if not isinstance(df.index, pd.DatetimeIndex):
            return None
        ret = df["close"].pct_change(fill_method=None)
        monthly = ret.groupby(df.index.month)
        current_month = df.index[-1].month
        if current_month not in monthly.groups:
            return None
        grp = monthly.get_group(current_month)
        # 该月历史日均收益
        avg = float(grp.mean())
        count_years = df.index.year.nunique()
        if count_years < self.params["min_years"]:
            return None
        cv = float(df["close"].iloc[-1])
        # 月度累积近似:日均 * 21
        monthly_exp = avg * 21
        th = self.params["threshold"]
        if monthly_exp > th:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min(abs(monthly_exp) * 10, 0.8), price=cv,
                          reason=f"{current_month}月历史季节性偏多({monthly_exp:.1%})",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          metadata={"month": current_month, "expected": monthly_exp})
        if monthly_exp < -th:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min(abs(monthly_exp) * 10, 0.8), price=cv,
                          reason=f"{current_month}月历史季节性偏空({monthly_exp:.1%})",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          metadata={"month": current_month, "expected": monthly_exp})
        return None


@register
class SeasonalityDayOfWeek(BaseStrategy):
    name = "seasonality_day_of_week"
    description = "星期效应:历史同星期平均收益方向"
    timeframes = ["1d"]
    params = {"min_obs": 60, "threshold": 0.0008}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if not isinstance(df.index, pd.DatetimeIndex):
            return None
        ret = df["close"].pct_change(fill_method=None)
        dow = df.index[-1].dayofweek
        grp = ret.groupby(df.index.dayofweek)
        if dow not in grp.groups or len(grp.get_group(dow)) < self.params["min_obs"] // 5:
            return None
        avg = float(grp.get_group(dow).mean())
        cv = float(df["close"].iloc[-1])
        th = self.params["threshold"]
        if avg > th:
            return Signal(symbol=symbol, direction=Direction.BUY,
                          confidence=min(abs(avg) * 200, 0.6), price=cv,
                          reason=f"星期{dow + 1}历史偏多", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        if avg < -th:
            return Signal(symbol=symbol, direction=Direction.SELL,
                          confidence=min(abs(avg) * 200, 0.6), price=cv,
                          reason=f"星期{dow + 1}历史偏空", strategy_name=self.name,
                          timeframe=self.timeframes[0])
        return None
