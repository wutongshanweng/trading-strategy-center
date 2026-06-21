"""交易信号聚合器 — 从各引擎收集信号, 聚合去重排序, 产出交易提醒。

数据流: DuckDB kline → StrategyEngine.compute_all → ResonanceEngineV2 → AlertSignal。
对关注品种列表全扫, 持久化到 data/alert_signals.json。
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

from core.config.watchlist import (DEFAULT_MAIN_CONTRACT, WATCHLIST_PRODUCTS,
                                   linkage_for_product)
from data_center.knowledge.contract_knowledge import ContractKnowledgeBase

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_SIGNALS_FILE = _DATA_DIR / "alert_signals.json"
_KB = ContractKnowledgeBase()


@dataclass
class AlertSignal:
    id: str
    created_at: str
    symbol: str
    product: str
    product_name: str
    direction: str            # BUY / SELL / HOLD / WATCH
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    star_rating: int
    reason: str
    source: str
    strategy_names: List[str] = field(default_factory=list)
    factor_names: List[str] = field(default_factory=list)
    detail: Dict = field(default_factory=dict)


def _main_contract(product: str) -> str:
    return DEFAULT_MAIN_CONTRACT.get(product.upper(), f"{product.upper()}2510")


def _name_cn(product: str) -> str:
    c = _KB.get_contract(product.upper())
    return c.name_cn if c else product.upper()


class AlertAggregator:
    """信号聚合器。"""

    def __init__(self, store=None):
        self._store = store
        self._lock = threading.Lock()
        self._engine = None

    def _get_store(self):
        if self._store is None:
            from data_center.storage.duckdb_store import get_store
            self._store = get_store()
        return self._store

    def _get_engine(self):
        if self._engine is None:
            from signals.engine import StrategyEngine
            eng = StrategyEngine()
            eng.load_all()
            self._engine = eng
        return self._engine

    def _load_kline(self, contract: str, timeframe: str = "D1", limit: int = 250) -> pd.DataFrame:
        """从 DuckDB 取合约 OHLCV。空则返回空 df。"""
        store = self._get_store()
        sid = store.query("SELECT symbol_id FROM symbols WHERE code = ?", [contract.upper()])
        if sid is None or sid.empty:
            return pd.DataFrame()
        symbol_id = int(sid.iloc[0]["symbol_id"])
        df = store.query(
            """SELECT datetime, open, high, low, close, volume FROM kline
               WHERE symbol_id=? AND timeframe=? ORDER BY datetime DESC LIMIT ?""",
            [symbol_id, timeframe, limit],
        )
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.sort_values("datetime").reset_index(drop=True)
        df = df.set_index("datetime")
        return df

    def _star_rating(self, n_strategies: int, confidence: float, resonance: float) -> int:
        """综合评星 1~5: 策略数 + 置信度 + 共振强度。"""
        score = 0.0
        score += min(n_strategies / 3.0, 1.0) * 2.0   # 最多 2 星
        score += confidence * 1.5                       # 最多 1.5 星
        score += min(abs(resonance) / 5.0, 1.0) * 1.5   # 最多 1.5 星
        return max(1, min(5, round(score)))

    def _scan_product(self, product: str) -> Optional[AlertSignal]:
        contract = _main_contract(product)
        df = self._load_kline(contract)
        if df.empty or len(df) < 30:
            return None
        engine = self._get_engine()
        signals = engine.compute_all(df, symbol=contract)
        if not signals:
            return None

        # 共振综合
        from core.resonance.engine_v2 import ResonanceEngineV2
        reso = ResonanceEngineV2().calculate(contract, signals, regime="RANGING")

        # 方向投票: 多数信号方向 (Direction 继承 str, 直接比较)
        buys = [s for s in signals if s.direction == "BUY"]
        sells = [s for s in signals if s.direction == "SELL"]
        if reso.direction != "HOLD":
            direction = reso.direction
        elif len(buys) > len(sells):
            direction = "BUY"
        elif len(sells) > len(buys):
            direction = "SELL"
        else:
            direction = "WATCH"

        side_signals = buys if direction == "BUY" else sells if direction == "SELL" else signals
        if not side_signals:
            side_signals = signals
        avg_conf = sum(s.confidence for s in side_signals) / len(side_signals)
        last_close = float(df["close"].iloc[-1])

        # 止盈止损 (ATR 近似: 用近 14 日波幅)
        atr = float((df["high"] - df["low"]).tail(14).mean()) if len(df) >= 14 else last_close * 0.02
        if direction == "SELL":
            entry, sl, tp = last_close, last_close + 2 * atr, last_close - 4 * atr
        else:
            entry, sl, tp = last_close, last_close - 2 * atr, last_close + 4 * atr

        strat_names = [s.strategy_name for s in side_signals][:8]
        star = self._star_rating(len(side_signals), avg_conf, reso.final_score)
        reason = side_signals[0].reason if side_signals[0].reason else f"{len(side_signals)} 个策略共振"

        sig = AlertSignal(
            id=f"{datetime.now():%Y%m%d%H%M}_{contract}_{direction}",
            created_at=datetime.now().isoformat(),
            symbol=contract, product=product.upper(), product_name=_name_cn(product),
            direction=direction, entry_price=round(entry, 2),
            stop_loss=round(sl, 2), take_profit=round(tp, 2),
            confidence=round(avg_conf, 3), star_rating=star, reason=reason,
            source="共振引擎", strategy_names=strat_names, factor_names=[],
            detail={
                "resonance": {
                    "final_score": round(reso.final_score, 3),
                    "score_G": round(reso.score_G, 3), "score_C": round(reso.score_C, 3),
                    "score_T": round(reso.score_T, 3), "confidence": round(reso.confidence, 3),
                },
                "strategies": [
                    {"name": s.strategy_name, "direction": s.direction.value,
                     "confidence": round(s.confidence, 3), "reason": s.reason}
                    for s in side_signals[:10]
                ],
                "macro_linkage": linkage_for_product(product),
                "n_total_signals": len(signals),
                "last_close": last_close, "atr14": round(atr, 2),
            },
        )
        return sig

    def run_once(self, products: List[str] | None = None) -> List[AlertSignal]:
        """一次完整信号收集周期。"""
        products = products or WATCHLIST_PRODUCTS
        out: List[AlertSignal] = []
        for p in products:
            try:
                sig = self._scan_product(p)
                if sig:
                    out.append(sig)
            except Exception as e:
                logger.warning(f"[alert] scan {p} failed: {type(e).__name__}: {e}")
        # 排序: 星级降序, 再置信度降序
        out.sort(key=lambda s: (s.star_rating, s.confidence), reverse=True)
        self._persist(out)
        logger.info(f"[alert] scan done: {len(out)} signals")
        return out

    def _persist(self, signals: List[AlertSignal]) -> None:
        with self._lock:
            _DATA_DIR.mkdir(parents=True, exist_ok=True)
            payload = {"updated_at": datetime.now().isoformat(),
                       "signals": [asdict(s) for s in signals]}
            _SIGNALS_FILE.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_active(self, limit: int = 20) -> Dict:
        """读最新信号; 无缓存则触发一次扫描。"""
        if not _SIGNALS_FILE.exists():
            self.run_once()
        try:
            payload = json.loads(_SIGNALS_FILE.read_text(encoding="utf-8"))
        except Exception:
            payload = {"updated_at": None, "signals": []}
        sigs = payload.get("signals", [])
        return {"updated_at": payload.get("updated_at"),
                "count": len(sigs[:limit]), "signals": sigs[:limit]}

    def get_by_id(self, sig_id: str) -> Optional[Dict]:
        data = self.get_active(limit=500)
        for s in data["signals"]:
            if s["id"] == sig_id:
                return s
        return None


# 模块级单例
_aggregator: AlertAggregator | None = None


def get_aggregator() -> AlertAggregator:
    global _aggregator
    if _aggregator is None:
        _aggregator = AlertAggregator()
    return _aggregator
