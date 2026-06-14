"""Multi-Agent DDPG (MADDPG) — NumPy implementation."""

from __future__ import annotations

import copy
from typing import List, Dict, Any

import numpy as np

from ...deep.networks import GaussianActor, TwinCritic
from ...deep.optim import grad_step_q, grad_step_actor


class MADDPG:
    """Centralised-critic, decentralised-execution multi-agent RL."""

    def __init__(
        self,
        num_agents: int,
        state_dims: List[int],
        action_dims: List[int],
        hidden_dim: int = 256,
        gamma: float = 0.95,
        tau: float = 0.01,
        lr: float = 1e-4,
    ):
        self.num_agents = num_agents
        self.gamma = gamma
        self.tau = tau

        total_sd = sum(state_dims)
        total_ad = sum(action_dims)

        self.actors = [GaussianActor(sd, ad, hidden_dim) for sd, ad in zip(state_dims, action_dims)]
        self.t_actors = [copy.deepcopy(a) for a in self.actors]
        self.critics = [TwinCritic(total_sd, total_ad, hidden_dim) for _ in range(num_agents)]
        self.t_critics = [copy.deepcopy(c) for c in self.critics]
        self.lr = lr

        # Cache action dims for proper slicing
        self._action_dims = list(action_dims)
        self._action_starts = np.cumsum([0] + self._action_dims[:-1])

    def select_actions(self, states: List[np.ndarray]) -> List[np.ndarray]:
        actions = []
        for actor, state in zip(self.actors, states):
            x = state.reshape(1, -1).astype(np.float32)
            mean, _ = actor.forward(x)
            action = np.tanh(mean)
            actions.append(action[0])
        return actions

    def update(self, batch: Any) -> Dict[str, float]:
        states, actions, rewards, next_states, dones = batch
        s = [np.array(x, dtype=np.float32) for x in states]
        a = [np.array(x, dtype=np.float32) for x in actions]
        r = [np.array(x, dtype=np.float32).reshape(-1, 1) for x in rewards]
        ns = [np.array(x, dtype=np.float32) for x in next_states]
        d = [np.array(x, dtype=np.float32).reshape(-1, 1) for x in dones]

        all_s = np.concatenate(s, axis=1)
        all_a = np.concatenate(a, axis=1)
        all_ns = np.concatenate(ns, axis=1)

        losses: Dict[str, float] = {}
        for i in range(self.num_agents):
            # Target actions for all agents
            na_list = []
            for j, ta in enumerate(self.t_actors):
                nm, _ = ta.forward(ns[j])
                na_list.append(np.tanh(nm))
            all_na = np.concatenate(na_list, axis=1)
            tq = r[i] + self.gamma * (1 - d[i]) * self.t_critics[i].forward(all_ns, all_na)

            cq = self.critics[i].forward(all_s, all_a)
            c_loss = float(np.mean((cq - tq) ** 2))
            losses[f"critic_{i}"] = c_loss

            # Update critic weights
            grad_step_q(self.critics[i].q1, all_s, all_a, tq, self.lr)
            grad_step_q(self.critics[i].q2, all_s, all_a, tq, self.lr)

            # Actor update: build full action vector with this agent's new actions
            actor = self.actors[i]
            x = s[i].astype(np.float32)
            h = _he_forward(actor, x)
            mean = h @ actor.W_mean + actor.b_mean
            my_new_action = np.tanh(mean)

            # Replace only agent i's slice in the full action vector
            full_a_with_new = all_a.copy()
            start = int(self._action_starts[i])
            end = start + self._action_dims[i]
            full_a_with_new[:, start:end] = my_new_action

            sa = np.concatenate([all_s, full_a_with_new], axis=-1)
            qh = _relu(sa @ self.critics[i].q1["W1"] + self.critics[i].q1["b1"])
            q_val = (qh @ self.critics[i].q1["W2"] + self.critics[i].q1["b2"]).squeeze(-1)
            dact = 1 - my_new_action ** 2
            dq = q_val[:, None] * dact
            n = len(x)
            actor.W_mean -= self.lr * (h.T @ dq) / n
            actor.b_mean -= self.lr * dq.mean(axis=0)

            a_loss = float(-np.mean(q_val))
            losses[f"actor_{i}"] = a_loss

            # Soft update target networks
            self.t_actors[i] = copy.deepcopy(self.actors[i])
            self.t_critics[i] = copy.deepcopy(self.critics[i])

        return losses


def _he_forward(actor: GaussianActor, x: np.ndarray) -> np.ndarray:
    """Forward pass through actor hidden layer, returning hidden state."""
    from ...deep.networks import _relu
    return _relu(x @ actor.W1 + actor.b1)
