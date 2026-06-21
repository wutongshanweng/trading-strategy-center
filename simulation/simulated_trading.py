"""模拟交易服务 — 持仓/历史/关注列表的 JSON 持久化 + 盈亏计算。

数据文件 (data/):
- simulated_positions.json   当前持仓
- simulated_history.json      历史成交
- watchlist_signals.json      收藏信号
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from data_center.knowledge.contract_knowledge import ContractKnowledgeBase
from data_center.realtime_quote import get_realtime

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_POS_FILE = _DATA_DIR / "simulated_positions.json"
_HIST_FILE = _DATA_DIR / "simulated_history.json"
_WATCH_FILE = _DATA_DIR / "watchlist_signals.json"
_KB = ContractKnowledgeBase()
_LOCK = threading.Lock()


def _load(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(path: Path, data: List[Dict]) -> None:
    with _LOCK:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _multiplier(contract: str) -> int:
    sym = "".join(ch for ch in contract.upper() if ch.isalpha())
    c = _KB.get_contract(sym)
    return c.contract_multiplier if c else 1


def _name_cn(contract: str) -> str:
    sym = "".join(ch for ch in contract.upper() if ch.isalpha())
    c = _KB.get_contract(sym)
    return c.name_cn if c else sym


class SimulatedTradingService:
    """模拟交易。"""

    # ---- 持仓 ----
    def open_position(self, symbol: str, direction: str, price: float,
                      qty: int, stop_loss: float = 0.0,
                      take_profit: float = 0.0) -> Dict:
        positions = _load(_POS_FILE)
        pos = {
            "id": uuid.uuid4().hex[:12],
            "symbol": symbol.upper(),
            "product_name": _name_cn(symbol),
            "direction": direction.lower(),       # long / short
            "entry_price": float(price),
            "qty": int(qty),
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "multiplier": _multiplier(symbol),
            "open_time": datetime.now().isoformat(),
        }
        positions.append(pos)
        _save(_POS_FILE, positions)
        return pos

    def list_positions(self) -> Dict:
        """持仓 + 实时价 + 浮动盈亏。"""
        positions = _load(_POS_FILE)
        if not positions:
            return {"positions": [], "total_pnl": 0.0}
        quotes = get_realtime([p["symbol"] for p in positions])
        enriched, total = [], 0.0
        for p in positions:
            q = quotes.get(p["symbol"], {})
            cur = q.get("price") or p["entry_price"]
            mult = p.get("multiplier", 1)
            qty = p["qty"]
            if p["direction"] == "short":
                pnl = (p["entry_price"] - cur) * qty * mult
            else:
                pnl = (cur - p["entry_price"]) * qty * mult
            cost = p["entry_price"] * qty * mult
            pnl_pct = (pnl / cost * 100) if cost else 0.0
            total += pnl
            enriched.append({**p, "current_price": cur,
                             "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2),
                             "quote_source": q.get("source", "none")})
        return {"positions": enriched, "total_pnl": round(total, 2)}

    def close_position(self, pos_id: str, close_price: Optional[float] = None) -> Dict:
        positions = _load(_POS_FILE)
        target = next((p for p in positions if p["id"] == pos_id), None)
        if target is None:
            raise ValueError(f"持仓不存在: {pos_id}")
        if close_price is None:
            q = get_realtime([target["symbol"]]).get(target["symbol"], {})
            close_price = q.get("price") or target["entry_price"]
        close_price = float(close_price)
        mult, qty = target.get("multiplier", 1), target["qty"]
        if target["direction"] == "short":
            pnl = (target["entry_price"] - close_price) * qty * mult
        else:
            pnl = (close_price - target["entry_price"]) * qty * mult
        record = {**target, "close_price": close_price, "pnl": round(pnl, 2),
                  "close_time": datetime.now().isoformat()}
        history = _load(_HIST_FILE)
        history.insert(0, record)
        _save(_HIST_FILE, history)
        _save(_POS_FILE, [p for p in positions if p["id"] != pos_id])
        return record

    def history(self) -> Dict:
        return {"history": _load(_HIST_FILE)}

    # ---- 关注列表 ----
    def list_watchlist(self) -> Dict:
        return {"watchlist": _load(_WATCH_FILE)}

    def add_watchlist(self, signal: Dict) -> Dict:
        watch = _load(_WATCH_FILE)
        sid = signal.get("id")
        if sid and any(w.get("id") == sid for w in watch):
            return {"added": False, "reason": "already exists"}
        watch.insert(0, {**signal, "saved_at": datetime.now().isoformat()})
        _save(_WATCH_FILE, watch)
        return {"added": True}

    def remove_watchlist(self, sig_id: str) -> Dict:
        watch = _load(_WATCH_FILE)
        new = [w for w in watch if w.get("id") != sig_id]
        _save(_WATCH_FILE, new)
        return {"removed": len(watch) - len(new)}


# 模块级单例
_service: SimulatedTradingService | None = None


def get_service() -> SimulatedTradingService:
    global _service
    if _service is None:
        _service = SimulatedTradingService()
    return _service
