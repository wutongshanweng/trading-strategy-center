"""期权策略注册表,镜像 signals/registry.py 的设计。"""
from typing import Dict, List, Optional, Type

from options.base import BaseOptionStrategy

_registry: Dict[str, Type[BaseOptionStrategy]] = {}


def register(cls):
    _registry[cls.strategy_name] = cls
    return cls


def get_strategy(name: str) -> Optional[Type[BaseOptionStrategy]]:
    return _registry.get(name)


def list_strategies() -> List[str]:
    return list(_registry.keys())


def get_all_strategies() -> Dict[str, Type[BaseOptionStrategy]]:
    return dict(_registry)
