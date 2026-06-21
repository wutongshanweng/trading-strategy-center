"""自动迭代调度 (B 阶段) — 安全的后台自动化。

只自动化"安全且可逆"的环节:
  1. 锦标赛真实回测 (刷新排名 + 回填目录, 只读评估)
  2. 参数层重优化 (贝叶斯, 存版本, 不改线上)

绝不自动化的 (保留人工闸门):
  - 晋升验证后的"毕业为 champion" (graduate 必须人工批准)
  - 真实资金分配

配置可运行时切换 (data/automation_config.json), 无需重启。
后台线程按 interval_hours 周期触发。
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from loguru import logger

_CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "automation_config.json"
_LOG_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "automation_log.json"
_lock = threading.Lock()

_DEFAULT = {
    "enabled": False,
    "interval_hours": 24,          # 多久跑一次安全周期
    "param_n_iter": 8,             # 参数层每策略优化迭代数
    "top_n_for_param": 8,          # 参数层重优化排行榜前 N
    "last_run": None,
    "next_run": None,
}


def get_config() -> Dict:
    if not _CONFIG_FILE.exists():
        return dict(_DEFAULT)
    try:
        cfg = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        return {**_DEFAULT, **cfg}
    except Exception:
        return dict(_DEFAULT)


def update_config(patch: Dict) -> Dict:
    with _lock:
        cfg = get_config()
        for k in ("enabled", "interval_hours", "param_n_iter", "top_n_for_param"):
            if k in patch and patch[k] is not None:
                cfg[k] = patch[k]
        _CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"[auto] config updated: enabled={cfg['enabled']} interval={cfg['interval_hours']}h")
    return cfg


def _append_log(entry: Dict) -> None:
    try:
        _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        log = []
        if _LOG_FILE.exists():
            log = json.loads(_LOG_FILE.read_text(encoding="utf-8"))
        log.insert(0, entry)
        _LOG_FILE.write_text(json.dumps(log[:50], ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"[auto] log persist failed: {e}")


def get_log(limit: int = 20) -> list:
    if not _LOG_FILE.exists():
        return []
    try:
        return json.loads(_LOG_FILE.read_text(encoding="utf-8"))[:limit]
    except Exception:
        return []


async def run_safe_cycle(trigger: str = "auto") -> Dict:
    """执行一次安全自动周期: 锦标赛回测 + 参数层重优化。

    异步: 调用方为后台线程时用 asyncio.run 包裹。
    返回执行摘要并写入 automation_log。
    """
    started = datetime.now()
    summary = {"trigger": trigger, "started_at": started.isoformat(),
               "tournament": None, "retrain": None, "error": None}
    try:
        # 1. 锦标赛真实回测 (刷新排名 + 回填目录)
        from tournament.tournament_runner import get_runner
        bt = await get_runner().run_and_feedback()
        summary["tournament"] = {
            "strategies_with_trades": bt.get("strategies_with_trades"),
            "top_strategy": bt.get("top_strategy"),
            "top_sharpe": bt.get("top_sharpe"),
            "retired": len(bt.get("retired", [])),
        }

        # 2. 参数层重优化 (排行榜前 N)
        cfg = get_config()
        from api.routes.tournament_routes import _manager
        board = await _manager.get_leaderboard(cfg["top_n_for_param"])
        names = [e.name for e in board]
        if names:
            from core.adaptive.retrain_orchestrator import get_orchestrator
            report = get_orchestrator().run_cycle(
                strategy_names=names, param_n_iter=cfg["param_n_iter"])
            summary["retrain"] = {"params_optimized": len(report.param_optimized)}
    except Exception as e:
        summary["error"] = f"{type(e).__name__}: {e}"
        logger.warning(f"[auto] safe cycle failed: {e}")

    summary["finished_at"] = datetime.now().isoformat()
    summary["duration_sec"] = round((datetime.now() - started).total_seconds(), 1)

    # 更新 last_run / next_run
    with _lock:
        cfg = get_config()
        cfg["last_run"] = summary["finished_at"]
        _CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    _append_log(summary)
    logger.info(f"[auto] safe cycle done ({trigger}): {summary.get('tournament')}")
    return summary


def should_run_now() -> bool:
    """后台线程判定: 已启用 且 距上次运行 ≥ interval_hours。"""
    cfg = get_config()
    if not cfg.get("enabled"):
        return False
    last = cfg.get("last_run")
    if not last:
        return True
    try:
        elapsed_h = (datetime.now() - datetime.fromisoformat(last)).total_seconds() / 3600
        return elapsed_h >= cfg.get("interval_hours", 24)
    except Exception:
        return True
