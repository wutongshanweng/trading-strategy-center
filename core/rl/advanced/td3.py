"""Twin Delayed DDPG (TD3) — NumPy implementation."""

from __future__ import annotations

import copy

import numpy as np

from ..deep.networks import GaussianActor, TwinCritic
from ..deep.optim import grad_step_q_pair, grad_step_actor


class TD3:
    """TD3 with delayed policy updates and target policy smoothing."""

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
        gamma: float = 0.99,
        tau: float = 0.005,
        policy_noise: float = 0.2,
        noise_clip: float = 0.5,
        policy_delay: int = 2,
        lr: float = 3e-4,
    ):
        self.gamma = gamma
        self.tau = tau
        self.pn = policy_noise
        self.nc = noise_clip
        self.pd = policy_delay
        self.updates = 0
        self.lr = lr

        self.actor = GaussianActor(state_dim, action_dim, hidden_dim)
        self.t_actor = copy.deepcopy(self.actor)
        self.critic = TwinCritic(state_dim, action_dim, hidden_dim)
        self.t_critic = copy.deepcopy(self.critic)

    def select_action(self, state: np.ndarray, noise: float = 0.1) -> np.ndarray:
        x = state.reshape(1, -1).astype(np.float32)
        mean, _ = self.actor.forward(x)
        action = np.tanh(mean)
        if noise > 0:
            action += np.random.randn(*action.shape) * noise
        return np.clip(action[0], -1, 1)

    def update(self, batch) -> dict:
        self.updates += 1
        s, a, r, ns, d = [np.array(x) for x in batch]
        s, a = s.astype(np.float32), a.astype(np.float32)
        r, ns, d = r.astype(np.float32), ns.astype(np.float32), d.astype(np.float32)
        r, d = r.reshape(-1, 1), d.reshape(-1, 1)

        # Target with policy smoothing
        na_mean, _ = self.t_actor.forward(ns)
        na = np.tanh(na_mean + np.clip(np.random.randn(*na_mean.shape) * self.pn, -self.nc, self.nc))
        tq = r + self.gamma * (1 - d) * self.t_critic.forward(ns, na)

        cq = self.critic.forward(s, a)
        c_loss = float(np.mean((cq - tq) ** 2) * 0.5)

        # Update critic weights
        grad_step_q_pair(self.critic, s, a, tq, self.lr)

        a_loss = 0.0
        if self.updates % self.pd == 0:
            na_mean, _ = self.actor.forward(s)
            a_loss = float(-np.mean(self.critic.forward(s, np.tanh(na_mean))))
            # Update actor weights
            grad_step_actor(self.actor, self.critic, s, self.lr)
            self.t_actor = copy.deepcopy(self.actor)
            self.t_critic = copy.deepcopy(self.critic)

        return {"critic_loss": c_loss, "actor_loss": a_loss, "updates": self.updates}
