"""Offline dataset management for CQL."""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np


class OfflineDataset:
    """Load and sample from a pre-collected offline dataset."""

    def __init__(self, data_path: Optional[str] = None):
        if data_path:
            data = np.load(data_path)
            self.states = data["states"]
            self.actions = data["actions"]
            self.rewards = data["rewards"]
            self.next_states = data["next_states"]
            self.dones = data["dones"]
        else:
            self.states = np.empty((0, 0))
            self.actions = np.empty((0, 0))
            self.rewards = np.empty(0)
            self.next_states = np.empty((0, 0))
            self.dones = np.empty(0)

    @property
    def size(self) -> int:
        return len(self.rewards)

    def sample(self, batch_size: int) -> Tuple:
        idx = np.random.choice(self.size, min(batch_size, self.size), replace=False)
        return (
            self.states[idx], self.actions[idx], self.rewards[idx],
            self.next_states[idx], self.dones[idx],
        )

    def get_stats(self) -> dict:
        return {
            "size": self.size,
            "state_dim": self.states.shape[1] if self.states.ndim > 1 else 0,
            "action_dim": self.actions.shape[1] if self.actions.ndim > 1 else 0,
            "reward_mean": float(np.mean(self.rewards)) if self.size > 0 else 0.0,
            "reward_std": float(np.std(self.rewards)) if self.size > 0 else 0.0,
        }
