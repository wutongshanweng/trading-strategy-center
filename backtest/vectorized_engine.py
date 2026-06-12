from typing import Optional, List, Dict
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from signals.base import BaseStrategy, Signal, Direction
from signals.engine import StrategyEngine


@dataclass
class BacktestResult:
    strategy_name: str = ""
    symbol: str = ""
    start_date: str = ""
    end_date: str = ""
    total_return: float = 0.0
    annualized_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    profit_factor: float = 0.0
    equity_curve: List[float] = field(default_factory=list)


class VectorizedBacktest:
    def __init__(self, initial_capital: float = 1_000_000.0, commission_pct: float = 0.0003):
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct

    def run(self, df: pd.DataFrame, strategy: BaseStrategy, symbol: str = "") -> BacktestResult:
        result = BacktestResult(strategy_name=strategy.name, symbol=symbol)
        if df.empty or len(df) < 50:
            return result

        signals = []
        for i in range(50, len(df)):
            chunk = df.iloc[:i + 1]
            sig = strategy.compute(chunk, symbol)
            if sig and sig.direction != Direction.HOLD:
                sig.timestamp = chunk.index[-1]
                signals.append(sig)

        if not signals:
            return result

        result.start_date = str(df.index[0])[:10]
        result.end_date = str(df.index[-1])[:10]

        capital = self.initial_capital
        position = 0
        entry_price = 0.0
        equity_curve = [capital]
        trades = []
        timestamps = df.index[50:]

        for i, ts in enumerate(timestamps):
            price = df.loc[ts, "close"]
            signal = next((s for s in signals if s.timestamp == ts), None)

            if signal and signal.direction == Direction.BUY and position == 0:
                position = int(capital * 0.1 / price)
                entry_price = price
                capital -= position * price * (1 + self.commission_pct)
                trades.append({"type": "BUY", "price": price, "qty": position, "ts": ts})
            elif signal and signal.direction == Direction.SELL and position > 0:
                capital += position * price * (1 - self.commission_pct)
                trades.append({"type": "SELL", "price": price, "qty": position, "pnl": (price - entry_price) * position, "ts": ts})
                position = 0

            equity = capital + position * price
            equity_curve.append(float(equity))

        if position > 0:
            final_price = df.iloc[-1]["close"]
            capital += position * final_price * (1 - self.commission_pct)

        equity_series = pd.Series(equity_curve)
        returns = equity_series.pct_change().dropna()
        total_return = (capital - self.initial_capital) / self.initial_capital

        result.total_return = round(float(total_return), 4)
        result.annualized_return = round(float(total_return * (252 / len(returns)) if len(returns) > 0 else 0), 4)
        result.sharpe_ratio = round(float(returns.mean() / returns.std() * np.sqrt(252)), 4) if len(returns) > 1 and returns.std() > 0 else 0.0

        rolling_max = equity_series.expanding().max()
        drawdowns = (equity_series - rolling_max) / rolling_max
        result.max_drawdown = round(float(drawdowns.min()), 4)

        closed_trades = [t for t in trades if "pnl" in t]
        result.total_trades = len(closed_trades)
        if closed_trades:
            wins = sum(1 for t in closed_trades if t["pnl"] > 0)
            total_pnl = sum(t["pnl"] for t in closed_trades)
            gross_profit = sum(t["pnl"] for t in closed_trades if t["pnl"] > 0)
            gross_loss = abs(sum(t["pnl"] for t in closed_trades if t["pnl"] < 0))
            result.win_rate = round(wins / len(closed_trades), 4)
            result.profit_factor = round(gross_profit / gross_loss, 4) if gross_loss > 0 else float("inf")

        result.equity_curve = [round(x, 2) for x in equity_curve]
        return result

    def compare_strategies(self, df: pd.DataFrame, strategies: List[BaseStrategy],
                           symbol: str = "") -> Dict[str, BacktestResult]:
        return {s.name: self.run(df, s, symbol) for s in strategies}
