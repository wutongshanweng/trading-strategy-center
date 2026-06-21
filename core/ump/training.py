"""UMP 训练数据生成 — 从策略回测产出"逐笔交易特征 + 盈亏"训练集。

跑某策略在某合约上的回测, 对每个入场点提取 trade_features, 配对该笔最终盈亏,
组装成 UMPManager.fit 所需的 DataFrame。
"""

from __future__ import annotations

import copy
from typing import List, Optional

import pandas as pd
from loguru import logger

from core.ump.judges import trade_features
from signals.base import Direction
from signals.registry import get_strategy


def build_training_set(strategy_name: str, df: pd.DataFrame,
                       lookback: int = 20) -> Optional[pd.DataFrame]:
    """对单策略在 df 上逐根计算信号, 入场点提取特征, 用后续价格变动定盈亏。

    简化盈亏: 入场后 持有到下一次反向信号或 N 根后平仓 的收益。
    返回含特征列 + pnl 列的 DataFrame。
    """
    import signals.strategies  # noqa: F401 触发注册
    cls = get_strategy(strategy_name)
    if cls is None or df is None or len(df) < lookback + 30:
        return None

    rows: List[dict] = []
    hold = 10  # 持有 10 根后评估盈亏
    for i in range(lookback, len(df) - hold):
        window = df.iloc[:i + 1]
        inst = cls()
        inst.params = copy.deepcopy(type(inst).params)
        try:
            sig = inst.compute(window, "ump_train")
        except Exception:
            continue
        if sig is None or sig.direction == Direction.HOLD:
            continue
        feats = trade_features(df, i, lookback)
        if feats is None:
            continue
        entry = float(df.iloc[i]["close"])
        exit_px = float(df.iloc[i + hold]["close"])
        # 方向化盈亏
        if sig.direction == Direction.BUY:
            pnl = (exit_px - entry) / entry
        else:
            pnl = (entry - exit_px) / entry
        rows.append({**feats, "pnl": pnl, "direction": sig.direction.value})

    if len(rows) < 20:
        return None
    out = pd.DataFrame(rows)
    logger.info(f"[ump] training set for {strategy_name}: {len(out)} trades "
                f"({(out['pnl'] > 0).mean():.0%} win)")
    return out


FEATURE_COLS = ["momentum", "momentum_5", "volatility", "price_position",
                "body_ratio", "volume_ratio", "upper_wick", "skew"]
