"""PPO Agent with dual-backend support (NumPy / PyTorch).

Usage:
    # PyTorch (default, fast)
    agent = PPOAgent(state_dim, action_dim, backend="torch")

    # NumPy fallback (no dependencies)
    agent = PPOAgent(state_dim, action_dim, backend="numpy")
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

_TORCH_AVAILABLE = False
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    _TORCH_AVAILABLE = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# PyTorch networks
# ---------------------------------------------------------------------------

class TorchMLP(nn.Module if _TORCH_AVAILABLE else object):
    """Two-layer MLP for PPO policy/value heads (PyTorch)."""

    def __init__(self, input_dim: int, output_dim: int, hidden_dim: int = 256):
        if not _TORCH_AVAILABLE:
            raise ImportError("torch not installed")
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        h = F.relu(self.fc1(x))
        h = F.relu(self.fc2(h))
        return self.fc3(h)


# ---------------------------------------------------------------------------
# Experience dataclass
# ---------------------------------------------------------------------------

@dataclass
class Experience:
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    log_prob: float = 0.0
    value: float = 0.0


# ---------------------------------------------------------------------------
# NumPy SimpleNetwork (unchanged — kept for numpy backend)
# ---------------------------------------------------------------------------

class SimpleNetwork:
    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        hidden_dim: int = 256,
    ) -> None:
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.hidden_dim = hidden_dim
        scale1 = np.sqrt(2.0 / input_dim)
        scale2 = np.sqrt(2.0 / hidden_dim)
        scale3 = np.sqrt(2.0 / hidden_dim)
        self.W1 = np.random.randn(input_dim, hidden_dim) * scale1
        self.b1 = np.zeros(hidden_dim)
        self.W2 = np.random.randn(hidden_dim, output_dim) * scale2
        self.b2 = np.zeros(output_dim)

    def forward(self, x: np.ndarray) -> np.ndarray:
        h = np.maximum(0, x @ self.W1 + self.b1)
        return h @ self.W2 + self.b2

    def get_params(self) -> Dict[str, np.ndarray]:
        return {"W1": self.W1, "b1": self.b1, "W2": self.W2, "b2": self.b2}

    def set_params(self, params: Dict[str, np.ndarray]) -> None:
        self.W1 = params["W1"]
        self.b1 = params["b1"]
        self.W2 = params["W2"]
        self.b2 = params["b2"]


# ---------------------------------------------------------------------------
# PPO Agent
# ---------------------------------------------------------------------------

class PPOAgent:
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        entropy_coef: float = 0.01,
        value_loss_coef: float = 0.5,
        max_grad_norm: float = 0.5,
        backend: str = "torch",
    ) -> None:
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.entropy_coef = entropy_coef
        self.value_loss_coef = value_loss_coef
        self.max_grad_norm = max_grad_norm
        self.backend = backend.lower() if _TORCH_AVAILABLE else "numpy"

        # Build networks
        if self.backend == "torch" and _TORCH_AVAILABLE:
            self.policy = TorchMLP(state_dim, action_dim, hidden_dim)
            self.value_net = TorchMLP(state_dim, 1, hidden_dim)
            self.policy_optimizer = optim.Adam(self.policy.parameters(), lr=learning_rate)
            self.value_optimizer = optim.Adam(self.value_net.parameters(), lr=learning_rate)
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.policy.to(self._device)
            self.value_net.to(self._device)
        else:
            self.policy = SimpleNetwork(state_dim, action_dim, hidden_dim)
            self.value_net = SimpleNetwork(state_dim, 1, hidden_dim)

        self._buffer: List[Experience] = []
        self._update_count = 0

    @property
    def buffer_size(self) -> int:
        return len(self._buffer)

    def select_action(
        self, state: np.ndarray, training: bool = True
    ) -> Tuple[int, float, float]:
        if self.backend == "torch" and _TORCH_AVAILABLE:
            return self._torch_select_action(state, training)
        else:
            return self._numpy_select_action(state, training)

    def _numpy_select_action(self, state: np.ndarray, training: bool) -> Tuple[int, float, float]:
        logits = self.policy.forward(state)
        probs = self._softmax(logits)
        if training:
            action = np.random.choice(self.action_dim, p=probs)
        else:
            action = int(np.argmax(probs))
        log_prob = float(np.log(probs[action] + 1e-10))
        value = float(self.value_net.forward(state)[0])
        return action, log_prob, value

    def _torch_select_action(self, state: np.ndarray, training: bool) -> Tuple[int, float, float]:
        with torch.no_grad():
            t = torch.as_tensor(state, dtype=torch.float32, device=self._device).unsqueeze(0)
            logits = self.policy(t)
            probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]
            if training:
                action = np.random.choice(self.action_dim, p=probs)
            else:
                action = int(np.argmax(probs))
            log_prob = float(np.log(probs[action] + 1e-10))
            value = float(self.value_net(t).cpu().numpy()[0, 0])
        return action, log_prob, value

    def store_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        log_prob: float = 0.0,
        value: float = 0.0,
    ) -> None:
        exp = Experience(state, action, reward, next_state, done, log_prob, value)
        self._buffer.append(exp)

    def compute_gae(
        self, rewards: List[float], values: List[float], dones: List[bool]
    ) -> Tuple[List[float], List[float]]:
        gae = 0.0
        advantages = []
        returns = []
        next_value = 0.0
        for t in reversed(range(len(rewards))):
            if dones[t]:
                next_value = 0.0
                gae = 0.0
            delta = rewards[t] + self.gamma * next_value - values[t]
            gae = delta + self.gamma * self.gae_lambda * gae
            advantages.insert(0, gae)
            returns.insert(0, gae + values[t])
            next_value = values[t]
        return advantages, returns

    def update(
        self,
        num_epochs: int = 10,
        batch_size: int = 64,
    ) -> Dict[str, float]:
        if len(self._buffer) < batch_size:
            return {"policy_loss": 0.0, "value_loss": 0.0, "entropy": 0.0}

        if self.backend == "torch" and _TORCH_AVAILABLE:
            return self._torch_update(num_epochs, batch_size)
        else:
            return self._numpy_update(num_epochs, batch_size)

    def _numpy_update(self, num_epochs: int, batch_size: int) -> Dict[str, float]:
        states = np.array([e.state for e in self._buffer])
        actions = np.array([e.action for e in self._buffer])
        old_log_probs = np.array([e.log_prob for e in self._buffer])
        rewards = [e.reward for e in self._buffer]
        values = [e.value for e in self._buffer]
        dones = [e.done for e in self._buffer]

        advantages, returns = self.compute_gae(rewards, values, dones)
        advantages = np.array(advantages)
        returns = np.array(returns)
        if len(advantages) > 1:
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        indices = np.arange(len(states))
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0
        num_updates = 0

        for _ in range(num_epochs):
            np.random.shuffle(indices)
            for start in range(0, len(indices), batch_size):
                end = start + batch_size
                batch_idx = indices[start:end]
                batch_states = states[batch_idx]
                batch_actions = actions[batch_idx]
                batch_old_log_probs = old_log_probs[batch_idx]
                batch_advantages = advantages[batch_idx]
                batch_returns = returns[batch_idx]

                logits = self.policy.forward(batch_states)
                probs = self._softmax(logits)
                new_log_probs = np.log(
                    probs[np.arange(len(batch_actions)), batch_actions] + 1e-10
                )

                ratio = np.exp(new_log_probs - batch_old_log_probs)
                clipped_ratio = np.clip(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon)
                policy_loss = -np.minimum(
                    ratio * batch_advantages, clipped_ratio * batch_advantages
                ).mean()

                values_pred = self.value_net.forward(batch_states).flatten()
                value_loss = ((values_pred - batch_returns) ** 2).mean()
                entropy = -(probs * np.log(probs + 1e-10)).sum(axis=1).mean()

                total_policy_loss += float(policy_loss)
                total_value_loss += float(value_loss)
                total_entropy += float(entropy)
                num_updates += 1

        self._update_count += 1
        self._buffer.clear()

        return {
            "policy_loss": total_policy_loss / max(num_updates, 1),
            "value_loss": total_value_loss / max(num_updates, 1),
            "entropy": total_entropy / max(num_updates, 1),
        }

    def _torch_update(self, num_epochs: int, batch_size: int) -> Dict[str, float]:
        states = torch.as_tensor(
            np.array([e.state for e in self._buffer]), dtype=torch.float32, device=self._device
        )
        actions = torch.as_tensor(
            np.array([e.action for e in self._buffer]), dtype=torch.long, device=self._device
        )
        old_log_probs = torch.as_tensor(
            np.array([e.log_prob for e in self._buffer]), dtype=torch.float32, device=self._device
        )
        rewards_np = [e.reward for e in self._buffer]
        values_np = [e.value for e in self._buffer]
        dones_np = [e.done for e in self._buffer]

        advantages, returns = self.compute_gae(rewards_np, values_np, dones_np)
        advantages_t = torch.as_tensor(advantages, dtype=torch.float32, device=self._device)
        returns_t = torch.as_tensor(returns, dtype=torch.float32, device=self._device)
        if len(advantages) > 1:
            advantages_t = (advantages_t - advantages_t.mean()) / (advantages_t.std() + 1e-8)

        indices = torch.arange(len(states), device=self._device)
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0
        num_updates = 0

        for _ in range(num_epochs):
            perm = indices[torch.randperm(len(indices))]
            for start in range(0, len(indices), batch_size):
                end = start + batch_size
                batch_idx = perm[start:end]
                s = states[batch_idx]
                a = actions[batch_idx]
                old_lp = old_log_probs[batch_idx]
                adv = advantages_t[batch_idx]
                ret = returns_t[batch_idx]

                logits = self.policy(s)
                log_probs = torch.log_softmax(logits, dim=-1)
                new_log_probs = log_probs.gather(1, a.unsqueeze(1)).squeeze(1)
                probs = torch.softmax(logits, dim=-1)

                ratio = torch.exp(new_log_probs - old_lp)
                clipped = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon)
                policy_loss = -torch.min(ratio * adv, clipped * adv).mean()

                values_pred = self.value_net(s).squeeze(1)
                value_loss = F.mse_loss(values_pred, ret)

                entropy = -(probs * log_probs).sum(dim=-1).mean()

                self.policy_optimizer.zero_grad()
                self.value_optimizer.zero_grad()
                loss = policy_loss + self.value_loss_coef * value_loss - self.entropy_coef * entropy
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
                torch.nn.utils.clip_grad_norm_(self.value_net.parameters(), self.max_grad_norm)
                self.policy_optimizer.step()
                self.value_optimizer.step()

                total_policy_loss += float(policy_loss.item())
                total_value_loss += float(value_loss.item())
                total_entropy += float(entropy.item())
                num_updates += 1

        self._update_count += 1
        self._buffer.clear()

        return {
            "policy_loss": total_policy_loss / max(num_updates, 1),
            "value_loss": total_value_loss / max(num_updates, 1),
            "entropy": total_entropy / max(num_updates, 1),
        }

    def save(self, path: str) -> None:
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)

        if self.backend == "torch" and _TORCH_AVAILABLE:
            torch.save(self.policy.state_dict(), save_path / "policy.pt")
            torch.save(self.value_net.state_dict(), save_path / "value.pt")
        else:
            np.savez(
                str(save_path / "model.npz"),
                **{f"policy_{k}": v for k, v in self.policy.get_params().items()},
                **{f"value_{k}": v for k, v in self.value_net.get_params().items()},
            )

        config = {
            "state_dim": self.state_dim,
            "action_dim": self.action_dim,
            "hidden_dim": self.hidden_dim,
            "learning_rate": self.learning_rate,
            "gamma": self.gamma,
            "gae_lambda": self.gae_lambda,
            "clip_epsilon": self.clip_epsilon,
            "entropy_coef": self.entropy_coef,
            "value_loss_coef": self.value_loss_coef,
            "max_grad_norm": self.max_grad_norm,
            "update_count": self._update_count,
            "backend": self.backend,
        }
        with open(save_path / "config.json", "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved PPO model to {save_path} (backend={self.backend})")

    def load(self, path: str) -> None:
        load_path = Path(path)
        with open(load_path / "config.json", "r") as f:
            config = json.load(f)
        self._update_count = config.get("update_count", 0)

        if self.backend == "torch" and _TORCH_AVAILABLE:
            self.policy.load_state_dict(torch.load(load_path / "policy.pt", map_location=self._device))
            self.value_net.load_state_dict(torch.load(load_path / "value.pt", map_location=self._device))
        else:
            data = np.load(str(load_path / "model.npz"))
            policy_params = {k: data[k] for k in data.files}
            self.policy.set_params(policy_params)
            value_params = {k: data[k] for k in data.files}
            self.value_net.set_params(value_params)
        logger.info(f"Loaded PPO model from {load_path}")

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / e_x.sum(axis=-1, keepdims=True)
