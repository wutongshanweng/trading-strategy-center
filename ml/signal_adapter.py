"""
ML 特征 → 信号引擎适配器。

将 FeaturePipeline 产出的特征转换为 signals/ 引擎可消费的 Signal 对象。

用法:
    adapter = MLSignalAdapter()
    X = pipe.compute_all(data)
    signals = adapter.to_signals(X, symbol="RB2510")
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd

from signals.base import Signal, Direction


class MLSignalAdapter:
    """将 ML 特征转换为信号引擎的 Signal 对象。

    规则: 每个特征做 z-score, 正分→BUY 负分→SELL, strength=|z|/3 截断 0~1。
    """

    def to_signals(
        self,
        features_df: pd.DataFrame,
        symbol: str = "",
        source_system: str = "ml_features",
    ) -> List[Signal]:
        """将特征矩阵每列转为一个 Signal (太弱的跳过)。"""
        signals: List[Signal] = []
        for col in features_df.columns:
            vals = features_df[col].dropna()
            if len(vals) < 3 or vals.std() == 0:
                continue
            z = (vals - vals.mean()) / (vals.std() + 1e-10)
            latest_z = float(z.iloc[-1])
            if latest_z > 0.5:
                direction = Direction.BUY
            elif latest_z < -0.5:
                direction = Direction.SELL
            else:
                continue
            signals.append(Signal(
                symbol=symbol, direction=direction,
                confidence=min(abs(latest_z) / 3.0, 1.0),
                score=latest_z, reason=f"ML特征{col} z-score={latest_z:.2f}",
                strategy_name=f"ml_{col}", source_system=source_system,
                resonance_layer="T"))
        return signals

    def to_combined_signal(
        self, features_df: pd.DataFrame, symbol: str = "",
    ) -> Optional[Signal]:
        """将所有特征 z-score 后等权合并为一个综合信号。"""
        vals = features_df.dropna()
        if vals.empty:
            return None
        z_scores = (vals - vals.mean()) / (vals.std() + 1e-10)
        combined_z = float(z_scores.mean(axis=1).iloc[-1])
        if abs(combined_z) < 0.3:
            return None
        return Signal(
            symbol=symbol,
            direction=Direction.BUY if combined_z > 0 else Direction.SELL,
            confidence=min(abs(combined_z) / 3.0, 0.9), score=combined_z,
            reason=f"ML综合信号 z-score={combined_z:.2f} ({len(vals.columns)}特征)",
            strategy_name="ml_ensemble", source_system="ml_features",
            resonance_layer="T")
