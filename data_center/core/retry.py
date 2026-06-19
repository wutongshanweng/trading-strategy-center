"""
同步网络调用重试 — 应对 akshare/baostock 等同步数据源的瞬时网络中断。

用户环境网络维护期常出现 ECONNRESET / RemoteDisconnected。只对**连接类**异常
退避重试, 不对"真无数据"或参数错误重试 (避免无谓等待)。
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar

from loguru import logger

T = TypeVar("T")

# 判定为"瞬时网络问题、值得重试"的异常特征 (按异常类型名/消息匹配, 不强依赖具体库)
_TRANSIENT_HINTS = (
    "connection", "reset", "timed out", "timeout", "remotedisconnected",
    "max retries", "temporarily", "econnreset", "broken pipe", "ssl",
    "aborted", "refused",
)


def _is_transient(exc: Exception) -> bool:
    s = f"{type(exc).__name__} {exc}".lower()
    return any(h in s for h in _TRANSIENT_HINTS)


def retry_sync(fn: Callable[..., T], *args,
               attempts: int = 3, delay: float = 1.0, backoff: float = 2.0,
               **kwargs) -> T:
    """同步调用 fn(*args, **kwargs), 仅对瞬时网络异常退避重试。

    非网络异常 (参数错误等) 立即抛出, 不重试。
    重试耗尽后抛出最后一次异常 (调用方据此区分"网络失败" vs "正常无数据")。
    """
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if not _is_transient(e) or attempt == attempts:
                raise
            wait = delay * (backoff ** (attempt - 1))
            logger.warning(
                f"{getattr(fn, '__name__', fn)} 第{attempt}/{attempts}次网络失败: {e}, "
                f"{wait:.1f}s 后重试")
            time.sleep(wait)
    assert last_exc is not None
    raise last_exc
