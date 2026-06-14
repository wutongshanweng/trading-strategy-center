"""Neural network building blocks for deep RL algorithms.

Pure NumPy implementations — no PyTorch dependency required.
These are lightweight feed-forward networks suitable for
tabular / small-dimensional trading environments.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(0, x)


def _relu_grad(x: np.ndarray) -> np.ndarray:
    return (x > 0).astype(float)


def _tanh(x: np.ndarray) -> np.ndarray:
    return np.tanh(x)


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


def _he_init(fan_in: int, fan_out: int) -> np.ndarray:
    return np.random.randn(fan_in, fan_out) * np.sqrt(2.0 / fan_in)


# ---------------------------------------------------------------------------
# DQNNetwork
# ---------------------------------------------------------------------------

class DQNNetwork:
    """Simple 2-layer DQN network (NumPy)."""

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        self.W1 = _he_init(state_dim, hidden_dim)
        self.b1 = np.zeros(hidden_dim)
        self.W2 = _he_init(hidden_dim, action_dim)
        self.b2 = np.zeros(action_dim)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Return Q-values for each action."""
        self._h1 = _relu(x @ self.W1 + self.b1)
        return self._h1 @ self.W2 + self.b2

    def get_params(self) -> dict:
        return {"W1": self.W1.copy(), "b1": self.b1.copy(),
                "W2": self.W2.copy(), "b2": self.b2.copy()}

    def set_params(self, params: dict) -> None:
        self.W1 = params["W1"].copy()
        self.b1 = params["b1"].copy()
        self.W2 = params["W2"].copy()
        self.b2 = params["b2"].copy()


# ---------------------------------------------------------------------------
# GaussianActor (for SAC / TD3 / DDPG continuous action spaces)
# ---------------------------------------------------------------------------

class GaussianActor:
    """Outputs mean and log_std for a Gaussian policy (NumPy)."""

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        self.W1 = _he_init(state_dim, hidden_dim)
        self.b1 = np.zeros(hidden_dim)
        self.W_mean = _he_init(hidden_dim, action_dim)
        self.b_mean = np.zeros(action_dim)
        self.W_logstd = _he_init(hidden_dim, action_dim)
        self.b_logstd = np.zeros(action_dim)

    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Return (mean, log_std) given state batch."""
        h = _relu(x @ self.W1 + self.b1)
        mean = h @ self.W_mean + self.b_mean
        log_std = np.clip(h @ self.W_logstd + self.b_logstd, -20.0, 2.0)
        return mean, log_std

    def sample(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Sample action and log-prob via reparameterisation trick."""
        mean, log_std = self.forward(x)
        std = np.exp(log_std)
        noise = np.random.randn(*mean.shape)
        raw = mean + noise * std
        action = np.tanh(raw)
        # log π(a|s)
        log_prob = (
            -0.5 * ((raw - mean) / (std + 1e-8)) ** 2
            - log_std
            - 0.5 * np.log(2 * np.pi)
        )
        # tanh correction
        log_prob -= np.log(1 - action ** 2 + 1e-6)
        return action, log_prob.sum(axis=-1, keepdims=True)

    def get_params(self) -> dict:
        return {
            "W1": self.W1.copy(), "b1": self.b1.copy(),
            "W_mean": self.W_mean.copy(), "b_mean": self.b_mean.copy(),
            "W_logstd": self.W_logstd.copy(), "b_logstd": self.b_logstd.copy(),
        }

    def set_params(self, params: dict) -> None:
        for k, v in params.items():
            setattr(self, k, v.copy())


# ---------------------------------------------------------------------------
# TwinCritic (for SAC / TD3)
# ---------------------------------------------------------------------------

class TwinCritic:
    """Twin Q-networks, returns min(Q1, Q2) (NumPy)."""

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        self.q1 = _build_q_net(state_dim, action_dim, hidden_dim)
        self.q2 = _build_q_net(state_dim, action_dim, hidden_dim)

    def forward(self, state: np.ndarray, action: np.ndarray) -> np.ndarray:
        sa = np.concatenate([state, action], axis=-1)
        return np.minimum(_forward_q(self.q1, sa), _forward_q(self.q2, sa))

    def get_params(self) -> dict:
        return {"q1": _copy_q(self.q1), "q2": _copy_q(self.q2)}

    def set_params(self, params: dict) -> None:
        self.q1 = params["q1"]
        self.q2 = params["q2"]


def _build_q_net(s_dim: int, a_dim: int, h: int) -> dict:
    return {
        "W1": _he_init(s_dim + a_dim, h),
        "b1": np.zeros(h),
        "W2": _he_init(h, 1),
        "b2": np.zeros(1),
    }


def _forward_q(net: dict, x: np.ndarray) -> np.ndarray:
    h = _relu(x @ net["W1"] + net["b1"])
    return (h @ net["W2"] + net["b2"]).squeeze(-1)


def _copy_q(net: dict) -> dict:
    return {k: v.copy() for k, v in net.items()}
