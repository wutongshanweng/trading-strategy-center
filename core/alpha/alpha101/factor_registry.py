import warnings
from typing import Dict, List, Optional, Type
from .base import AlphaFactor


class FactorRegistry:
    """Registry for alpha factor classes.

    This class maintains a registry of all alpha factor classes and provides
    methods to register, retrieve, and list factors.
    """

    _factors: Dict[str, Type[AlphaFactor]] = {}
    _names: Dict[str, str] = {}  # Maps class name to factor name
    _categories: Dict[str, str] = {}  # Maps class name to category
    _initialized: bool = False

    @classmethod
    def ensure_initialized(cls) -> None:
        """Ensure all factors are registered. Safe to call multiple times."""
        if cls._factors:
            cls._initialized = True
            return
        # Remove cached alpha factor modules (NOT factor_registry itself) so that
        # import re-executes the @register decorators using the SAME FactorRegistry class.
        import sys
        mods_to_del = [
            m for m in sys.modules
            if m.startswith("core.alpha.alpha101.") and "factor_registry" not in m
        ]
        for m in mods_to_del:
            del sys.modules[m]
        # force __init__.py to re-process imports (it finds factor_registry still cached)
        sys.modules.pop("core.alpha.alpha101", None)
        import core.alpha.alpha101  # noqa: F401 — fresh __init__ run, @register fires into *this* class
        cls._initialized = bool(cls._factors)

    @classmethod
    def reset(cls) -> None:
        """Reset registry (useful for testing)."""
        cls._factors.clear()
        cls._names.clear()
        cls._categories.clear()
        cls._initialized = False

    @classmethod
    def register(cls, factor_class: Type[AlphaFactor]):
        """Register an alpha factor class.

        Args:
            factor_class: The alpha factor class to register.

        Raises:
            Warning: If a factor with the same name is already registered.
        """
        instance = factor_class()
        if instance.name in cls._factors:
            warnings.warn(
                f"Factor '{instance.name}' is already registered. "
                f"Overwriting previous registration.",
                UserWarning,
                stacklevel=2
            )
        cls._factors[instance.name] = factor_class
        cls._names[factor_class.__name__] = instance.name
        cls._categories[instance.name] = instance.category
        cls._initialized = True
        return factor_class

    @classmethod
    def get(cls, name: str) -> Optional[Type[AlphaFactor]]:
        """Get a factor class by name.

        Args:
            name: The name of the factor to retrieve.

        Returns:
            The factor class if found, None otherwise.
        """
        return cls._factors.get(name)

    @classmethod
    def list_all(cls) -> List[str]:
        """List all registered factor names.

        Returns:
            List of all registered factor names.
        """
        return list(cls._factors.keys())

    @classmethod
    def list_by_category(cls, category: str) -> List[str]:
        """List all factor names in a given category.

        Args:
            category: The category to filter by.

        Returns:
            List of factor names in the specified category.
        """
        return [n for n, cat in cls._categories.items() if cat == category]
