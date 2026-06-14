from typing import List, Optional, Dict, Type
from loguru import logger
import pandas as pd

from signals.base import BaseStrategy, Signal, Direction
from signals.registry import get_all_strategies


class StrategyEngine:
    def __init__(self):
        self._strategies: Dict[str, BaseStrategy] = {}

    def load_all(self):
        # 导入策略包触发自动注册(@register),再从注册表实例化
        import signals.strategies  # noqa: F401
        for name, cls in get_all_strategies().items():
            self._strategies[name] = cls()
        logger.info(f"Loaded {len(self._strategies)} strategies")

    def register(self, strategy: BaseStrategy):
        self._strategies[strategy.name] = strategy

    def get(self, name: str) -> Optional[BaseStrategy]:
        return self._strategies.get(name)

    def compute_all(self, df: pd.DataFrame, symbol: str = "",
                    filter_names: List[str] = None) -> List[Signal]:
        results = []
        names = filter_names or list(self._strategies.keys())
        for name in names:
            strategy = self._strategies.get(name)
            if strategy is None:
                continue
            try:
                signal = strategy.compute(df, symbol)
                if signal and signal.direction != Direction.HOLD:
                    signal.strategy_name = name
                    results.append(signal)
            except Exception as e:
                logger.error(f"Strategy {name} failed: {e}")
        return results

    def compute_named(self, name: str, df: pd.DataFrame,
                      symbol: str = "") -> Optional[Signal]:
        strategy = self._strategies.get(name)
        if strategy is None:
            logger.warning(f"Strategy {name} not found")
            return None
        try:
            return strategy.compute(df, symbol)
        except Exception as e:
            logger.error(f"Strategy {name} failed: {e}")
            return None

    @property
    def count(self) -> int:
        return len(self._strategies)
