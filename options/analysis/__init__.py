"""期权链分析工具 — PCR / Max Pain / 持仓量分布。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class OptionChainRow:
    """期权链单行:某行权价的看涨/看跌 持仓量与成交量。"""

    strike: float
    call_oi: float = 0.0
    put_oi: float = 0.0
    call_volume: float = 0.0
    put_volume: float = 0.0


def put_call_ratio(rows: List[OptionChainRow], by: str = "oi") -> float:
    """Put/Call Ratio。

    by="oi" 用持仓量,by="volume" 用成交量。
    PCR > 1 通常代表偏空情绪(或对冲需求高),极值常作反转信号。
    """
    if by == "volume":
        calls = sum(r.call_volume for r in rows)
        puts = sum(r.put_volume for r in rows)
    else:
        calls = sum(r.call_oi for r in rows)
        puts = sum(r.put_oi for r in rows)
    if calls <= 0:
        return float("nan")
    return puts / calls


def max_pain(rows: List[OptionChainRow]) -> Optional[float]:
    """最大痛点:令所有期权买方总内在价值最小的行权价。

    即期权卖方(做市商)整体损失最小的标的结算价,理论上价格有向其靠拢的倾向。
    """
    if not rows:
        return None
    strikes = sorted(r.strike for r in rows)
    best_k: Optional[float] = None
    best_pain = float("inf")
    for settle in strikes:
        pain = 0.0
        for r in rows:
            # 结算在 settle 时,call 买方内在价值 = max(settle-K,0)
            pain += max(settle - r.strike, 0.0) * r.call_oi
            pain += max(r.strike - settle, 0.0) * r.put_oi
        if pain < best_pain:
            best_pain = pain
            best_k = settle
    return best_k


def oi_distribution(rows: List[OptionChainRow]) -> Dict[float, Dict[str, float]]:
    """按行权价输出持仓量分布(便于找支撑/压力墙)。"""
    return {
        r.strike: {"call_oi": r.call_oi, "put_oi": r.put_oi}
        for r in sorted(rows, key=lambda x: x.strike)
    }
