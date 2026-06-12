from typing import Dict, List, Optional, Type
from .base import AlphaFactor


class FactorRegistry:
    _factors: Dict[str, Type[AlphaFactor]] = {}
    _names: Dict[str, str] = {}  # Maps class name to factor name
    _categories: Dict[str, str] = {}  # Maps class name to category

    @classmethod
    def register(cls, factor_class: Type[AlphaFactor]):
        instance = factor_class()
        cls._factors[instance.name] = factor_class
        cls._names[factor_class.__name__] = instance.name
        cls._categories[instance.name] = instance.category

    @classmethod
    def get(cls, name: str) -> Optional[Type[AlphaFactor]]:
        return cls._factors.get(name)

    @classmethod
    def list_all(cls) -> List[str]:
        return list(cls._factors.keys())

    @classmethod
    def list_by_category(cls, category: str) -> List[str]:
        return [n for n, cat in cls._categories.items() if cat == category]
