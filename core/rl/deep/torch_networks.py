"""PyTorch neural network building blocks for deep RL algorithms.

Wraps torch.nn.Module for automatic differentiation + Adam optimizer.
Falls back gracefully if torch is not installed.

Usage:
    from core.rl.deep.torch_networks import DQNTorchNet, GaussianActorTorch, TwinCriticTorch
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

# Optional torch dependency
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    torch = nn = F = optim = None  # type: ignore


# ---------------------------------------------------------------------------
# Device helper
# ---------------------------------------------------------------------------

def _device() -> Optional["torch.device"]:
    """Return best available device (cuda > mps > cpu)."""
    if not _TORCH_AVAILABLE:
        return None
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


# ---------------------------------------------------------------------------
# DQNTorchNet — PyTorch DQN
# ---------------------------------------------------------------------------

class DQNTorchNet(nn.Module if _TORCH_AVAILABLE else object):
    """Two-layer DQN with PyTorch autograd."""

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128,
        lr: float = 1e-3,
    ):
        if not _TORCH_AVAILABLE:
            raise ImportError("torch not installed — install with: pip install torch")
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, action_dim)
        self.optimizer = optim.Adam(self.parameters(), lr=lr)
        self._to_device()

    def _to_device(self):
        if _TORCH_AVAILABLE:
            self.to(_device())

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        h = F.relu(self.fc1(x))
        return self.fc2(h)

    def forward_np(self, x: np.ndarray) -> np.ndarray:
        """NumPy input → NumPy output (no gradient)."""
        t = torch.as_tensor(x, dtype=torch.float32, device=_device())
        with torch.no_grad():
            out = self.forward(t)
        return out.cpu().numpy()

    def update(self, states: np.ndarray, actions: np.ndarray, targets: np.ndarray) -> float:
        """One gradient step, returns loss value."""
        s = torch.as_tensor(states, dtype=torch.float32, device=_device())
        a = torch.as_tensor(actions, dtype=torch.long, device=_device())
        tgt = torch.as_tensor(targets, dtype=torch.float32, device=_device())

        q_vals = self.forward(s)
        q_selected = q_vals.gather(1, a.unsqueeze(1)).squeeze(1)
        loss = F.smooth_l1_loss(q_selected, tgt)

        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.parameters(), 10.0)
        self.optimizer.step()
        return loss.item()

    def sync_from(self, source: "DQNTorchNet") -> None:
        """Copy parameters from source network (target network sync)."""
        self.load_state_dict(source.state_dict())


# ---------------------------------------------------------------------------
# GaussianActorTorch — continuous policy (SAC / TD3 / DDPG)
# ---------------------------------------------------------------------------

class GaussianActorTorch(nn.Module if _TORCH_AVAILABLE else object):
    """Mean + log_std Gaussian policy with tanh squashing (PyTorch)."""

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
        lr: float = 3e-4,
        log_std_min: float = -20.0,
        log_std_max: float = 2.0,
    ):
        if not _TORCH_AVAILABLE:
            raise ImportError("torch not installed")
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc_mean = nn.Linear(hidden_dim, action_dim)
        self.fc_logstd = nn.Linear(hidden_dim, action_dim)
        self.log_std_min = log_std_min
        self.log_std_max = log_std_max
        self.optimizer = optim.Adam(self.parameters(), lr=lr)
        self._to_device()

    def _to_device(self):
        if _TORCH_AVAILABLE:
            self.to(_device())

    def forward(self, x: "torch.Tensor") -> Tuple["torch.Tensor", "torch.Tensor"]:
        h = F.relu(self.fc1(x))
        mean = self.fc_mean(h)
        log_std = torch.clamp(self.fc_logstd(h), self.log_std_min, self.log_std_max)
        return mean, log_std

    def sample(self, x: "torch.Tensor") -> Tuple["torch.Tensor", "torch.Tensor"]:
        """Reparameterised sample + log-prob (tanh correction)."""
        mean, log_std = self.forward(x)
        std = log_std.exp()
        noise = torch.randn_like(mean)
        raw = mean + noise * std
        action = torch.tanh(raw)
        # log π(a|s) with tanh correction
        log_prob = (
            -0.5 * ((raw - mean) / (std + 1e-8)) ** 2
            - log_std
            - 0.5 * np.log(2 * np.pi)
        )
        log_prob = (log_prob - torch.log(1 - action ** 2 + 1e-6)).sum(dim=-1, keepdim=True)
        return action, log_prob

    def forward_np(self, x: np.ndarray, deterministic: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """NumPy input → (action, log_std)."""
        t = torch.as_tensor(x, dtype=torch.float32, device=_device())
        with torch.no_grad():
            mean, log_std = self.forward(t)
            if deterministic:
                action = torch.tanh(mean)
            else:
                std = log_std.exp()
                action = torch.tanh(mean + torch.randn_like(mean) * std)
        return action.cpu().numpy(), log_std.cpu().numpy()


# ---------------------------------------------------------------------------
# TwinCriticTorch — twin Q-networks with min
# ---------------------------------------------------------------------------

class TwinCriticTorch(nn.Module if _TORCH_AVAILABLE else object):
    """Two Q-networks; forward returns min(Q1, Q2)."""

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
        lr: float = 3e-4,
    ):
        if not _TORCH_AVAILABLE:
            raise ImportError("torch not installed")
        super().__init__()
        # Q1
        self.fc1_q1 = nn.Linear(state_dim + action_dim, hidden_dim)
        self.fc2_q1 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3_q1 = nn.Linear(hidden_dim, 1)
        # Q2
        self.fc1_q2 = nn.Linear(state_dim + action_dim, hidden_dim)
        self.fc2_q2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3_q2 = nn.Linear(hidden_dim, 1)

        self.optimizer = optim.Adam(self.parameters(), lr=lr)
        self._to_device()

    def _to_device(self):
        if _TORCH_AVAILABLE:
            self.to(_device())

    def _q_forward(self, sa: "torch.Tensor", path: int) -> "torch.Tensor":
        if path == 0:
            h = F.relu(self.fc1_q1(sa))
            h = F.relu(self.fc2_q1(h))
            return self.fc3_q1(h).squeeze(-1)
        else:
            h = F.relu(self.fc1_q2(sa))
            h = F.relu(self.fc2_q2(h))
            return self.fc3_q2(h).squeeze(-1)

    def forward(self, state: "torch.Tensor", action: "torch.Tensor") -> "torch.Tensor":
        sa = torch.cat([state, action], dim=-1)
        return torch.min(self._q_forward(sa, 0), self._q_forward(sa, 1))

    def forward_np(self, state: np.ndarray, action: np.ndarray) -> np.ndarray:
        """NumPy input → min Q-value (no grad)."""
        s = torch.as_tensor(state, dtype=torch.float32, device=_device())
        a = torch.as_tensor(action, dtype=torch.float32, device=_device())
        with torch.no_grad():
            return self.forward(s, a).cpu().numpy()

    def update_critic(
        self,
        state: np.ndarray,
        action: np.ndarray,
        target: np.ndarray,
    ) -> float:
        """One gradient step on both Q-nets, returns critic loss."""
        s = torch.as_tensor(state, dtype=torch.float32, device=_device())
        a = torch.as_tensor(action, dtype=torch.float32, device=_device())
        tgt = torch.as_tensor(target, dtype=torch.float32, device=_device())

        sa = torch.cat([s, a], dim=-1)
        q1 = self._q_forward(sa, 0)
        q2 = self._q_forward(sa, 1)
        loss = F.smooth_l1_loss(q1, tgt) + F.smooth_l1_loss(q2, tgt)

        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.parameters(), 10.0)
        self.optimizer.step()
        return loss.item()

    def sync_from(self, source: "TwinCriticTorch") -> None:
        self.load_state_dict(source.state_dict())


# ---------------------------------------------------------------------------
# SoftUpdate — polyak averaging for target networks
# ---------------------------------------------------------------------------

def soft_update(target: nn.Module, source: nn.Module, tau: float = 0.005) -> None:
    """Polyak averaging: target ← τ * source + (1 - τ) * target."""
    with torch.no_grad():
        for tp, sp in zip(target.parameters(), source.parameters()):
            tp.data.mul_(1.0 - tau)
            tp.data.add_(tau * sp.data)


def hard_update(target: nn.Module, source: nn.Module) -> None:
    """Hard copy: target ← source."""
    target.load_state_dict(source.state_dict())
