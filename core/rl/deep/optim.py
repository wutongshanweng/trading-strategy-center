"""Shared gradient helpers for NumPy-based RL algorithms."""

from __future__ import annotations

import numpy as np

from .networks import TwinCritic, GaussianActor, _relu


def grad_step_q(net: dict, states: np.ndarray, actions: np.ndarray, target_q: np.ndarray, lr: float) -> None:
    """One gradient step on a single Q-network (dict of W1/b1/W2/b2).

    Args:
        net: dict with keys W1, b1, W2, b2 (numpy arrays).
        states: (batch, state_dim)
        actions: (batch, action_dim)
        target_q: (batch, 1) or (batch,) target Q-values
        lr: learning rate
    """
    sa = np.concatenate([states, actions], axis=-1)
    h = _relu(sa @ net["W1"] + net["b1"])
    q = (h @ net["W2"] + net["b2"]).squeeze(-1)
    err = q - target_q.squeeze()
    n = len(states)
    dh = (err[:, None] @ net["W2"].T) * (h > 0).astype(float)
    net["W1"] -= lr * (sa.T @ dh) / n
    net["b1"] -= lr * dh.mean(axis=0)
    net["W2"] -= lr * (h.T @ err[:, None]) / n
    net["b2"] -= lr * err.mean()


def grad_step_q_pair(critic: TwinCritic, states: np.ndarray, actions: np.ndarray, target_q: np.ndarray, lr: float) -> None:
    """Gradient step on both Q-networks of a TwinCritic."""
    grad_step_q(critic.q1, states, actions, target_q, lr)
    grad_step_q(critic.q2, states, actions, target_q, lr)


def grad_step_actor(actor: GaussianActor, critic: TwinCritic, states: np.ndarray, lr: float) -> None:
    """One gradient step on the actor to increase Q(s, pi(s))."""
    x = states.astype(np.float32)
    h = _relu(x @ actor.W1 + actor.b1)
    mean = h @ actor.W_mean + actor.b_mean
    action = np.tanh(mean)
    sa = np.concatenate([x, action], axis=-1)
    qh = _relu(sa @ critic.q1["W1"] + critic.q1["b1"])
    q_val = (qh @ critic.q1["W2"] + critic.q1["b2"]).squeeze(-1)
    dact = (1 - action ** 2)  # dtanh
    dq = q_val[:, None] * dact  # (batch, action_dim)
    n = len(states)
    actor.W_mean -= lr * (h.T @ dq) / n
    actor.b_mean -= lr * dq.mean(axis=0)


def logsumexp_clip(values: np.ndarray, clip_min: float = -50.0, clip_max: float = 50.0) -> float:
    """Numerically stable logsumexp: log(mean(exp(x))) = max(x) + log(mean(exp(x - max(x))))."""
    c = np.clip(values, clip_min, clip_max)
    max_c = np.max(c)
    return float(max_c + np.log(np.mean(np.exp(c - max_c))))
