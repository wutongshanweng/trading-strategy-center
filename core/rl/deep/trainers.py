"""DQN Trainer with experience replay and target network."""

from __future__ import annotations

import copy
import random
from typing import List

import numpy as np

from .networks import DQNNetwork
from .replay_buffer import ReplayBuffer


class DQNTrainer:
    """Deep Q-Network trainer."""

    def __init__(
        self,
        env,
        network: DQNNetwork,
        replay_buffer: ReplayBuffer,
        gamma: float = 0.99,
        eps_start: float = 1.0,
        eps_end: float = 0.01,
        eps_decay: int = 1000,
        target_update: int = 100,
        lr: float = 1e-3,
        batch_size: int = 32,
    ):
        self.env = env
        self.net = network
        self.target = copy.deepcopy(network)
        self.buf = replay_buffer
        self.gamma = gamma
        self.eps_start = eps_start
        self.eps_end = eps_end
        self.eps_decay = eps_decay
        self.target_update = target_update
        self.batch_size = batch_size
        self.steps = 0
        self.lr = lr

    def train(self, num_episodes: int = 1000, max_steps: int = 200) -> List[float]:
        rewards: List[float] = []
        for _ep in range(num_episodes):
            state = self.env.reset()
            episode_reward = 0.0
            for _step in range(max_steps):
                action = self._select_action(state)
                result = self.env.step(action)
                if len(result) == 5:
                    next_state, reward, terminated, truncated, _info = result
                    done = terminated or truncated
                else:
                    next_state, reward, done, _info = result
                self.buf.push(state, action, reward, next_state, done)
                if len(self.buf) >= self.batch_size:
                    self._update()
                if self.steps % self.target_update == 0:
                    self.target = copy.deepcopy(self.net)
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
            q = self.net.forward(state.reshape(1, -1))
            return int(np.argmax(q[0]))
        return self.env.action_space.sample() if hasattr(self.env, "action_space") else random.randint(0, 2)

    def _update(self) -> None:
        s, a, r, ns, d = self.buf.sample(self.batch_size)
        with np.errstate(divide="ignore", invalid="ignore"):
            next_q = self.target.forward(ns)
            max_next_q = np.max(next_q, axis=1)
            target_q = r + self.gamma * max_next_q * (1 - d)
        _simple_update(self.net, s, a, target_q, self.lr)


def _simple_update(net, states, actions, targets, lr):
    """Minimal gradient step for the 2-layer DQN network."""
    n = len(actions)
    h = np.maximum(0, states @ net.W1 + net.b1)  # (batch, hidden)
    q = h @ net.W2 + net.b2  # (batch, action_dim)
    q_vals = q[np.arange(n), actions]  # (batch,)
    err = q_vals - targets  # (batch,)
    # Gradient for selected actions: spread error across action_dim
    err_onehot = np.zeros_like(q)  # (batch, action_dim)
    err_onehot[np.arange(n), actions] = err
    # dW2 = h.T @ err_onehot / n -> (hidden, action_dim)
    dW2 = h.T @ err_onehot / n
    db2 = err_onehot.mean(axis=0)  # (action_dim,)
    # Backprop through ReLU
    dh = (err_onehot @ net.W2.T) * (h > 0).astype(float)  # (batch, hidden)
    dW1 = states.T @ dh / n  # (input, hidden)
    db1 = dh.mean(axis=0)  # (hidden,)
    net.W2 -= lr * dW2
    net.b2 -= lr * db2
    net.W1 -= lr * dW1
    net.b1 -= lr * db1
