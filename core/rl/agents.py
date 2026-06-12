from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger


@dataclass
class Experience:
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    log_prob: float = 0.0
    value: float = 0.0


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
        return {
            "W1": self.W1,
            "b1": self.b1,
            "W2": self.W2,
            "b2": self.b2,
        }

    def set_params(self, params: Dict[str, np.ndarray]) -> None:
        self.W1 = params["W1"]
        self.b1 = params["b1"]
        self.W2 = params["W2"]
        self.b2 = params["b2"]


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

        self.policy = SimpleNetwork(state_dim, action_dim, hidden_dim)
        self.value = SimpleNetwork(state_dim, 1, hidden_dim)

        self._buffer: List[Experience] = []
        self._update_count = 0

    @property
    def buffer_size(self) -> int:
        return len(self._buffer)

    def select_action(
        self, state: np.ndarray, training: bool = True
    ) -> Tuple[int, float, float]:
        logits = self.policy.forward(state)
        probs = self._softmax(logits)

        if training:
            action = np.random.choice(self.action_dim, p=probs)
        else:
            action = int(np.argmax(probs))

        log_prob = float(np.log(probs[action] + 1e-10))
        value = float(self.value.forward(state)[0])

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
        exp = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done,
            log_prob=log_prob,
            value=value,
        )
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

            delta = (
                rewards[t]
                + self.gamma * next_value
                - values[t]
            )
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
            advantages = (advantages - advantages.mean()) / (
                advantages.std() + 1e-8
            )

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
                    probs[np.arange(len(batch_actions)), batch_actions]
                    + 1e-10
                )

                ratio = np.exp(new_log_probs - batch_old_log_probs)
                clipped_ratio = np.clip(
                    ratio,
                    1 - self.clip_epsilon,
                    1 + self.clip_epsilon,
                )

                policy_loss = -np.minimum(
                    ratio * batch_advantages,
                    clipped_ratio * batch_advantages,
                ).mean()

                values_pred = self.value.forward(batch_states).flatten()
                value_loss = ((values_pred - batch_returns) ** 2).mean()

                entropy = -(
                    probs * np.log(probs + 1e-10)
                ).sum(axis=1).mean()

                total_policy_loss += float(policy_loss)
                total_value_loss += float(value_loss)
                total_entropy += float(entropy)
                num_updates += 1

        self._update_count += 1
        self._buffer.clear()

        avg_policy_loss = (
            total_policy_loss / num_updates if num_updates > 0 else 0.0
        )
        avg_value_loss = (
            total_value_loss / num_updates if num_updates > 0 else 0.0
        )
        avg_entropy = (
            total_entropy / num_updates if num_updates > 0 else 0.0
        )

        return {
            "policy_loss": avg_policy_loss,
            "value_loss": avg_value_loss,
            "entropy": avg_entropy,
        }

    def save(self, path: str) -> None:
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)

        policy_params = self.policy.get_params()
        value_params = self.value.get_params()

        np.savez(
            str(save_path / "model.npz"),
            **{f"policy_{k}": v for k, v in policy_params.items()},
            **{f"value_{k}": v for k, v in value_params.items()},
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
        }
        with open(save_path / "config.json", "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved model to {save_path}")

    def load(self, path: str) -> None:
        load_path = Path(path)

        with open(load_path / "config.json", "r") as f:
            config = json.load(f)

        self._update_count = config.get("update_count", 0)

        data = np.load(str(load_path / "model.npz"))

        policy_params = {
            k.replace("policy_", ""): data[f"policy_{k}"]
            for k in ["W1", "b1", "W2", "b2"]
        }
        value_params = {
            k.replace("value_", ""): data[f"value_{k}"]
            for k in ["W1", "b1", "W2", "b2"]
        }

        self.policy.set_params(policy_params)
        self.value.set_params(value_params)

        logger.info(f"Loaded model from {load_path}")

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / e_x.sum(axis=-1, keepdims=True)
