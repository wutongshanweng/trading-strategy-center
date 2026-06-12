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
