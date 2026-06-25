"""Twin Delayed DDPG (TD3) — NumPy (original) + PyTorch backends.

Usage:
    agent = TD3(state_dim, action_dim, backend="torch")   # fast
    agent = TD3(state_dim, action_dim, backend="numpy")     # no deps
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

class NumpyTD3:
    """TD3 with NumPy networks and manual gradients."""

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
        from ..deep.networks import GaussianActor, TwinCritic
        from ..deep.optim import grad_step_q_pair, grad_step_actor

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

        self._grad_step_q_pair = grad_step_q_pair
        self._grad_step_actor = grad_step_actor

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

        na_mean, _ = self.t_actor.forward(ns)
        na = np.tanh(na_mean + np.clip(np.random.randn(*na_mean.shape) * self.pn, -self.nc, self.nc))
        tq = r + self.gamma * (1 - d) * self.t_critic.forward(ns, na)
        cq = self.critic.forward(s, a)
        c_loss = float(np.mean((cq - tq) ** 2) * 0.5)
        self._grad_step_q_pair(self.critic, s, a, tq, self.lr)

        a_loss = 0.0
        if self.updates % self.pd == 0:
            na_mean2, _ = self.actor.forward(s)
            a_loss = float(-np.mean(self.critic.forward(s, np.tanh(na_mean2))))
            self._grad_step_actor(self.actor, self.critic, s, self.lr)
            self.t_actor = copy.deepcopy(self.actor)
            self.t_critic = copy.deepcopy(self.critic)

        return {"critic_loss": c_loss, "actor_loss": a_loss, "updates": self.updates}


# ---------------------------------------------------------------------------
# PyTorch backend
# ---------------------------------------------------------------------------

class TorchTD3:
    """TD3 with PyTorch networks and automatic differentiation."""

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
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.actor = GaussianActorTorch(state_dim, action_dim, hidden_dim, lr=lr)
        self.target_actor = GaussianActorTorch(state_dim, action_dim, hidden_dim, lr=lr)
        self.critic = TwinCriticTorch(state_dim, action_dim, hidden_dim, lr=lr)
        self.target_critic = TwinCriticTorch(state_dim, action_dim, hidden_dim, lr=lr)
        self.target_actor.sync_from(self.actor)
        self.target_critic.sync_from(self.critic)

        self.actor.to(self._device)
        self.target_actor.to(self._device)
        self.critic.to(self._device)
        self.target_critic.to(self._device)

    def select_action(self, state: np.ndarray, noise: float = 0.1) -> np.ndarray:
        action, _ = self.actor.forward_np(state.reshape(1, -1), deterministic=True)
        if noise > 0:
            action = action[0] + np.random.randn(*action[0].shape) * noise
        return np.clip(action[0], -1, 1)

    def update(self, batch) -> dict:
        self.updates += 1
        s, a, r, ns, d = [np.array(x) for x in batch]
        s_t = torch.as_tensor(s, dtype=torch.float32, device=self._device)
        a_t = torch.as_tensor(a, dtype=torch.float32, device=self._device)
        r_t = torch.as_tensor(r, dtype=torch.float32, device=self._device).unsqueeze(1)
        ns_t = torch.as_tensor(ns, dtype=torch.float32, device=self._device)
        d_t = torch.as_tensor(d, dtype=torch.float32, device=self._device).unsqueeze(1)

        # Target policy smoothing
        with torch.no_grad():
            na_target, _ = self.target_actor.sample(ns_t)
            noise = na_target.new_empty(na_target.size()).normal_(0, self.pn).clamp(-self.nc, self.nc)
            na_target_smooth = torch.tanh(na_target + noise)
            tq = r_t + self.gamma * (1 - d_t) * self.target_critic(ns_t, na_target_smooth).unsqueeze(1)

        # Critic update
        cq = self.critic(s_t, a_t).unsqueeze(1)
        critic_loss = F.mse_loss(cq, tq)

        self.critic.optimizer.zero_grad()
        critic_loss.backward()
        self.critic.optimizer.step()

        actor_loss = 0.0
        if self.updates % self.pd == 0:
            na, _ = self.actor.sample(s_t)
            actor_loss = -torch.mean(self.critic(s_t, na))

            self.actor.optimizer.zero_grad()
            actor_loss.backward()
            self.actor.optimizer.step()

            soft_update(self.target_actor, self.actor, self.tau)
            soft_update(self.target_critic, self.critic, self.tau)
            actor_loss = float(actor_loss.item())

        return {"critic_loss": float(critic_loss.item()), "actor_loss": actor_loss, "updates": self.updates}


# ---------------------------------------------------------------------------
# Unified TD3 (backward-compatible constructor)
# ---------------------------------------------------------------------------

class TD3:
    """Twin Delayed DDPG. Backend selected by constructor or config."""

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
        backend: str = "auto",
    ):
        if backend == "auto":
            backend = "torch" if _TORCH_AVAILABLE else "numpy"

        self.backend = backend.lower()
        if self.backend == "torch" and _TORCH_AVAILABLE:
            self._impl = TorchTD3(
                state_dim, action_dim, hidden_dim, gamma, tau,
                policy_noise, noise_clip, policy_delay, lr,
            )
        else:
            self._impl = NumpyTD3(
                state_dim, action_dim, hidden_dim, gamma, tau,
                policy_noise, noise_clip, policy_delay, lr,
            )

    def select_action(self, state: np.ndarray, noise: float = 0.1) -> np.ndarray:
        return self._impl.select_action(state, noise)

    def update(self, batch) -> dict:
        return self._impl.update(batch)
