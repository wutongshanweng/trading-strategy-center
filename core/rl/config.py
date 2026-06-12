from __future__ import annotations

from typing import Any, Dict

RL_CONFIG: Dict[str, Any] = {
    "environment": {
        "initial_balance": 100000.0,
        "commission_rate": 0.001,
        "slippage": 0.0001,
        "max_position": 1.0,
        "reward_scaling": 1.0,
        "transaction_cost_penalty": 0.001,
    },
    "agent": {
        "learning_rate": 3e-4,
        "gamma": 0.99,
        "gae_lambda": 0.95,
        "clip_epsilon": 0.2,
        "entropy_coef": 0.01,
        "value_loss_coef": 0.5,
        "max_grad_norm": 0.5,
        "hidden_dim": 256,
        "num_layers": 2,
    },
    "training": {
        "num_episodes": 1000,
        "max_steps_per_episode": 500,
        "update_interval": 2048,
        "num_epochs": 10,
        "batch_size": 64,
        "eval_interval": 10,
        "save_interval": 50,
    },
    "data": {
        "lookback_window": 60,
        "feature_columns": [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "returns",
            "ma_20",
            "ma_50",
            "rsi",
            "atr",
        ],
        "normalize": True,
    },
}
