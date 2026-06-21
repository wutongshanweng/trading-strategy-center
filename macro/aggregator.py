"""宏观指标聚合 — 从 DuckDB macro_data 查最新值 + 趋势。

复用 data_center/data_center.db (与 macro_collector 同库, 走同一进程 get_store)。
"""

from __future__ import annotations

from typing import Dict, List

from loguru import logger

# 展示用指标 (code → 中文名/单位)
INDICATORS: List[Dict] = [
    {"code": "CPI", "name": "CPI", "unit": "%"},
    {"code": "PPI", "name": "PPI", "unit": "%"},
    {"code": "PMI", "name": "PMI", "unit": ""},
    {"code": "GDP", "name": "GDP", "unit": "%"},
    {"code": "M2", "name": "M2", "unit": "%"},
    {"code": "LPR1Y", "name": "LPR", "unit": "%"},
]


def _trend(curr: float, prev: float) -> str:
    if prev is None or curr is None:
        return "→"
    if curr > prev:
        return "↑"
    if curr < prev:
        return "↓"
    return "→"


class MacroAggregator:
    """宏观指标看板聚合器。"""

    def __init__(self, store=None):
        self._store = store

    def _get_store(self):
        if self._store is None:
            from data_center.storage.duckdb_store import get_store
            self._store = get_store()
        return self._store

    def _series(self, code: str) -> List[Dict]:
        """取单指标全序列 (date 升序)。"""
        store = self._get_store()
        df = store.query(
            """SELECT md.date, md.value FROM macro_data md
               JOIN products p ON md.product_id = p.product_id
               WHERE p.code = ? ORDER BY md.date""",
            [code.upper()],
        )
        if df is None or df.empty:
            return []
        return [{"date": str(d), "value": float(v)}
                for d, v in zip(df["date"], df["value"]) if v is not None]

    def dashboard(self) -> Dict:
        """返回 6 指标看板: 最新值 + 前值 + 趋势 + 变化 + 近 12 期迷你序列。"""
        cards: List[Dict] = []
        for ind in INDICATORS:
            series = self._series(ind["code"])
            if not series:
                cards.append({**ind, "value": None, "prev": None, "trend": "→",
                              "change": None, "date": None, "spark": [], "available": False})
                continue
            curr = series[-1]["value"]
            prev = series[-2]["value"] if len(series) >= 2 else None
            change = round(curr - prev, 3) if prev is not None else None
            spark = [p["value"] for p in series[-12:]]
            cards.append({
                **ind, "value": round(curr, 3), "prev": round(prev, 3) if prev is not None else None,
                "trend": _trend(curr, prev), "change": change,
                "date": series[-1]["date"], "spark": spark, "available": True,
            })
        return {"indicators": cards}

    def consecutive_direction(self, code: str, n: int = 3) -> Dict:
        """近 n 期连续方向 (用于远期趋势展望)。返回 {direction, periods, latest}。"""
        series = self._series(code)
        if len(series) < 2:
            return {"direction": "flat", "periods": 0, "latest": None}
        vals = [p["value"] for p in series]
        latest = vals[-1]
        ups = downs = 0
        for i in range(len(vals) - 1, 0, -1):
            if vals[i] > vals[i - 1]:
                if downs:
                    break
                ups += 1
            elif vals[i] < vals[i - 1]:
                if ups:
                    break
                downs += 1
            else:
                break
        if ups:
            return {"direction": "up", "periods": ups, "latest": round(latest, 3)}
        if downs:
            return {"direction": "down", "periods": downs, "latest": round(latest, 3)}
        return {"direction": "flat", "periods": 0, "latest": round(latest, 3)}
