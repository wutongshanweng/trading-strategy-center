"""API routes for intelligence upgrade: RL, risk monitoring, monitoring."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])


# ---- Request / Response Models ----

class VaRRequest(BaseModel):
    returns: List[float]
    confidence: float = 0.95
    method: str = "historical"


class StressTestRequest(BaseModel):
    portfolio: Dict[str, Dict[str, float]]


class KellyRequest(BaseModel):
    win_rate: float
    win_loss_ratio: float
    fraction: Optional[float] = None


class AlertRuleRequest(BaseModel):
    name: str
    metric: str
    threshold: float
    direction: str = "above"
    severity: str = "warning"


class RLStatusResponse(BaseModel):
    algorithms: List[str]
    status: str


class ComputeFactorsRequest(BaseModel):
    factor_names: List[str]
    n_rows: int = 100
    data: Optional[Dict[str, List[float]]] = None


class AlertCheckRequest(BaseModel):
    metrics: Dict[str, float]
    rules: Optional[List[AlertRuleRequest]] = None


# ---- VaR / CVaR Routes ----

@router.post("/risk/var")
def calculate_var(req: VaRRequest) -> Dict[str, Any]:
    from core.risk.monitoring.var_calculator import VaRCalculator
    returns = pd.Series(req.returns)
    calc = VaRCalculator(confidence=req.confidence)
    if req.method == "parametric":
        var = calc.parametric(returns)
    elif req.method == "monte_carlo":
        var = calc.monte_carlo(returns)
    else:
        var = calc.historical(returns)
    return {"var": var, "confidence": req.confidence, "method": req.method}


@router.post("/risk/cvar")
def calculate_cvar(req: VaRRequest) -> Dict[str, Any]:
    from core.risk.monitoring.cvar_calculator import CVaRCalculator
    returns = pd.Series(req.returns)
    calc = CVaRCalculator(confidence=req.confidence)
    cvar = calc.calculate(returns)
    return {"cvar": cvar, "confidence": req.confidence}


# ---- Stress Testing ----

@router.post("/risk/stress-test")
def stress_test(req: StressTestRequest) -> Dict[str, Any]:
    from core.risk.monitoring.stress_testing import StressTesting
    st = StressTesting(req.portfolio)
    scenarios = st.hypothetical_scenarios()
    return {"scenarios": scenarios}


@router.post("/risk/reverse-stress-test")
def reverse_stress_test(req: StressTestRequest, threshold: float = 0.05) -> Dict[str, Any]:
    from core.risk.monitoring.stress_testing import StressTesting
    st = StressTesting(req.portfolio)
    scenarios = st.reverse_stress_test(threshold)
    return {"scenarios": scenarios, "threshold": threshold}


# ---- Kelly / Position Sizing ----

@router.post("/risk/kelly")
def kelly_sizing(req: KellyRequest) -> Dict[str, Any]:
    from core.risk.position.kelly_criterion import KellyCriterion
    k = KellyCriterion()
    full = k.calculate(req.win_rate, req.win_loss_ratio)
    frac = k.fractional(req.win_rate, req.win_loss_ratio, req.fraction or 0.5)
    return {"full_kelly": full, "fractional_kelly": frac}


# ---- RL Algorithms ----

@router.get("/rl/algorithms")
def list_rl_algorithms() -> RLStatusResponse:
    return RLStatusResponse(
        algorithms=["PPO", "DQN", "SAC", "TD3", "DDPG", "MADDPG", "CQL"],
        status="available",
    )


@router.post("/rl/dqn/train")
def train_dqn(
    state_dim: int = 20,
    action_dim: int = 5,
    num_episodes: int = 10,
) -> Dict[str, Any]:
    from core.rl.deep.networks import DQNNetwork
    from core.rl.deep.replay_buffer import ReplayBuffer
    from core.rl.deep.trainers import DQNTrainer

    class _Env:
        def __init__(self):
            self.action_space = type("A", (), {"n": action_dim, "sample": lambda self: np.random.randint(action_dim)})()
        def reset(self): return np.random.randn(state_dim).astype(np.float32)
        def step(self, a): return np.random.randn(state_dim).astype(np.float32), np.random.randn(), np.random.random() > 0.95, False, {}

    env = _Env()
    net = DQNNetwork(state_dim, action_dim, 64)
    buf = ReplayBuffer(1000)
    trainer = DQNTrainer(env, net, buf, eps_decay=100, batch_size=16)
    rewards = trainer.train(num_episodes=num_episodes, max_steps=50)
    return {"rewards": rewards, "mean_reward": float(np.mean(rewards))}


# ---- Monitoring ----

_monitor_store: Dict[str, Any] = {}
_alert_rules: Optional[object] = None


def _get_alert_rules():
    """Get or create persistent alert rules."""
    global _alert_rules
    if _alert_rules is None:
        from monitoring.alerting.threshold_rules import ThresholdRules
        _alert_rules = ThresholdRules()
        # Add sensible default rules
        _alert_rules.add_rule("high_cpu", "cpu", 80, "above", "warning")
        _alert_rules.add_rule("low_memory", "memory", 20, "below", "critical")
        _alert_rules.add_rule("high_latency", "latency", 500, "above", "warning")
    return _alert_rules


@router.post("/monitoring/collect")
def collect_metrics() -> Dict[str, Any]:
    from monitoring.dashboard.metrics_collector import MetricsCollector
    mc = MetricsCollector()
    mc.register("system_status", lambda: "healthy")
    mc.register("num_strategies", lambda: 14)
    mc.register("uptime_hours", lambda: 24.5)
    metrics = mc.collect()
    _monitor_store.update(metrics)
    return metrics


@router.get("/monitoring/metrics")
def get_metrics() -> Dict[str, Any]:
    return _monitor_store


@router.post("/monitoring/alerts/rules")
def add_alert_rule(req: AlertRuleRequest) -> Dict[str, Any]:
    tr = _get_alert_rules()
    tr.add_rule(req.name, req.metric, req.threshold, req.direction, req.severity)
    return {"rule_added": req.name, "status": "active"}


@router.get("/monitoring/alerts/rules")
def list_alert_rules() -> Dict[str, Any]:
    tr = _get_alert_rules()
    rules = [{"name": r["name"], "metric": r["metric"], "threshold": r["threshold"],
              "direction": r["direction"], "severity": r["severity"]}
             for r in tr.rules]
    return {"rules": rules, "count": len(rules)}


@router.post("/monitoring/alerts/check")
def check_alerts(req: AlertCheckRequest) -> Dict[str, Any]:
    """Check metrics against alert rules.

    If custom rules are provided in the request, use those.
    Otherwise, use the persistent rules configured via /alerts/rules.
    """
    from monitoring.alerting.threshold_rules import ThresholdRules

    if req.rules:
        tr = ThresholdRules()
        for rule in req.rules:
            tr.add_rule(rule.name, rule.metric, rule.threshold, rule.direction, rule.severity)
    else:
        tr = _get_alert_rules()

    alerts = tr.evaluate(req.metrics)
    return {"alerts": alerts, "count": len(alerts)}


# ---- Factor Pipeline ----

@router.get("/alpha/factors")
def list_alpha_factors() -> Dict[str, Any]:
    from core.alpha.alpha101.factor_registry import FactorRegistry
    FactorRegistry.ensure_initialized()
    factors = FactorRegistry.list_all()
    return {"factors": factors, "count": len(factors)}


@router.post("/alpha/compute")
def compute_factors(req: ComputeFactorsRequest) -> Dict[str, Any]:
    """Compute alpha factors.

    If real OHLCV data is provided in req.data, use it.
    Otherwise, generates demo data for testing.
    """
    from core.alpha.alpha101.factor_registry import FactorRegistry
    FactorRegistry.ensure_initialized()
    from core.alpha.alpha101.factor_pipeline import FactorPipeline

    if req.data and all(k in req.data for k in ("open", "high", "low", "close", "volume")):
        data = pd.DataFrame({k: np.array(v, dtype=np.float64) for k, v in req.data.items()})
    else:
        np.random.seed(42)
        n = req.n_rows
        data = pd.DataFrame({
            "open": np.random.randn(n) + 100,
            "high": np.random.randn(n) + 101,
            "low": np.random.randn(n) + 99,
            "close": np.random.randn(n) + 100,
            "volume": np.random.randint(1000, 10000, n).astype(float),
        })

    pipeline = FactorPipeline(max_workers=4)
    results = pipeline.compute_factors(req.factor_names, data)
    summary = {k: {"mean": float(v.mean()), "std": float(v.std())} for k, v in results.items()}
    return {"factors": summary, "count": len(summary)}
