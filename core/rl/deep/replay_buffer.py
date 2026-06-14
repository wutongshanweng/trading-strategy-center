"""Experience replay buffers for deep RL."""

from __future__ import annotations

import random
from typing import List, Optional, Tuple

import numpy as np


class ReplayBuffer:
    """Standard circular replay buffer."""

    def __init__(self, capacity: int = 100_000):
        self.capacity = capacity
        self.buffer: List[Tuple] = []
        self.pos = 0

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ) -> None:
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
        self.buffer[self.pos] = (state, action, reward, next_state, done)
        self.pos = (self.pos + 1) % self.capacity

    def sample(self, batch_size: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        batch = random.sample(self.buffer, batch_size)
        s, a, r, ns, d = zip(*batch)
        return np.array(s), np.array(a), np.array(r, dtype=np.float32), np.array(ns), np.array(d, dtype=np.float32)

    def __len__(self) -> int:
        return len(self.buffer)


class PrioritizedReplayBuffer:
    """Prioritised experience replay (Schaul et al., 2015)."""

    def __init__(self, capacity: int = 100_000, alpha: float = 0.6):
        self.capacity = capacity
        self.alpha = alpha
        self.buffer: List[Tuple] = []
        self.priorities: List[float] = []
        self.pos = 0

    def push(self, state, action, reward, next_state, done) -> None:
        mx = max(self.priorities) if self.priorities else 1.0
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
            self.priorities.append(None)
        self.buffer[self.pos] = (state, action, reward, next_state, done)
        self.priorities[self.pos] = mx
        self.pos = (self.pos + 1) % self.capacity

    def sample(self, batch_size: int, beta: float = 0.4):
        p = np.array(self.priorities[: len(self.buffer)]) ** self.alpha
        p /= p.sum()
        idx = np.random.choice(len(self.buffer), batch_size, p=p, replace=False)
        w = (len(self.buffer) * p[idx]) ** (-beta)
        w /= w.max()
        batch = [self.buffer[i] for i in idx]
        s, a, r, ns, d = zip(*batch)
        return (
            np.array(s), np.array(a), np.array(r, dtype=np.float32),
            np.array(ns), np.array(d, dtype=np.float32), idx, w.astype(np.float32),
        )

    def update_priorities(self, indices: np.ndarray, priorities: np.ndarray) -> None:
        for i, p in zip(indices, priorities):
            self.priorities[i] = float(p) + 1e-5

    def __len__(self) -> int:
        return len(self.buffer)
