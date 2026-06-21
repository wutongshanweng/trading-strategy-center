"""API routes for intelligence upgrade: RL, risk monitoring, monitoring."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])


class RetrainCycleRequest(BaseModel):
    strategies: Optional[List[str]] = None
    products: Optional[List[str]] = None
    param_n_iter: int = 10


@router.post("/retrain/cycle")
async def retrain_cycle(req: RetrainCycleRequest):
    """触发式重训单周期 (阶段3): 参数层贝叶斯再优化 + 因子/模型层检测。

    strategies 省略时取锦标赛排行榜前 8。同步执行, 参数层较慢。
    """
    from core.adaptive.retrain_orchestrator import get_orchestrator
    strategies = req.strategies
    if not strategies:
        from api.routes.tournament_routes import _manager
        board = await _manager.get_leaderboard(8)
        strategies = [e.name for e in board]
    report = get_orchestrator().run_cycle(
        strategy_names=strategies, products=req.products, param_n_iter=req.param_n_iter)
    return report.to_dict()


# ---- 智能迭代监控 (统一状态聚合) ----

def _read_json(path, default):
    import json
    from pathlib import Path
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


@router.get("/iteration/overview")
async def iteration_overview():
    """智能迭代总览: 自动化状态 + 各环节计数。"""
    from core.adaptive.parameter_store import ParameterStore
    from api.routes.tournament_routes import _manager

    store = ParameterStore()
    strategies = store.list_strategies()
    total_versions = sum(len(store.list_versions(s)) for s in strategies)

    promo_hist = _read_json("data/promotion_history.json", [])
    retrain_hist = _read_json("data/retrain_history.json", [])
    feedback = _read_json("data/feedback_log.json", [])

    from core.adaptive.champion_challenger import get_registry
    lifecycle = get_registry().list_all()

    board = await _manager.get_leaderboard(100)
    return {
        "automation": {
            "enabled": False,
            "note": "迭代当前为手动触发 (回测/晋升/重训需点按钮或调 API)。后台线程仅跑新闻30min+信号15min。",
            "background_tasks": ["news_refresh_30min", "signal_scan_15min"],
        },
        "counts": {
            "ranked_strategies": len(board),
            "param_tuned_strategies": len(strategies),
            "param_versions_total": total_versions,
            "promotion_runs": len(promo_hist),
            "retrain_cycles": len(retrain_hist),
            "feedback_entries": len(feedback),
            "champions": len(lifecycle["champions"]),
            "challengers": len(lifecycle["challengers"]),
        },
        "last_promotion": promo_hist[0] if promo_hist else None,
        "last_retrain": retrain_hist[0] if retrain_hist else None,
    }


@router.get("/iteration/param-versions")
async def iteration_param_versions(strategy: Optional[str] = None):
    """参数版本演化: 某策略或全部策略的优化历史。"""
    from core.adaptive.parameter_store import ParameterStore
    store = ParameterStore()
    names = [strategy] if strategy else store.list_strategies()
    out = {}
    for name in names:
        versions = store.list_versions(name)
        out[name] = [
            {"version": v.version, "score": round(v.score, 4),
             "params": v.params, "timestamp": v.timestamp}
            for v in versions
        ]
    return {"strategies": out}


@router.get("/iteration/promotion-history")
async def iteration_promotion_history(limit: int = 20):
    """晋升验证历史 (含每窗口 IS/OOS 明细)。"""
    hist = _read_json("data/promotion_history.json", [])
    return {"count": len(hist), "history": hist[:limit]}


@router.get("/iteration/retrain-history")
async def iteration_retrain_history(limit: int = 20):
    """重训周期历史。"""
    hist = _read_json("data/retrain_history.json", [])
    return {"count": len(hist), "history": hist[:limit]}


# ---- 自动迭代 (B 阶段) ----

class AutomationConfigRequest(BaseModel):
    enabled: Optional[bool] = None
    interval_hours: Optional[int] = None
    param_n_iter: Optional[int] = None
    top_n_for_param: Optional[int] = None


@router.get("/automation/config")
async def automation_config():
    """读取自动迭代配置 + 最近运行日志。"""
    from core.adaptive.auto_iteration import get_config, get_log
    return {"config": get_config(), "log": get_log(20)}


@router.post("/automation/config")
async def set_automation_config(req: AutomationConfigRequest):
    """更新自动迭代配置 (运行时生效, 无需重启)。"""
    from core.adaptive.auto_iteration import update_config
    return {"config": update_config(req.model_dump(exclude_none=True))}


@router.post("/automation/run-now")
async def automation_run_now():
    """立即手动触发一次安全自动周期 (回测 + 参数层重优化)。"""
    from core.adaptive.auto_iteration import run_safe_cycle
    return await run_safe_cycle(trigger="manual")


# ---- UMP 裁判机制 (交易级 ML 否决闸门) ----

class UMPTrainRequest(BaseModel):
    strategy: str
    contracts: Optional[List[str]] = None


@router.get("/ump/models")
async def ump_models():
    """已训练的 UMP 裁判模型列表。"""
    from core.ump.service import get_ump_service
    return {"models": get_ump_service().list_models()}


@router.post("/ump/train")
async def ump_train(req: UMPTrainRequest):
    """对某策略训练 UMP 裁判 (从真实 kline 提取逐笔交易特征+盈亏)。"""
    from core.ump.service import get_ump_service
    return get_ump_service().train(req.strategy, req.contracts)



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
