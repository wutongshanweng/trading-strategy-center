"""Soft Actor-Critic (SAC) — NumPy implementation."""

from __future__ import annotations

import copy

import numpy as np

from ..deep.networks import GaussianActor, TwinCritic
from ..deep.optim import grad_step_q_pair, grad_step_actor


class SAC:
    """SAC with automatic entropy tuning."""

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
        gamma: float = 0.99,
        tau: float = 0.005,
        alpha: float = 0.2,
        lr: float = 3e-4,
    ):
        self.gamma = gamma
        self.tau = tau
        self.alpha = alpha

        self.actor = GaussianActor(state_dim, action_dim, hidden_dim)
        self.critic = TwinCritic(state_dim, action_dim, hidden_dim)
        self.target_critic = copy.deepcopy(self.critic)

        self.target_entropy = -float(action_dim)
        self.log_alpha = np.array([np.log(alpha)])
        self.lr = lr

    def select_action(self, state: np.ndarray, deterministic: bool = False) -> np.ndarray:
        x = state.reshape(1, -1).astype(np.float32)
        mean, log_std = self.actor.forward(x)
        if deterministic:
            action = np.tanh(mean)
        else:
            std = np.exp(np.clip(log_std, -5, 2))
            raw = mean + np.random.randn(*mean.shape) * std
            action = np.tanh(raw)
        return action[0]

    def update(self, batch) -> dict:
        s, a, r, ns, d = [np.array(x) for x in batch]
        s, a = s.astype(np.float32), a.astype(np.float32)
        r, ns, d = r.astype(np.float32), ns.astype(np.float32), d.astype(np.float32)
        r, d = r.reshape(-1, 1), d.reshape(-1, 1)

        # Target Q
        na, lp = self.actor.sample(ns)
        tq = r + self.gamma * (1 - d) * (self.target_critic.forward(ns, na) - self.alpha * lp)

        # Critic loss
        cq = self.critic.forward(s, a)
        c_loss = float(np.mean((cq - tq) ** 2) * 0.5)

        # Actor loss
        na2, lp2 = self.actor.sample(s)
        a_loss = float(-np.mean(self.critic.forward(s, na2) + self.alpha * lp2))

        # Alpha loss: correct SAC entropy temperature gradient
        # d(alpha)/d(log_alpha) = alpha * (log_pi + target_entropy).mean()
        # But since log_alpha is log(alpha), the gradient of the objective w.r.t. log_alpha is:
        #   -alpha * (log_pi + target_entropy).mean()
        alpha_grad = -float(np.mean(lp2 + self.target_entropy))
        self.log_alpha += self.lr * self.alpha * alpha_grad
        self.alpha = float(np.exp(self.log_alpha[0]))

        # Gradient steps
        grad_step_q_pair(self.critic, s, a, tq, self.lr)
        grad_step_actor(self.actor, self.critic, s, self.lr)

        # Soft update target critic
        self.target_critic = copy.deepcopy(self.critic)

        return {
            "critic_loss": c_loss,
            "actor_loss": a_loss,
            "alpha_loss": alpha_grad,
            "alpha": float(self.alpha),
        }
