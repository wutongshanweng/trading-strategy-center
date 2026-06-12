from abc import ABC, abstractmethod

import pandas as pd

# Required columns for alpha factor computation
REQUIRED_COLUMNS = ['open', 'high', 'low', 'close', 'volume']


class AlphaBase(ABC):
    """Abstract base class for alpha factors.

    This class defines the interface that all alpha factors must implement.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the alpha factor."""
        raise NotImplementedError

    @property
    @abstractmethod
    def category(self) -> str:
        """Return the category of the alpha factor."""
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """Return the description of the alpha factor."""
        raise NotImplementedError

    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.Series:
        """Compute the alpha factor values.

        Args:
            data: DataFrame with OHLCV data.

        Returns:
            Series with computed factor values.
        """
        raise NotImplementedError



class AlphaFactor(ABC):
    """Abstract base class for alpha factors with validation."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the alpha factor."""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Return the category of the alpha factor."""
        pass

    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.Series:
        """Compute the alpha factor values.

        Args:
            data: DataFrame with OHLCV data.

        Returns:
            Series with computed factor values.
        """
        pass

    def validate(self, data: pd.DataFrame) -> bool:
        """Validate that the input data contains all required columns.

        Args:
            data: DataFrame to validate.

        Returns:
            True if all required columns are present, False otherwise.
        """
        return all(col in data.columns for col in REQUIRED_COLUMNS)
