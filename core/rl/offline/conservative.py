"""Conservative Q-Learning (CQL) for offline RL — NumPy implementation."""

from __future__ import annotations

import copy

import numpy as np

from ..deep.networks import GaussianActor, TwinCritic
from ..deep.optim import grad_step_q_pair, grad_step_actor, logsumexp_clip


class CQL:
    """CQL: conservative offline RL via Q-value lower bounding."""

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
        gamma: float = 0.99,
        tau: float = 0.005,
        alpha: float = 1.0,
        lr: float = 3e-4,
    ):
        self.gamma = gamma
        self.tau = tau
        self.alpha = alpha
        self.lr = lr

        self.actor = GaussianActor(state_dim, action_dim, hidden_dim)
        self.critic = TwinCritic(state_dim, action_dim, hidden_dim)
        self.t_critic = copy.deepcopy(self.critic)

    def select_action(self, state: np.ndarray, deterministic: bool = True) -> np.ndarray:
        x = state.reshape(1, -1).astype(np.float32)
        mean, _ = self.actor.forward(x)
        action = np.tanh(mean)
        return action[0]

    def update(self, batch) -> dict:
        s, a, r, ns, d = [np.array(x) for x in batch]
        s, a = s.astype(np.float32), a.astype(np.float32)
        r, ns, d = r.astype(np.float32), ns.astype(np.float32), d.astype(np.float32)
        r, d = r.reshape(-1, 1), d.reshape(-1, 1)

        # Target Q
        na, lp = self.actor.sample(ns)
        tq = r + self.gamma * (1 - d) * (self.t_critic.forward(ns, na) - self.alpha * lp)

        # CQL penalty on current Q using numerically stable logsumexp
        cq = self.critic.forward(s, a)
        ra = np.random.uniform(-1, 1, a.shape)
        q_rand = self.critic.forward(s, ra)
        # CQL loss = logsumexp(Q) - mean(Q_dataset)
        cql_loss = float((logsumexp_clip(q_rand) - float(np.mean(cq))) * self.alpha)

        total_loss = float(np.mean((cq - tq) ** 2)) + cql_loss

        # Actor update
        na2, lp2 = self.actor.sample(s)
        a_loss = float(-np.mean(self.critic.forward(s, na2) + self.alpha * lp2))

        # Gradient steps for critic and actor
        grad_step_q_pair(self.critic, s, a, tq, self.lr)
        grad_step_actor(self.actor, self.critic, s, self.lr)

        # Soft update
        if np.random.random() < self.tau:
            self.t_critic = copy.deepcopy(self.critic)

        return {"total_loss": total_loss, "cql_penalty": cql_loss, "actor_loss": a_loss}
