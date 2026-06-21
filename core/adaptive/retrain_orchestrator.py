"""重训编排器 (阶段3) — 触发式三层迭代, 非定时盲重训。

三层不同节奏:
  - 参数层 (param): 对策略数值参数贝叶斯再优化 (OptimizationScheduler + 真实 kline)
  - 因子层 (factor): FactorDecayDetector 衰减检测, 产出健康报告
  - 模型层 (model): ModelMonitor 漂移检测 → 仅在 needs_retrain 时跑 AutoMLPipeline

设计原则: 由信号(漂移/衰减/退化)触发, 不是固定日历盲重训。
编排在 API 进程内 (DuckDB 单进程锁)。
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

from backtest.vectorized_engine import VectorizedBacktest
from core.adaptive.bayesian_optimizer import ParameterSpace
from core.adaptive.parameter_store import ParameterStore
from core.adaptive.scheduler import OptimizationScheduler
from core.config.watchlist import DEFAULT_MAIN_CONTRACT, WATCHLIST_PRODUCTS
from signals.registry import get_strategy


@dataclass
class RetrainReport:
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    param_optimized: List[Dict] = field(default_factory=list)
    factor_health: List[Dict] = field(default_factory=list)
    models_checked: List[Dict] = field(default_factory=list)
    models_retrained: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


def _load_kline(contract: str, timeframe: str = "D1", limit: int = 500) -> pd.DataFrame:
    from data_center.storage.duckdb_store import get_store
    store = get_store()
    sid = store.query("SELECT symbol_id FROM symbols WHERE code = ?", [contract.upper()])
    if sid is None or sid.empty:
        return pd.DataFrame()
    symbol_id = int(sid.iloc[0]["symbol_id"])
    df = store.query(
        """SELECT datetime, open, high, low, close, volume FROM kline
           WHERE symbol_id=? AND timeframe=? ORDER BY datetime DESC LIMIT ?""",
        [symbol_id, timeframe, limit],
    )
    if df is None or df.empty:
        return pd.DataFrame()
    return df.sort_values("datetime").reset_index(drop=True).set_index("datetime")


class RetrainOrchestrator:
    """三层触发式重训编排。"""

    def __init__(self, param_store_path: str = "parameter_store"):
        self._engine = VectorizedBacktest()
        self._store = ParameterStore(base_path=param_store_path)
        self._scheduler = OptimizationScheduler(parameter_store=self._store)

    # ---- 参数层 ----
    def optimize_params(self, strategy_names: List[str],
                        products: Optional[List[str]] = None,
                        n_iter: int = 10) -> List[Dict]:
        """对策略数值参数贝叶斯再优化, 结果存 ParameterStore。"""
        import signals.strategies  # noqa: F401 触发注册
        products = products or WATCHLIST_PRODUCTS
        out: List[Dict] = []
        for sname in strategy_names:
            cls = get_strategy(sname)
            if cls is None:
                continue
            base = copy.deepcopy(getattr(cls, "params", {}) or {})
            space = [ParameterSpace(name=k, low=max(1.0, v * 0.5), high=max(v * 1.5, v * 0.5 + 1.0))
                     for k, v in base.items()
                     if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0]
            if not space:
                continue
            # 取首个有数据的品种
            df = pd.DataFrame()
            contract = ""
            for p in products:
                contract = DEFAULT_MAIN_CONTRACT.get(p.upper(), f"{p.upper()}2510")
                df = _load_kline(contract)
                if not df.empty and len(df) >= 80:
                    break
            if df.empty or len(df) < 80:
                continue

            def objective(params: Dict[str, float], _df=df, _cls=cls, _base=base) -> float:
                inst = _cls()
                merged = copy.deepcopy(_base)
                for k, v in params.items():
                    merged[k] = int(round(v)) if isinstance(_base.get(k), int) else v
                inst.params = merged
                res = self._engine.run(_df, inst, symbol="opt")
                return float(res.sharpe_ratio) if res.total_trades > 0 else -10.0

            task_id = self._scheduler.submit_task(sname, space, objective, n_iterations=n_iter)
            result = self._scheduler.run_task(task_id)
            if result:
                out.append({"strategy": sname, "contract": contract,
                            "best_score": round(result["best_score"], 4),
                            "best_params": result["best_params"]})
        logger.info(f"[retrain] param layer: optimized {len(out)} strategies")
        return out

    # ---- 因子层 ----
    def check_factor_health(self, ic_series_map: Optional[Dict[str, pd.Series]] = None) -> List[Dict]:
        """因子衰减检测。无输入时跳过 (IC 序列需上游因子评估产出)。"""
        if not ic_series_map:
            return []
        from core.alpha.management.factor_decay import FactorDecayDetector
        det = FactorDecayDetector()
        reports = det.batch_check(ic_series_map)
        return [{"factor": name, "health": r.health.value if hasattr(r.health, "value") else str(r.health),
                 "current_ic": round(r.current_ic, 4), "alert": r.alert_level}
                for name, r in reports.items()]

    # ---- 模型层 ----
    def check_models(self, eval_data: Optional[Dict] = None,
                     auto_retrain: bool = False) -> tuple[List[Dict], List[str]]:
        """模型漂移检测; needs_retrain 且 auto_retrain 时跑 AutoMLPipeline。

        eval_data: {model_name: (predictions, actuals, baseline_ic)}。无则跳过。
        """
        if not eval_data:
            return [], []
        from ml.model_monitor import ModelMonitor
        monitor = ModelMonitor()
        checked, retrained = [], []
        for name, payload in eval_data.items():
            preds, actuals = payload[0], payload[1]
            baseline = payload[2] if len(payload) > 2 else None
            rep = monitor.check(name, preds, actuals, baseline_ic=baseline)
            checked.append(rep.to_dict())
            if rep.needs_retrain and auto_retrain:
                try:
                    from ml.auto_pipeline import AutoMLPipeline
                    symbol = name.split("_")[-1] if "_" in name else name
                    AutoMLPipeline().run(symbol)
                    retrained.append(name)
                except Exception as e:
                    logger.warning(f"[retrain] AutoML {name} failed: {e}")
        return checked, retrained

    # ---- 单周期编排 ----
    def run_cycle(self, strategy_names: Optional[List[str]] = None,
                  products: Optional[List[str]] = None,
                  ic_series_map: Optional[Dict] = None,
                  model_eval_data: Optional[Dict] = None,
                  auto_retrain_models: bool = False,
                  param_n_iter: int = 10) -> RetrainReport:
        """一次完整迭代周期。各层独立, 缺输入则跳过该层。"""
        report = RetrainReport()
        if strategy_names:
            report.param_optimized = self.optimize_params(strategy_names, products, param_n_iter)
        else:
            report.notes.append("param 层跳过: 未提供策略列表")
        report.factor_health = self.check_factor_health(ic_series_map)
        if not ic_series_map:
            report.notes.append("factor 层跳过: 未提供 IC 序列")
        report.models_checked, report.models_retrained = self.check_models(
            model_eval_data, auto_retrain=auto_retrain_models)
        if not model_eval_data:
            report.notes.append("model 层跳过: 未提供模型评估数据")
        logger.info(f"[retrain] cycle done: params={len(report.param_optimized)} "
                    f"factors={len(report.factor_health)} retrained={len(report.models_retrained)}")
        _append_retrain_history(report)
        return report


_RETRAIN_HISTORY = Path(__file__).resolve().parent.parent.parent / "data" / "retrain_history.json"


def _append_retrain_history(report: "RetrainReport") -> None:
    """持久化重训周期历史, 供监控页展示。只留最近 50 次。"""
    try:
        import json
        _RETRAIN_HISTORY.parent.mkdir(parents=True, exist_ok=True)
        hist = []
        if _RETRAIN_HISTORY.exists():
            hist = json.loads(_RETRAIN_HISTORY.read_text(encoding="utf-8"))
        d = report.to_dict()
        hist.insert(0, {
            "timestamp": d["timestamp"],
            "n_params_optimized": len(d["param_optimized"]),
            "param_optimized": d["param_optimized"],
            "n_factors_checked": len(d["factor_health"]),
            "n_models_checked": len(d["models_checked"]),
            "models_retrained": d["models_retrained"],
            "notes": d["notes"],
        })
        _RETRAIN_HISTORY.write_text(json.dumps(hist[:50], ensure_ascii=False, indent=2),
                                    encoding="utf-8")
    except Exception as e:
        logger.warning(f"[retrain] history persist failed: {e}")


_orch: Optional[RetrainOrchestrator] = None


def get_orchestrator() -> RetrainOrchestrator:
    global _orch
    if _orch is None:
        _orch = RetrainOrchestrator()
    return _orch
