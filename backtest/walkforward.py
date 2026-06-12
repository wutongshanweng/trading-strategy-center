from typing import List, Dict
import pandas as pd
from backtest.vectorized_engine import VectorizedBacktest, BacktestResult
from signals.base import BaseStrategy


class WalkForward:
    def __init__(self, window_train: int = 252, window_test: int = 63):
        self.window_train = window_train
        self.window_test = window_test

    def run(self, df: pd.DataFrame, strategy: BaseStrategy, symbol: str = "") -> List[BacktestResult]:
        results = []
        total = len(df)
        start = self.window_train + self.window_test
        while start <= total:
            train_df = df.iloc[start - self.window_train - self.window_test: start - self.window_test]
            test_df = df.iloc[start - self.window_test: start]
            if len(train_df) < self.window_train or len(test_df) < self.window_test // 2:
                break
            bt = VectorizedBacktest()
            result = bt.run(test_df, strategy, symbol)
            result.strategy_name = f"{strategy.name}_wf_{start}"
            results.append(result)
            start += self.window_test
        return results
