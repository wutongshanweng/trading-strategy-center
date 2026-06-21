from typing import List, Dict, Optional
from dataclasses import dataclass, field
import asyncio
import json
from pathlib import Path
import numpy as np
from tournament.scoring import calculate_composite_score

_STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "tournament_state.json"


@dataclass
class StrategyEntry:
    name: str
    current_score: float = 0.0
    trades: int = 0
    win_rate: float = 0.0
    sharpe: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    rank: int = 0
    total_return: float = 0.0
    pnls: List[float] = field(default_factory=list)


class TournamentManager:
    def __init__(self):
        self._entries: Dict[str, StrategyEntry] = {}
        self._lock = asyncio.Lock()
        self._load()

    async def register_strategy(self, name: str):
        async with self._lock:
            if name not in self._entries:
                self._entries[name] = StrategyEntry(name=name)

    async def record_trade(self, name: str, pnl: float):
        async with self._lock:
            if name not in self._entries:
                self._entries[name] = StrategyEntry(name=name)
            entry = self._entries[name]
            entry.pnls.append(pnl)
            entry.trades = len(entry.pnls)
            wins = sum(1 for p in entry.pnls if p > 0)
            entry.win_rate = wins / entry.trades if entry.trades > 0 else 0.0
            if entry.trades >= 2:
                arr = np.array(entry.pnls)
                entry.sharpe = float(arr.mean() / arr.std() * np.sqrt(252)) if arr.std() > 0 else 0.0
                gross_profit = sum(p for p in entry.pnls if p > 0)
                gross_loss = abs(sum(p for p in entry.pnls if p < 0))
                entry.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    async def record_result(self, name: str, sharpe: float, win_rate: float,
                            profit_factor: float, max_drawdown: float,
                            total_trades: int, total_return: float = 0.0):
        """直接写入回测聚合绩效 (供真实回测编排, 非逐笔)。"""
        async with self._lock:
            entry = self._entries.get(name) or StrategyEntry(name=name)
            entry.sharpe = sharpe
            entry.win_rate = win_rate
            entry.profit_factor = profit_factor
            entry.max_drawdown = max_drawdown
            entry.trades = total_trades
            entry.total_return = total_return
            self._entries[name] = entry
        self._save()


    async def update_scores(self):
        async with self._lock:
            for entry in self._entries.values():
                stats = {"sharpe": entry.sharpe, "win_rate": entry.win_rate,
                         "profit_factor": entry.profit_factor if entry.profit_factor != float("inf") else 10,
                         "max_drawdown": entry.max_drawdown, "trade_count": entry.trades}
                entry.current_score = calculate_composite_score(stats)
            ranked = sorted(self._entries.values(), key=lambda e: e.current_score, reverse=True)
            for i, entry in enumerate(ranked):
                entry.rank = i + 1

    async def get_leaderboard(self, top_n: int = 10) -> List[StrategyEntry]:
        await self.update_scores()
        async with self._lock:
            return sorted(self._entries.values(), key=lambda e: e.current_score, reverse=True)[:top_n]

    async def eliminate_bottom(self, pct: float = 0.1):
        async with self._lock:
            await self.update_scores()
            sorted_entries = sorted(self._entries.values(), key=lambda e: e.current_score)
            n_eliminate = max(1, int(len(sorted_entries) * pct))
            for entry in sorted_entries[:n_eliminate]:
                del self._entries[entry.name]

    async def get_tournament_summary(self) -> Dict:
        await self.update_scores()
        async with self._lock:
            scores = [e.current_score for e in self._entries.values()]
            return {
                "total_strategies": len(self._entries),
                "avg_score": sum(scores) / len(scores) if scores else 0.0,
                "max_score": max(scores) if scores else 0.0,
                "min_score": min(scores) if scores else 0.0,
            }

    # ---- 持久化 (data/tournament_state.json) ----
    def _save(self) -> None:
        try:
            _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            payload = [
                {"name": e.name, "current_score": e.current_score, "trades": e.trades,
                 "win_rate": e.win_rate, "sharpe": e.sharpe, "profit_factor": e.profit_factor,
                 "max_drawdown": e.max_drawdown, "rank": e.rank,
                 "total_return": e.total_return, "pnls": e.pnls}
                for e in self._entries.values()
            ]
            _STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load(self) -> None:
        if not _STATE_FILE.exists():
            return
        try:
            data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
            for d in data:
                pf = d.get("profit_factor", 0.0)
                self._entries[d["name"]] = StrategyEntry(
                    name=d["name"], current_score=d.get("current_score", 0.0),
                    trades=d.get("trades", 0), win_rate=d.get("win_rate", 0.0),
                    sharpe=d.get("sharpe", 0.0),
                    profit_factor=float("inf") if pf is None else pf,
                    max_drawdown=d.get("max_drawdown", 0.0), rank=d.get("rank", 0),
                    total_return=d.get("total_return", 0.0), pnls=d.get("pnls", []))
        except Exception:
            pass
