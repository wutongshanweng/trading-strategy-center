from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class TradeState:
    balance: float
    position: float
    current_price: float
    step: int
    total_trades: int
    realized_pnl: float
    unrealized_pnl: float


class TradingEnvironment:
    def __init__(
        self,
        data: pd.DataFrame,
        initial_balance: float = 100000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.0001,
        max_position: float = 1.0,
        reward_scaling: float = 1.0,
        transaction_cost_penalty: float = 0.001,
        lookback_window: int = 60,
    ) -> None:
        self.data = data
        self.initial_balance = initial_balance
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.max_position = max_position
        self.reward_scaling = reward_scaling
        self.transaction_cost_penalty = transaction_cost_penalty
        self.lookback_window = lookback_window

        self.n_actions = 3
        self._observation_space_size = lookback_window * len(
            data.columns
        ) + 3

        self._state: Optional[TradeState] = None
        self._episode_data: Optional[pd.DataFrame] = None

    @property
    def action_space_size(self) -> int:
        return self.n_actions

    @property
    def observation_space_size(self) -> int:
        return self._observation_space_size

    def reset(self, seed: Optional[int] = None) -> np.ndarray:
        if seed is not None:
            np.random.seed(seed)

        start_idx = np.random.randint(
            self.lookback_window, len(self.data) - 1
        )
        self._episode_data = self.data.iloc[
            start_idx - self.lookback_window : start_idx + 1
        ].copy()

        self._state = TradeState(
            balance=self.initial_balance,
            position=0.0,
            current_price=float(
                self._episode_data["close"].iloc[-1]
            ),
            step=0,
            total_trades=0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
        )

        return self._get_observation()

    def step(
        self, action: int
    ) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        if self._state is None:
            raise RuntimeError("Environment not reset")

        prev_price = self._state.current_price
        self._state.step += 1

        done = self._state.step >= len(self._episode_data) - 1

        if not done:
            new_price = float(
                self._episode_data["close"].iloc[self._state.step + 1]
            )
        else:
            new_price = prev_price

        self._state.current_price = new_price

        trade_cost = 0.0
        if action == 1 and self._state.position < self.max_position:
            trade_cost = self._execute_buy()
        elif action == 2 and self._state.position > 0:
            trade_cost = self._execute_sell()

        self._state.unrealized_pnl = (
            self._state.position * (new_price - prev_price)
        )

        reward = self._calculate_reward(prev_price, new_price, trade_cost)
        obs = self._get_observation()

        info = {
            "balance": self._state.balance,
            "position": self._state.position,
            "total_trades": self._state.total_trades,
            "realized_pnl": self._state.realized_pnl,
            "unrealized_pnl": self._state.unrealized_pnl,
            "portfolio_value": self._get_portfolio_value(),
        }

        return obs, reward, done, info

    def _get_observation(self) -> np.ndarray:
        if self._state is None or self._episode_data is None:
            return np.zeros(self.observation_space_size)

        start = max(0, self._state.step - self.lookback_window + 1)
        end = self._state.step + 1
        window = self._episode_data.iloc[start:end]

        features = []
        for col in self._episode_data.columns:
            col_data = window[col].values
            if len(col_data) < self.lookback_window:
                col_data = np.pad(
                    col_data,
                    (self.lookback_window - len(col_data), 0),
                    "constant",
                )
            features.append(col_data[-self.lookback_window :])

        market_features = np.concatenate(features)

        portfolio_state = np.array(
            [
                self._state.balance / self.initial_balance,
                self._state.position / self.max_position,
                self._state.current_price
                / (self._episode_data["close"].iloc[0] + 1e-10),
            ]
        )

        observation = np.concatenate([market_features, portfolio_state])
        return observation.astype(np.float32)

    def _calculate_reward(
        self,
        prev_price: float,
        new_price: float,
        trade_cost: float,
    ) -> float:
        price_return = (new_price - prev_price) / (prev_price + 1e-10)
        position_return = self._state.position * price_return

        reward = position_return * self.reward_scaling
        reward -= trade_cost * self.transaction_cost_penalty

        return float(reward)

    def _execute_buy(self) -> float:
        if self._state is None:
            return 0.0

        price_with_slippage = self._state.current_price * (
            1 + self.slippage
        )
        affordable = self._state.balance / (
            price_with_slippage * (1 + self.commission_rate)
        )
        buy_amount = min(affordable, self.max_position - self._state.position)

        if buy_amount <= 0:
            return 0.0

        cost = buy_amount * price_with_slippage
        commission = cost * self.commission_rate

        self._state.balance -= cost + commission
        self._state.position += buy_amount
        self._state.total_trades += 1

        return commission

    def _execute_sell(self) -> float:
        if self._state is None:
            return 0.0

        price_with_slippage = self._state.current_price * (
            1 - self.slippage
        )
        sell_amount = self._state.position

        if sell_amount <= 0:
            return 0.0

        revenue = sell_amount * price_with_slippage
        commission = revenue * self.commission_rate

        pnl = revenue - commission - (
            sell_amount * self._state.current_price
        )
        self._state.realized_pnl += pnl

        self._state.balance += revenue - commission
        self._state.position = 0.0
        self._state.total_trades += 1

        return commission

    def _get_portfolio_value(self) -> float:
        if self._state is None:
            return self.initial_balance
        return self._state.balance + self._state.position * self._state.current_price
