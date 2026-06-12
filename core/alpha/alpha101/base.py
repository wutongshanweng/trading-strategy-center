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
