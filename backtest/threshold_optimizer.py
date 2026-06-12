from typing import List, Dict, Any
from itertools import product
import pandas as pd
from signals.base import BaseStrategy, Signal, Direction


class ThresholdOptimizer:
    def __init__(self, param_grid: Dict[str, List[Any]], metric: str = "sharpe_ratio"):
        self.param_grid = param_grid
        self.metric = metric
        self.results: List[Dict] = []

    def optimize(self, df: pd.DataFrame, strategy_cls: type, symbol: str = "") -> Dict[str, Any]:
        self.results = []
        keys = list(self.param_grid.keys())
        values = list(self.param_grid.values())

        for combo in product(*values):
            params = dict(zip(keys, combo))
            strategy = strategy_cls(**params)
            from backtest.vectorized_engine import VectorizedBacktest
            bt = VectorizedBacktest()
            result = bt.run(df, strategy, symbol)
            score = getattr(result, self.metric, 0.0)
            self.results.append({"params": params, self.metric: score})

        best = max(self.results, key=lambda x: x.get(self.metric, -999))
        return best
