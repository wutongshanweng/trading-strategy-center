"""实时行情快照 — 多源容错。

第一期优先级:
1. akshare futures_zh_realtime (纯 HTTP)
2. DuckDB kline 最新收盘价 (零外部依赖兜底, 标 source=warehouse)

2026 时钟下 akshare 实时常拉不到, 故以仓库最新收盘为可靠兜底。
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, List

from loguru import logger

from core.config.watchlist import DEFAULT_MAIN_CONTRACT
from data_center.knowledge.main_contract import MainContractResolver

_RESOLVER = MainContractResolver()
_AK = None
_AK_LOCK = threading.Lock()


def _get_ak():
    global _AK
    if _AK is None:
        with _AK_LOCK:
            if _AK is None:
                import akshare as ak
                _AK = ak
    return _AK


def _product_of(contract: str) -> str:
    try:
        parsed = _RESOLVER.parse_contract_code(contract.upper())
        return parsed.get("symbol", contract.upper())
    except Exception:
        return contract.upper()


def _from_warehouse(contract: str) -> Dict | None:
    """DuckDB kline 最近两根日线 → 价格 + 涨跌。"""
    try:
        from data_center.storage.duckdb_store import get_store
        store = get_store()
        sid = store.query("SELECT symbol_id FROM symbols WHERE code = ?", [contract.upper()])
        if sid is None or sid.empty:
            return None
        symbol_id = int(sid.iloc[0]["symbol_id"])
        df = store.query(
            """SELECT datetime, close FROM kline
               WHERE symbol_id=? AND timeframe='D1' ORDER BY datetime DESC LIMIT 2""",
            [symbol_id],
        )
        if df is None or df.empty:
            return None
        price = float(df.iloc[0]["close"])
        prev = float(df.iloc[1]["close"]) if len(df) >= 2 else price
        change = round(price - prev, 2)
        change_pct = round(change / prev * 100, 2) if prev else 0.0
        return {"price": price, "change": change, "change_pct": change_pct,
                "updated_at": str(df.iloc[0]["datetime"]), "source": "warehouse"}
    except Exception as e:
        logger.warning(f"[realtime] warehouse {contract} failed: {e}")
        return None


def _from_akshare(contract: str) -> Dict | None:
    try:
        ak = _get_ak()
        product = _product_of(contract)
        df = ak.futures_zh_realtime(symbol=product)
        if df is None or df.empty:
            return None
        row = df.iloc[-1]
        price = float(row.get("current_price") or row.get("trade") or 0) or None
        if not price:
            return None
        prev = float(row.get("pre_close") or price)
        change = round(price - prev, 2)
        return {"price": price, "change": change,
                "change_pct": round(change / prev * 100, 2) if prev else 0.0,
                "updated_at": datetime.now().isoformat(), "source": "akshare"}
    except Exception as e:
        logger.warning(f"[realtime] akshare {contract} failed: {type(e).__name__}")
        return None


def get_realtime(contracts: List[str]) -> Dict[str, Dict]:
    """批量取实时行情快照。akshare → warehouse 兜底。"""
    out: Dict[str, Dict] = {}
    for c in contracts:
        c = c.strip().upper()
        if not c:
            continue
        quote = _from_akshare(c) or _from_warehouse(c)
        if quote is None:
            # 完全无数据: 用默认合约价占位
            quote = {"price": None, "change": 0.0, "change_pct": 0.0,
                     "updated_at": datetime.now().isoformat(), "source": "none"}
        out[c] = quote
    return out
