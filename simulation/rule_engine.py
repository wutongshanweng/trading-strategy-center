from typing import List, Callable, Awaitable
from signals.base import Signal


class RuleEngine:
    def __init__(self):
        self._rules: List[Callable[[Signal], Awaitable[bool]]] = []

    def add_rule(self, rule: Callable[[Signal], Awaitable[bool]]):
        self._rules.append(rule)

    async def check(self, signal: Signal) -> bool:
        for rule in self._rules:
            if not await rule(signal):
                return False
        return True

    async def check_all(self, signals: List[Signal]) -> List[Signal]:
        return [s for s in signals if await self.check(s)]


async def min_confidence_rule(min_conf: float = 0.3):
    async def rule(signal: Signal) -> bool:
        return signal.confidence >= min_conf
    return rule


async def direction_filter_rule(allowed: List[str] = None):
    async def rule(signal: Signal) -> bool:
        if allowed is None:
            return True
        return signal.direction.value in allowed
    return rule
