"""
采集后台任务管理器 — 在 API 进程内异步运行采集 (写 DuckDB 仓库)。

为什么进程内: DuckDB 单进程独占锁, 下载与查询必须在同一个拥有 DB 的进程里。
为什么单实例: 同一时刻只允许一个采集任务, 避免写锁争用与 checkpoint 混乱。

用法:
    job = get_jobs()
    job.start("collect:RB", run_coro_factory)   # 已有任务运行中会抛 RuntimeError
    job.status()                                # 查询进度
"""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from loguru import logger


class CollectJobs:
    """进程内采集任务的单实例状态机。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._task: Optional[asyncio.Task] = None
        self._state: Dict[str, Any] = {
            "running": False, "name": None, "started_at": None,
            "finished_at": None, "result": None, "error": None,
        }

    def is_running(self) -> bool:
        return self._state["running"]

    def start(self, name: str, coro_factory: Callable[[], Any]) -> None:
        """启动一个采集任务。coro_factory 是一个返回 awaitable 的无参函数。"""
        with self._lock:
            if self._state["running"]:
                raise RuntimeError(f"已有采集任务运行中: {self._state['name']}")
            self._state.update(running=True, name=name, started_at=datetime.now().isoformat(),
                               finished_at=None, result=None, error=None)
        self._task = asyncio.create_task(self._wrap(name, coro_factory))

    async def _wrap(self, name: str, coro_factory: Callable[[], Any]) -> None:
        try:
            result = await coro_factory()
            self._state.update(result=result)
            logger.info(f"采集任务完成 [{name}]: {result}")
        except Exception as e:  # noqa: BLE001
            self._state.update(error=str(e))
            logger.error(f"采集任务失败 [{name}]: {e}")
        finally:
            self._state.update(running=False, finished_at=datetime.now().isoformat())

    def status(self) -> Dict[str, Any]:
        return dict(self._state)


_jobs: Optional[CollectJobs] = None


def get_jobs() -> CollectJobs:
    global _jobs
    if _jobs is None:
        _jobs = CollectJobs()
    return _jobs
