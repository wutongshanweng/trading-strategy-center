"""
合约生命周期 — 统一处理期货/期权合约的到期、状态、有效数据窗口。

核心原则 (用户设计要求):
- 每个真实合约有生命周期 (挂牌→交割), 生命周期外不应有数据。
- 合约状态: 在挂 (今天≤到期) / 已到期 (今天>到期), 期货期权统一。

用途:
1. status(code) — 合约状态, 供前端展示/过滤。
2. lifecycle_guard(df, code) — 入库前裁剪超出生命周期的脏数据
   (防止把"主力连续"误存成具体合约, 如 M2609 出现 2005 年数据)。

到期日为近似 (按交割月月末); 精确到期规则各交易所不同, 有 symbols.expire_date 时优先用。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd

from .main_contract import MainContractResolver

_resolver = MainContractResolver()

# 真实合约最长生命周期 (年): 任何期货/期权合约都不可能在到期前这么久就有数据。
# 用于裁剪误存的连续合约历史。期货远月最长约2-3年, 取 3 年留足余量。
MAX_LIFE_YEARS = 3


def parse_expiry(code: str) -> Optional[date]:
    """合约到期日 (近似: 交割月月末)。无法解析 (纯品种/连续) 返回 None。"""
    p = _resolver.parse_contract_code(code)
    year, month = p.get("year"), p.get("month")
    if not year or not month:
        return None
    return (pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)).date()


def status(code: str, today: Optional[date] = None) -> str:
    """合约状态: '在挂' / '已到期' / '连续' (纯品种或主连无固定到期)。"""
    exp = parse_expiry(code)
    if exp is None:
        return "连续"
    today = today or date.today()
    return "已到期" if today > exp else "在挂"


def lifecycle_window(code: str) -> Optional[tuple[date, date]]:
    """合约有效数据窗口 (最早可信日, 到期日)。无固定到期返回 None。

    最早可信日 = 到期 - MAX_LIFE_YEARS。窗口外的数据视为脏数据 (误存连续合约)。
    """
    exp = parse_expiry(code)
    if exp is None:
        return None
    earliest = (pd.Timestamp(exp) - pd.DateOffset(years=MAX_LIFE_YEARS)).date()
    return earliest, exp


def lifecycle_guard(df: pd.DataFrame, code: str, dt_col: str = "datetime") -> pd.DataFrame:
    """裁剪超出合约生命周期的行。连续/纯品种 (无固定到期) 不裁剪原样返回。

    返回裁剪后的 df。若裁剪掉了行, 调用方应警惕"误存连续合约"。
    """
    win = lifecycle_window(code)
    if win is None or df is None or df.empty or dt_col not in df.columns:
        return df
    earliest, exp = win
    dt = pd.to_datetime(df[dt_col])
    # 到期后留 1 个月缓冲 (摘牌当月数据), 最早日前一律视为脏数据
    mask = (dt >= pd.Timestamp(earliest)) & (dt <= pd.Timestamp(exp) + pd.offsets.MonthEnd(1))
    return df[mask]
