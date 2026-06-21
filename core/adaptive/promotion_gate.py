"""晋升闸门 (阶段2) — 样本外验证 + 防过拟合 + 按市态分组冠军。

纠偏阶段1的问题: 不再用 composite score (负夏普被截断) 决定晋级,
改为 walk-forward 滚动前推的样本外稳健性 (detect_overfitting / check_robustness)。

晋级 = 通过 walk-forward 闸门 (样本外不显著退化)。
冠军按市态 (QUIET/TRENDING/VOLATILE/CRISIS) 分组, 避免风格切换全军覆没。
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

from backtest.vectorized_engine import VectorizedBacktest
from core.adaptive.bayesian_optimizer import BayesianOptimizer, ParameterSpace
from core.adaptive.walk_forward_validator import WalkForwardValidator
from core.config.watchlist import DEFAULT_MAIN_CONTRACT, WATCHLIST_PRODUCTS
from signals.registry import get_strategy


@dataclass
class PromotionVerdict:
    strategy_name: str
    contract: str
    passed: bool
    reason: str
    n_windows: int = 0
    mean_oos_sharpe: float = 0.0
    mean_degradation: float = 0.0
    overfit_ratio: float = 0.0
    best_params: Dict = field(default_factory=dict)
    regime: str = "UNKNOWN"
    windows: List[Dict] = field(default_factory=list)  # 每窗口 IS/OOS 明细 (训练过程可视化)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


def _load_kline(contract: str, timeframe: str = "D1", limit: int = 600) -> pd.DataFrame:
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


def _ensure_strategies_loaded() -> None:
    """确保策略已注册 (导入 signals.strategies 触发 @register 自动加载)。"""
    import signals.strategies  # noqa: F401


def _build_param_space(strategy_name: str) -> tuple[List[ParameterSpace], Dict]:
    """从策略默认 params 派生数值参数空间 (±50% 区间)。返回 (空间, 原始params)。"""
    _ensure_strategies_loaded()
    cls = get_strategy(strategy_name)
    if cls is None:
        return [], {}
    base = copy.deepcopy(getattr(cls, "params", {}) or {})
    spaces: List[ParameterSpace] = []
    for k, v in base.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        if v <= 0:
            continue
        low = max(1.0, v * 0.5)
        high = max(low + 1.0, v * 1.5)
        spaces.append(ParameterSpace(name=k, low=low, high=high))
    return spaces, base


def _detect_regime(df: pd.DataFrame) -> str:
    """用 HMMDetector 对收益序列判市态, 返回最后一个 regime 标签。失败回退 UNKNOWN。"""
    try:
        import numpy as np
        from market_state.regime_detector_v2 import HMMDetector
        returns = df["close"].pct_change()
        # 清洗 inf/NaN (零价/跳空会产生 inf), 否则 HMM 报错
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
        if len(returns) < 30:
            return "UNKNOWN"
        det = HMMDetector(n_regimes=4)
        det.fit(returns)
        labels = det.predict(returns)
        return labels[-1] if labels else "UNKNOWN"
    except Exception as e:
        logger.warning(f"[gate] regime detect failed: {e}")
        return "UNKNOWN"


class PromotionGate:
    """walk-forward 晋升闸门。"""

    def __init__(self, n_splits: int = 4, train_ratio: float = 0.6,
                 n_opt_iter: int = 8):
        self._engine = VectorizedBacktest()
        self._validator = WalkForwardValidator(
            train_ratio=train_ratio, n_splits=n_splits, min_train_size=80)
        self._n_opt_iter = n_opt_iter

    def _make_objective(self, strategy_name: str, base_params: Dict):
        cls = get_strategy(strategy_name)

        def objective(params: Dict[str, float], data_slice) -> float:
            inst = cls()
            merged = copy.deepcopy(base_params)
            for k, v in params.items():
                # 原始为 int 的参数取整
                merged[k] = int(round(v)) if isinstance(base_params.get(k), int) else v
            inst.params = merged
            if data_slice is None or len(data_slice) < 60:
                return -10.0
            res = self._engine.run(data_slice, inst, symbol=strategy_name)
            if res.total_trades == 0:
                return -10.0
            return float(res.sharpe_ratio)

        return objective

    def evaluate(self, strategy_name: str, contract: str) -> PromotionVerdict:
        """对单策略单合约跑 walk-forward, 给出晋升裁决。"""
        df = _load_kline(contract)
        if df.empty or len(df) < 200:
            return PromotionVerdict(strategy_name, contract, False,
                                    "数据不足 (<200 根)")
        param_space, base_params = _build_param_space(strategy_name)
        if not param_space:
            return PromotionVerdict(strategy_name, contract, False,
                                    "无可调数值参数, 跳过 walk-forward")
        objective = self._make_objective(strategy_name, base_params)
        try:
            report = self._validator.validate(
                data=df, objective=objective, optimizer_class=BayesianOptimizer,
                param_space=param_space, n_optimization_iter=self._n_opt_iter)
        except Exception as e:
            return PromotionVerdict(strategy_name, contract, False,
                                    f"验证异常: {type(e).__name__}: {e}")
        if report.n_windows == 0:
            return PromotionVerdict(strategy_name, contract, False, "无有效窗口")

        robust = self._validator.check_robustness(report)
        overfit = self._validator.detect_overfitting(report)
        passed = robust and not overfit and report.mean_oos_score > 0
        if passed:
            reason = "通过: 样本外稳健且无过拟合"
        elif overfit:
            reason = f"拒绝: 过拟合 (退化{report.mean_degradation:.1%}, 过拟合比{report.overfit_ratio:.0%})"
        elif report.mean_oos_score <= 0:
            reason = f"拒绝: 样本外夏普≤0 ({report.mean_oos_score:.2f})"
        else:
            reason = "拒绝: 稳健性不足"

        best = report.windows[-1].params if report.windows else {}
        windows = [
            {"window_id": w.window_id, "is_sharpe": round(w.in_sample_score, 4),
             "oos_sharpe": round(w.out_sample_score, 4),
             "degradation": round(w.oos_degradation, 4),
             "params": {k: round(v, 3) for k, v in w.params.items()}}
            for w in report.windows
        ]
        return PromotionVerdict(
            strategy_name, contract, passed, reason,
            n_windows=report.n_windows,
            mean_oos_sharpe=round(report.mean_oos_score, 4),
            mean_degradation=round(report.mean_degradation, 4),
            overfit_ratio=round(report.overfit_ratio, 4),
            best_params=best, regime=_detect_regime(df), windows=windows)

    def evaluate_candidates(self, strategy_names: List[str],
                            products: Optional[List[str]] = None) -> Dict:
        """批量评估候选, 返回晋级名单 + 按市态分组冠军。"""
        products = products or WATCHLIST_PRODUCTS
        verdicts: List[PromotionVerdict] = []
        for sname in strategy_names:
            # 每策略取首个有足够数据的品种主力评估 (控制耗时)
            for p in products:
                contract = DEFAULT_MAIN_CONTRACT.get(p.upper(), f"{p.upper()}2510")
                v = self.evaluate(sname, contract)
                if "数据不足" not in v.reason:
                    verdicts.append(v)
                    break

        promoted = [v for v in verdicts if v.passed]
        # 按市态分组冠军 (每市态取样本外夏普最高)
        by_regime: Dict[str, Dict] = {}
        for v in promoted:
            cur = by_regime.get(v.regime)
            if cur is None or v.mean_oos_sharpe > cur["mean_oos_sharpe"]:
                by_regime[v.regime] = v.to_dict()

        logger.info(f"[gate] evaluated {len(verdicts)}, promoted {len(promoted)}, "
                    f"regimes {list(by_regime.keys())}")
        result = {
            "evaluated": len(verdicts),
            "promoted": [v.to_dict() for v in promoted],
            "rejected": [v.to_dict() for v in verdicts if not v.passed],
            "champions_by_regime": by_regime,
        }
        _append_history(result)
        return result


_HISTORY_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "promotion_history.json"


def _append_history(result: Dict) -> None:
    """持久化晋升验证历史 (含每窗口明细), 供监控页展示。只留最近 50 次。"""
    try:
        import json
        from datetime import datetime
        _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        hist = []
        if _HISTORY_FILE.exists():
            hist = json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
        hist.insert(0, {
            "timestamp": datetime.now().isoformat(),
            "evaluated": result["evaluated"],
            "n_promoted": len(result["promoted"]),
            "champions_by_regime": list(result["champions_by_regime"].keys()),
            "verdicts": result["promoted"] + result["rejected"],
        })
        _HISTORY_FILE.write_text(json.dumps(hist[:50], ensure_ascii=False, indent=2),
                                 encoding="utf-8")
    except Exception as e:
        logger.warning(f"[gate] history persist failed: {e}")


_gate: Optional[PromotionGate] = None


def get_gate() -> PromotionGate:
    global _gate
    if _gate is None:
        _gate = PromotionGate()
    return _gate
