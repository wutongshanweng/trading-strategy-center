"""
种子数据加载 — 从 seeds/*.csv 初始化 products / cross_market_mapping。

幂等: 重复运行不会产生重复行 (products.code UNIQUE; mapping UNIQUE 约束)。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

from ..storage.duckdb_store import DuckDBStore, get_store

_SEEDS = Path(__file__).resolve().parent / "seeds"


def _val(v):
    """NaN -> None (DuckDB 参数化需要)。"""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return v


def load_products(store: DuckDBStore | None = None) -> int:
    store = store or get_store()
    df = pd.read_csv(_SEEDS / "products.csv", dtype=str).where(lambda x: x.notna(), None)
    n = 0
    for _, r in df.iterrows():
        mult = r.get("multiplier")
        store.execute(
            """INSERT INTO products (code, name, asset_type, exchange, sector, multiplier)
               VALUES (?,?,?,?,?,?) ON CONFLICT (code) DO NOTHING""",
            [r["code"].upper(), r["name"], r["asset_type"], _val(r.get("exchange")),
             _val(r.get("sector")), int(mult) if _val(mult) else None],
        )
        n += 1
    logger.info(f"Seeded {n} products")
    return n


def load_cross_market(store: DuckDBStore | None = None) -> int:
    store = store or get_store()
    df = pd.read_csv(_SEEDS / "cross_market_seed.csv", dtype=str)
    n = 0
    for _, r in df.iterrows():
        a = store.query("SELECT product_id, asset_type FROM products WHERE code = ?", [r["product_a"].upper()])
        b = store.query("SELECT product_id, asset_type FROM products WHERE code = ?", [r["product_b"].upper()])
        if a.empty or b.empty:
            logger.warning(f"跨市场映射跳过 (品种缺失): {r['product_a']} / {r['product_b']}")
            continue
        store.execute(
            """INSERT INTO cross_market_mapping
               (product_id_a, asset_type_a, product_id_b, asset_type_b,
                relation_type, logic_desc, direction)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT (product_id_a, product_id_b, relation_type) DO NOTHING""",
            [int(a.iloc[0]["product_id"]), a.iloc[0]["asset_type"],
             int(b.iloc[0]["product_id"]), b.iloc[0]["asset_type"],
             r["relation_type"], r["logic_desc"], r.get("direction", "bidirectional")],
        )
        n += 1
    logger.info(f"Seeded {n} cross-market mappings")
    return n


def load_all(store: DuckDBStore | None = None) -> dict:
    store = store or get_store()
    return {"products": load_products(store), "cross_market": load_cross_market(store)}


if __name__ == "__main__":
    print(load_all())
