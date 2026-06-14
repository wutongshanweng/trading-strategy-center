"""Real-time metrics collector."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class MetricsCollector:
    """Collect and query system / strategy metrics."""

    def __init__(self):
        self._collectors: Dict[str, Callable[[], Any]] = {}
        self._metrics: Dict[str, Any] = {}

    def register(self, name: str, fn: Callable[[], Any]) -> None:
        self._collectors[name] = fn

    def collect(self) -> Dict[str, Any]:
        for name, fn in self._collectors.items():
            try:
                self._metrics[name] = fn()
            except Exception as exc:  # noqa: BLE001
                self._metrics[name] = None
        return self._metrics.copy()

    def get(self, name: str) -> Optional[Any]:
        return self._metrics.get(name)

    def get_all(self) -> Dict[str, Any]:
        return self._metrics.copy()
