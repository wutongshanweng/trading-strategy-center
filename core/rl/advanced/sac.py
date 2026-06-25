"""Soft Actor-Critic (SAC) — NumPy (original) + PyTorch backends.

Usage:
    # PyTorch (default, fast)
    agent = SAC(state_dim, action_dim, backend="torch")

    # NumPy fallback (no torch dependency)
    agent = SAC(state_dim, action_dim, backend="numpy")
"""

from __future__ import annotations

import copy

import numpy as np

_TORCH_AVAILABLE = False
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    from .torch_networks import GaussianActorTorch, TwinCriticTorch, soft_update
    _TORCH_AVAILABLE = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# NumPy backend
# ---------------------------------------------------------------------------

class NumpySAC:
    """SAC with NumPy networks and manual gradients."""

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
        from ..deep.networks import GaussianActor, TwinCritic
        from ..deep.optim import grad_step_q_pair, grad_step_actor

        self.gamma = gamma
        self.tau = tau
        self.alpha = alpha
        self.lr = lr

        self.actor = GaussianActor(state_dim, action_dim, hidden_dim)
        self.critic = TwinCritic(state_dim, action_dim, hidden_dim)
        self.target_critic = copy.deepcopy(self.critic)
        self.target_entropy = -float(action_dim)
        self.log_alpha = np.array([np.log(alpha)])

        self._grad_step_q_pair = grad_step_q_pair
        self._grad_step_actor = grad_step_actor

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

        na, lp = self.actor.sample(ns)
        tq = r + self.gamma * (1 - d) * (self.target_critic.forward(ns, na) - self.alpha * lp)
        cq = self.critic.forward(s, a)
        c_loss = float(np.mean((cq - tq) ** 2) * 0.5)

        na2, lp2 = self.actor.sample(s)
        a_loss = float(-np.mean(self.critic.forward(s, na2) + self.alpha * lp2))

        alpha_grad = -float(np.mean(lp2 + self.target_entropy))
        self.log_alpha += self.lr * self.alpha * alpha_grad
        self.alpha = float(np.exp(self.log_alpha[0]))

        self._grad_step_q_pair(self.critic, s, a, tq, self.lr)
        self._grad_step_actor(self.actor, self.critic, s, self.lr)
        self.target_critic = copy.deepcopy(self.critic)

        return {"critic_loss": c_loss, "actor_loss": a_loss, "alpha": self.alpha}


# ---------------------------------------------------------------------------
# PyTorch backend
# ---------------------------------------------------------------------------

class TorchSAC:
    """SAC with PyTorch networks and automatic differentiation."""

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
        self.lr = lr
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.actor = GaussianActorTorch(state_dim, action_dim, hidden_dim, lr=lr)
        self.critic = TwinCriticTorch(state_dim, action_dim, hidden_dim, lr=lr)
        self.target_critic = TwinCriticTorch(state_dim, action_dim, hidden_dim, lr=lr)
        self.target_critic.sync_from(self.critic)

        self.target_entropy = -float(action_dim)
        self.log_alpha = nn.Parameter(torch.tensor([np.log(alpha)], device=self._device))
        self.alpha_optimizer = optim.Adam([self.log_alpha], lr=lr)

        self.actor.to(self._device)
        self.critic.to(self._device)
        self.target_critic.to(self._device)

    def select_action(self, state: np.ndarray, deterministic: bool = False) -> np.ndarray:
        action, _ = self.actor.forward_np(state.reshape(1, -1), deterministic=deterministic)
        return action[0]

    def update(self, batch) -> dict:
        s, a, r, ns, d = [np.array(x) for x in batch]
        s_t = torch.as_tensor(s, dtype=torch.float32, device=self._device)
        a_t = torch.as_tensor(a, dtype=torch.float32, device=self._device)
        r_t = torch.as_tensor(r, dtype=torch.float32, device=self._device).unsqueeze(1)
        ns_t = torch.as_tensor(ns, dtype=torch.float32, device=self._device)
        d_t = torch.as_tensor(d, dtype=torch.float32, device=self._device).unsqueeze(1)

        # Target Q
        with torch.no_grad():
            na_target, lp_target = self.actor.sample(ns_t)
            tq = r_t + self.gamma * (1 - d_t) * (
                self.target_critic(ns_t, na_target) - self.alpha * lp_target
            )

        # Critic update
        cq = self.critic(s_t, a_t)
        critic_loss = F.mse_loss(cq, tq.squeeze(1))

        self.critic.optimizer.zero_grad()
        critic_loss.backward()
        self.critic.optimizer.step()

        # Actor update
        na, lp = self.actor.sample(s_t)
        actor_loss = -torch.mean(self.critic(s_t, na) + self.alpha * lp)

        self.actor.optimizer.zero_grad()
        actor_loss.backward()
        self.actor.optimizer.step()

        # Alpha update
        alpha_loss = -torch.mean(lp.detach() + self.target_entropy) * self.alpha
        self.alpha_optimizer.zero_grad()
        alpha_loss.backward()
        self.alpha_optimizer.step()
        self.alpha = float(np.exp(self.log_alpha.item()))

        # Soft update target
        soft_update(self.target_critic, self.critic, self.tau)

        return {
            "critic_loss": float(critic_loss.item()),
            "actor_loss": float(actor_loss.item()),
            "alpha": self.alpha,
        }


# ---------------------------------------------------------------------------
# Unified SAC (backward-compatible constructor)
# ---------------------------------------------------------------------------

def _numpy_available():
    try:
        from ..deep.networks import GaussianActor, TwinCritic
        from ..deep.optim import grad_step_q_pair, grad_step_actor
        return True
    except ImportError:
        return False


class SAC:
    """Soft Actor-Critic. Backend selected by constructor or config."""

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
        gamma: float = 0.99,
        tau: float = 0.005,
        alpha: float = 0.2,
        lr: float = 3e-4,
        backend: str = "auto",
    ):
        if backend == "auto":
            backend = "torch" if _TORCH_AVAILABLE else "numpy"

        self.backend = backend.lower()
        if self.backend == "torch" and _TORCH_AVAILABLE:
            self._impl = TorchSAC(state_dim, action_dim, hidden_dim, gamma, tau, alpha, lr)
        else:
            self._impl = NumpySAC(state_dim, action_dim, hidden_dim, gamma, tau, alpha, lr)

    def select_action(self, state: np.ndarray, deterministic: bool = False) -> np.ndarray:
        return self._impl.select_action(state, deterministic)

    def update(self, batch) -> dict:
        return self._impl.update(batch)
