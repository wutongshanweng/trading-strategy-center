"""
模型性能监控 — 检测模型退化, 触发自动重训。

检测:
  - 当前滚动 IC vs 上线 baseline IC (衰减比例)
  - 预测误差 (RMSE)
  - 简易数据漂移分 (预测分布均值/方差偏移)

用法:
    monitor = ModelMonitor(decay_threshold=-0.3)
    report = monitor.check("lgb_rb", preds, actuals, baseline_ic=0.08)
    if report.needs_retrain:
        AutoMLPipeline().run("RB2510")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from loguru import logger


@dataclass
class MonitorReport:
    model_name: str
    current_ic: float
    baseline_ic: float
    ic_decay: float            # 相对衰减比例, 负值=退化
    prediction_error: float    # RMSE
    data_drift_score: float    # 0~1
    needs_retrain: bool
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "current_ic": round(self.current_ic, 4),
            "baseline_ic": round(self.baseline_ic, 4),
            "ic_decay": round(self.ic_decay, 4),
            "prediction_error": round(self.prediction_error, 6),
            "data_drift_score": round(self.data_drift_score, 4),
            "needs_retrain": self.needs_retrain, "reason": self.reason,
        }


class ModelMonitor:
    """模型性能监控 — 对比当前表现与 baseline。"""

    def __init__(self, decay_threshold: float = -0.3, drift_threshold: float = 0.5):
        """
        decay_threshold: IC 相对衰减超过此值 (更负) 触发重训, 如 -0.3 = 衰减30%
        drift_threshold: 数据漂移分超过此值触发重训
        """
        self.decay_threshold = decay_threshold
        self.drift_threshold = drift_threshold

    def check(
        self,
        model_name: str,
        predictions: np.ndarray,
        actuals: np.ndarray,
        baseline_ic: Optional[float] = None,
        baseline_pred_mean: Optional[float] = None,
        baseline_pred_std: Optional[float] = None,
    ) -> MonitorReport:
        """检查模型是否退化。"""
        pred = np.asarray(predictions, dtype=float).ravel()
        act = np.asarray(actuals, dtype=float).ravel()
        n = min(len(pred), len(act))
        pred, act = pred[:n], act[:n]

        current_ic = 0.0
        if n >= 3 and np.std(pred) > 0 and np.std(act) > 0:
            c = float(np.corrcoef(pred, act)[0, 1])
            current_ic = c if np.isfinite(c) else 0.0

        rmse = float(np.sqrt(np.mean((pred - act) ** 2))) if n else 0.0

        base = baseline_ic if baseline_ic is not None else current_ic
        # 相对衰减: (current - base) / |base|
        ic_decay = ((current_ic - base) / abs(base)) if abs(base) > 1e-9 else 0.0

        # 数据漂移: 预测分布相对 baseline 的均值/方差偏移
        drift = 0.0
        if baseline_pred_mean is not None and baseline_pred_std and baseline_pred_std > 0:
            mean_shift = abs(np.mean(pred) - baseline_pred_mean) / (baseline_pred_std + 1e-9)
            std_ratio = abs(np.std(pred) - baseline_pred_std) / (baseline_pred_std + 1e-9)
            drift = float(min((mean_shift + std_ratio) / 2, 1.0))

        reasons = []
        if ic_decay < self.decay_threshold:
            reasons.append(f"IC衰减{ic_decay:.0%} (当前{current_ic:.3f} vs基线{base:.3f})")
        if drift > self.drift_threshold:
            reasons.append(f"数据漂移分{drift:.2f}")
        needs = bool(reasons)

        report = MonitorReport(
            model_name=model_name, current_ic=current_ic, baseline_ic=base,
            ic_decay=ic_decay, prediction_error=rmse, data_drift_score=drift,
            needs_retrain=needs, reason="; ".join(reasons) or "健康")
        if needs:
            logger.warning(f"模型 {model_name} 需重训: {report.reason}")
        return report

    def batch_check(self, registry, eval_data: dict) -> List[MonitorReport]:
        """检查多个已注册模型。

        eval_data: {model_name: (predictions, actuals, baseline_ic)}
        """
        reports = []
        for name, payload in eval_data.items():
            preds, actuals = payload[0], payload[1]
            baseline = payload[2] if len(payload) > 2 else None
            reports.append(self.check(name, preds, actuals, baseline_ic=baseline))
        return reports
