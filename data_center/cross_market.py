"""
跨市场相关性计算 (设计文档 §2.9 / Phase 4)。

对 cross_market_mapping 中每条关系, 计算:
- corr_20d / corr_60d: 两品种收益率的滚动相关系数 (最近值)
- lead_lag_corr / lag_days: 领先-滞后最优相关 (在 +-5 日内搜索)

数据来源: kline D1 收盘价。期货用主力连续 (优先 is_main, 否则成交量最大合约)。
结果回写 cross_market_mapping。
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger

from .storage.duckdb_store import DuckDBStore, get_store


def _product_close_series(store: DuckDBStore, product_code: str) -> pd.Series:
    """取某品种代表性 D1 收盘序列 (按日期)。

    期货: 选 D1 数据最多的合约作为代表 (近似主力连续)。
    股票/指数: 该品种唯一 symbol。
    """
    rows = store.query(
        """SELECT k.datetime, k.close, k.symbol_id
           FROM kline k
           JOIN symbols sy ON k.symbol_id = sy.symbol_id
           JOIN products p ON sy.product_id = p.product_id
           WHERE p.code = ? AND k.timeframe = 'D1'""",
        [product_code.upper()],
    )
    if rows.empty:
        return pd.Series(dtype=float)
    # 选数据最多的 symbol_id 作代表
    top_sid = rows["symbol_id"].value_counts().idxmax()
    s = rows[rows["symbol_id"] == top_sid].copy()
    s["datetime"] = pd.to_datetime(s["datetime"])
    s = s.sort_values("datetime").set_index("datetime")["close"].astype(float)
    return s[~s.index.duplicated(keep="last")]


def _lead_lag(ra: pd.Series, rb: pd.Series, max_lag: int = 5) -> tuple[float, int]:
    """在 [-max_lag, max_lag] 搜索使相关最大的滞后天数。

    lag>0 表示 A 领先 B lag 天。返回 (最优相关, 最优lag)。
    """
    best_corr, best_lag = 0.0, 0
    for lag in range(-max_lag, max_lag + 1):
        c = ra.corr(rb.shift(-lag))
        if pd.notna(c) and abs(c) > abs(best_corr):
            best_corr, best_lag = float(c), lag
    return best_corr, best_lag


def compute_all(store: Optional[DuckDBStore] = None) -> int:
    """计算并回写所有映射的相关统计。返回更新条数。"""
    store = store or get_store()
    maps = store.query(
        """SELECT m.mapping_id, pa.code AS a, pb.code AS b
           FROM cross_market_mapping m
           JOIN products pa ON m.product_id_a = pa.product_id
           JOIN products pb ON m.product_id_b = pb.product_id
           WHERE m.status = 'active'"""
    )
    updated = 0
    for _, row in maps.iterrows():
        sa = _product_close_series(store, row["a"])
        sb = _product_close_series(store, row["b"])
        if sa.empty or sb.empty:
            logger.warning(f"相关性跳过 {row['a']}~{row['b']}: 缺少 D1 数据")
            continue
        # 对齐到共同交易日, 取收益率
        df = pd.concat([sa.rename("a"), sb.rename("b")], axis=1).dropna()
        if len(df) < 25:
            logger.warning(f"相关性跳过 {row['a']}~{row['b']}: 重叠样本不足 ({len(df)})")
            continue
        ra, rb = df["a"].pct_change(), df["b"].pct_change()
        rr = pd.concat([ra, rb], axis=1).dropna()
        corr_20 = float(rr["a"].tail(20).corr(rr["b"].tail(20))) if len(rr) >= 20 else None
        corr_60 = float(rr["a"].tail(60).corr(rr["b"].tail(60))) if len(rr) >= 60 else None
        ll_corr, lag = _lead_lag(rr["a"], rr["b"])
        store.execute(
            """UPDATE cross_market_mapping
               SET corr_20d=?, corr_60d=?, lead_lag_corr=?, lag_days=?, updated_at=now()
               WHERE mapping_id=?""",
            [_nan(corr_20), _nan(corr_60), _nan(ll_corr), lag, int(row["mapping_id"])],
        )
        updated += 1
        logger.info(f"{row['a']}~{row['b']}: corr20={corr_20}, corr60={corr_60}, "
                    f"leadlag={ll_corr:.3f}@{lag}d")
    logger.info(f"更新 {updated} 条跨市场相关性")
    return updated


def _nan(v):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else round(v, 4)


if __name__ == "__main__":
    print("updated:", compute_all())
