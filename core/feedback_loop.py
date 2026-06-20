"""
反馈闭环 — 锦标赛结果 → 策略目录表现更新 / 下线 / (可选)ML 重训。

设计为解耦: process_tournament_results 接收通用 results dict
(不绑定某套 tournament 实现), 形如:
    {"id": "...", "strategies": [
        {"name": "trend_ma_cross", "sharpe": 1.2, "win_rate": 0.55,
         "total_trades": 40, "max_drawdown": 0.08, "symbol": "RB2510"}, ...]}

流程:
  1. 逐策略更新 StrategyCatalog 表现 (sharpe/win_rate/...)
  2. 夏普过低且交易数足够 → 标记下线 (可选 is_active=False)
  3. 汇总 top/worst → 写入反馈历史
  4. (可选) 触发 ML 重训

用法:
    loop = FeedbackLoop()
    entry = loop.process_tournament_results(results)
    loop.get_history(limit=10)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from core.feedback_config import FeedbackConfig


@dataclass
class FeedbackEntry:
    """一次反馈记录。"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tournament_id: str = ""
    n_strategies: int = 0
    top_strategy: str = ""
    top_sharpe: float = 0.0
    worst_strategy: str = ""
    worst_sharpe: float = 0.0
    strategies_retired: List[str] = field(default_factory=list)
    strategies_starred: List[str] = field(default_factory=list)
    models_retrained: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


class FeedbackLoop:
    """反馈闭环 — 锦标赛 → 策略/ML。"""

    def __init__(
        self,
        catalog=None,
        config: Optional[FeedbackConfig] = None,
        ml_pipeline=None,
        store_path: Optional[str] = None,
    ):
        # catalog 默认用全局单例
        if catalog is None:
            from signals.catalog import get_catalog
            catalog = get_catalog()
        self.catalog = catalog
        self.config = config or FeedbackConfig()
        self.ml_pipeline = ml_pipeline
        self.store_path = Path(
            store_path or os.path.join("data", "feedback_log.json"))
        self.history: List[FeedbackEntry] = []
        self._load_history()

    def _load_history(self) -> None:
        """从 JSON 恢复反馈历史。"""
        if not self.store_path.exists():
            return
        try:
            with open(self.store_path, encoding="utf-8") as f:
                data = json.load(f)
            self.history = [FeedbackEntry(**e) for e in data]
        except Exception as e:  # noqa: BLE001
            logger.warning(f"反馈历史读取失败: {e}")

    def _save_history(self) -> None:
        """持久化反馈历史到 JSON。"""
        try:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in self.history], f,
                          ensure_ascii=False, indent=2)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"反馈历史持久化失败: {e}")

    def process_tournament_results(self, results: Dict) -> FeedbackEntry:
        """处理锦标赛结果, 回填策略目录并生成反馈记录。"""
        cfg = self.config
        strategies = results.get("strategies", [])
        entry = FeedbackEntry(tournament_id=str(results.get("id", "")),
                              n_strategies=len(strategies))
        best_sharpe, worst_sharpe = float("-inf"), float("inf")

        for sr in strategies:
            name = sr.get("name", "")
            sharpe = float(sr.get("sharpe", 0.0))
            win_rate = float(sr.get("win_rate", 0.0))
            trades = int(sr.get("total_trades", 0))
            mdd = sr.get("max_drawdown")
            symbol = sr.get("symbol")

            # 1. 更新目录
            self.catalog.update_performance(
                name, sharpe=sharpe, win_rate=win_rate,
                max_drawdown=float(mdd) if mdd is not None else None,
                total_trades=trades, symbol=symbol)

            # 2. 下线判定
            if sharpe < cfg.retire_sharpe and trades >= cfg.retire_min_trades:
                entry.strategies_retired.append(name)
                if cfg.deactivate_on_retire:
                    self.catalog.update_performance(name, is_active=False)
                logger.warning(f"策略 {name} 持续失效 (夏普{sharpe:.2f}), 已标记下线")

            # 3. 明星判定
            if sharpe >= cfg.star_sharpe:
                entry.strategies_starred.append(name)

            if sharpe > best_sharpe:
                best_sharpe, entry.top_strategy = sharpe, name
            if sharpe < worst_sharpe:
                worst_sharpe, entry.worst_strategy = sharpe, name

        if strategies:
            entry.top_sharpe = best_sharpe if best_sharpe != float("-inf") else 0.0
            entry.worst_sharpe = worst_sharpe if worst_sharpe != float("inf") else 0.0

        # 4. 可选 ML 重训
        if cfg.retrain_on_decay and self.ml_pipeline is not None:
            symbols = {sr.get("symbol") for sr in strategies if sr.get("symbol")}
            for sym in symbols:
                try:
                    self.ml_pipeline.run(sym)
                    entry.models_retrained += 1
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"ML 重训 {sym} 失败: {e}")

        self.history.append(entry)
        self._save_history()
        logger.info(f"反馈处理完成: top={entry.top_strategy}({entry.top_sharpe:.2f}) "
                    f"下线={len(entry.strategies_retired)} 明星={len(entry.strategies_starred)}")
        return entry

    def get_strategy_rankings(self, min_trades: int = 0) -> List[Dict]:
        """获取目录中策略表现排名 (经锦标赛回填后)。"""
        metas = [m for m in self.catalog.all() if m.total_trades >= min_trades]
        metas.sort(key=lambda m: m.sharpe, reverse=True)
        return [m.to_dict() for m in metas]

    def get_history(self, limit: int = 20) -> List[FeedbackEntry]:
        return self.history[-limit:]


_loop: Optional[FeedbackLoop] = None


def get_feedback_loop() -> FeedbackLoop:
    """全局反馈闭环单例。"""
    global _loop
    if _loop is None:
        _loop = FeedbackLoop()
    return _loop
