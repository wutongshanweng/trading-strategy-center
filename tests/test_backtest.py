import pytest
import pandas as pd
import numpy as np
from backtest.vectorized_engine import VectorizedBacktest, BacktestResult
from signals.base import BaseStrategy, Signal, Direction


class BuyStrat(BaseStrategy):
    name = "test_buy"
    description = ""
    def compute(self, df, symbol=""):
        return Signal(symbol=symbol, direction=Direction.BUY, confidence=1.0, price=float(df["close"].iloc[-1]))


@pytest.fixture
def df():
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=200, freq="D")
    price = 100.0
    prices = [price := price * (1 + np.random.normal(0.0005, 0.01)) for _ in range(200)]
    return pd.DataFrame({"open": [p * 0.99 for p in prices], "high": [p * 1.015 for p in prices],
                          "low": [p * 0.985 for p in prices], "close": prices, "volume": np.random.randint(1000, 10000, 200)}, index=dates)


class TestBacktest:
    def test_run_returns_result(self, df):
        r = VectorizedBacktest().run(df, BuyStrat(), "TEST")
        assert isinstance(r, BacktestResult)
        assert r.strategy_name == "test_buy"

    def test_fields(self, df):
        r = VectorizedBacktest().run(df, BuyStrat(), "TEST")
        assert hasattr(r, "total_return") and hasattr(r, "sharpe_ratio")
        assert hasattr(r, "max_drawdown") and hasattr(r, "total_trades")
