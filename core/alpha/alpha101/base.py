from abc import ABC, abstractmethod

import pandas as pd


class AlphaBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def category(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.Series:
        raise NotImplementedError


class AlphaFactor(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        pass

    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.Series:
        pass

    def validate(self, data: pd.DataFrame) -> bool:
        required = ['open', 'high', 'low', 'close', 'volume']
        return all(col in data.columns for col in required)
