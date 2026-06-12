from typing import Dict, Type, List, Optional
from signals.base import BaseStrategy

_registry: Dict[str, Type[BaseStrategy]] = {}


def register(cls):
    _registry[cls.name] = cls
    return cls


def get_strategy(name: str) -> Optional[Type[BaseStrategy]]:
    return _registry.get(name)


def list_strategies() -> List[str]:
    return list(_registry.keys())


def get_all_strategies() -> Dict[str, Type[BaseStrategy]]:
    return dict(_registry)
