"""DQN Trainer — PyTorch backend (primary) with NumPy fallback.

backend="torch"   → PyTorch (requires: pip install torch)
backend="numpy"   → pure NumPy (no dependencies)
"""

from __future__ import annotations

import copy
import random
from typing import List

import numpy as np

from .replay_buffer import ReplayBuffer

_TORCH_AVAILABLE = False
try:
    from .torch_networks import DQNTorchNet
    _TORCH_AVAILABLE = True
except ImportError:
    pass


class DQNTrainer:
    """Deep Q-Network trainer with dual-backend support."""

    def __init__(
        self,
        env,
        state_dim: int,
        action_dim: int,
        backend: str = "torch",
        hidden_dim: int = 128,
        gamma: float = 0.99,
        eps_start: float = 1.0,
        eps_end: float = 0.01,
        eps_decay: int = 1000,
        target_update: int = 100,
        lr: float = 1e-3,
        batch_size: int = 32,
    ):
        self.env = env
        self.gamma = gamma
        self.eps_start = eps_start
        self.eps_end = eps_end
        self.eps_decay = eps_decay
        self.target_update = target_update
        self.batch_size = batch_size
        self.steps = 0
        self.lr = lr
        self.backend = backend.lower()

        if self.backend == "torch" and _TORCH_AVAILABLE:
            self.net = DQNTorchNet(state_dim, action_dim, hidden_dim, lr=lr)
            self.target = DQNTorchNet(state_dim, action_dim, hidden_dim, lr=lr)
            self.target.sync_from(self.net)
        else:
            from .networks import DQNNetwork
            self.net = DQNNetwork(state_dim, action_dim, hidden_dim)
            self.target = copy.deepcopy(self.net)

        self.buf = ReplayBuffer()

    def train(self, num_episodes: int = 1000, max_steps: int = 200) -> List[float]:
        rewards: List[float] = []
        for _ in range(num_episodes):
            state = self.env.reset()
            episode_reward = 0.0
            for _ in range(max_steps):
                action = self._select_action(state)
                result = self.env.step(action)
                if len(result) == 5:
                    next_state, reward, terminated, truncated, _ = result
                    done = terminated or truncated
                else:
                    next_state, reward, done, _ = result
                self.buf.push(state, action, reward, next_state, done)
                if len(self.buf) >= self.batch_size:
                    self._update()
                if self.steps % self.target_update == 0:
                    self._sync_target()
                state = next_state
                episode_reward += reward
                self.steps += 1
                if done:
                    break
            rewards.append(episode_reward)
        return rewards

    def _select_action(self, state: np.ndarray) -> int:
        eps = self.eps_end + (self.eps_start - self.eps_end) * np.exp(
            -self.steps / max(self.eps_decay, 1)
        )
        if random.random() > eps:
            if self.backend == "torch" and _TORCH_AVAILABLE:
                q = self.net.forward_np(state.reshape(1, -1))
            else:
                q = self.net.forward(state.reshape(1, -1))
            return int(np.argmax(q[0]))
        return self.env.action_space.sample() if hasattr(self.env, "action_space") else random.randint(0, 2)

    def _update(self) -> None:
        s, a, r, ns, d = self.buf.sample(self.batch_size)
        with np.errstate(divide="ignore", invalid="ignore"):
            if self.backend == "torch" and _TORCH_AVAILABLE:
                next_q = self.target.forward_np(ns)
            else:
                next_q = self.target.forward(ns)
            max_next_q = np.max(next_q, axis=1)
            target_q = r + self.gamma * max_next_q * (1 - d)

        if self.backend == "torch" and _TORCH_AVAILABLE:
            self.net.update(s, a.astype(np.int64), target_q.astype(np.float32))
        else:
            self._numpy_update(s, a, target_q)

    def _numpy_update(self, s, a, targets) -> None:
        lr = self.lr
        h = np.maximum(0, s @ self.net.W1 + self.net.b1)
        q = h @ self.net.W2 + self.net.b2
        q_vals = q[np.arange(len(a)), a]
        err = q_vals - targets
        err_onehot = np.zeros_like(q)
        err_onehot[np.arange(len(a)), a] = err
        dW2 = h.T @ err_onehot / len(a)
        db2 = err_onehot.mean(axis=0)
        dh = (err_onehot @ self.net.W2.T) * (h > 0).astype(float)
        dW1 = s.T @ dh / len(a)
        db1 = dh.mean(axis=0)
        self.net.W2 -= lr * dW2
        self.net.b2 -= lr * db2
        self.net.W1 -= lr * dW1
        self.net.b1 -= lr * db1

    def _sync_target(self) -> None:
        if self.backend == "torch" and _TORCH_AVAILABLE:
            self.target.sync_from(self.net)
        else:
            self.target = copy.deepcopy(self.net)
