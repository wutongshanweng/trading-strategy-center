"""UMP 裁判机制 — 交易级 ML 否决闸门 (受 abu 启发, 全新独立实现)。

概念 (非拷贝 abu GPL 代码, 按思想重写):
  不预测涨跌, 而是学习"策略在什么特征形态下会亏", 在下单前否决"长得像历史亏损单"的交易。
  叠加在任意策略之上, 与策略本身解耦。

两层裁判:
  - 主裁 (UMPMainJudge): GMM 高斯混合聚类把历史交易特征分簇, 标记"高失败率+负收益"的坏簇,
    新交易落入坏簇则否决。
  - 边裁 (UMPEdgeJudge): 相似度投票 (KNN 欧氏距离 + 相关性), 找历史最相似交易加权投票胜负。

特征提取: trade_features() 从入场时的 kline 窗口算 动量/波动/位置/量能 等特征。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger


def trade_features(df: pd.DataFrame, idx: int, lookback: int = 20) -> Optional[Dict[str, float]]:
    """提取某根 K 线 (入场点) 的交易特征。idx 为 df 中的位置索引。

    返回归一化的形态特征 dict; 数据不足返回 None。
    """
    if idx < lookback or idx >= len(df):
        return None
    win = df.iloc[idx - lookback:idx + 1]
    close = win["close"].values
    high = win["high"].values
    low = win["low"].values
    vol = win["volume"].values if "volume" in win else np.ones(len(win))
    c0 = close[-1]
    if c0 <= 0:
        return None
    rng = high.max() - low.min()
    rets = np.diff(close) / close[:-1]
    feats = {
        # 动量: 近 lookback 收益
        "momentum": float((c0 - close[0]) / close[0]),
        # 短期动量: 近 5 根
        "momentum_5": float((c0 - close[-6]) / close[-6]) if len(close) >= 6 else 0.0,
        # 波动率: 收益标准差
        "volatility": float(np.std(rets)) if len(rets) > 1 else 0.0,
        # 价格在区间的位置 (0=最低, 1=最高)
        "price_position": float((c0 - low.min()) / rng) if rng > 0 else 0.5,
        # 当前 K 实体相对区间
        "body_ratio": float(abs(close[-1] - df.iloc[idx]["open"]) / rng) if rng > 0 else 0.0,
        # 量能比: 当前量 / 均量
        "volume_ratio": float(vol[-1] / (vol.mean() + 1e-9)),
        # 上影/下影
        "upper_wick": float((high[-1] - max(close[-1], df.iloc[idx]["open"])) / rng) if rng > 0 else 0.0,
        # 偏度
        "skew": float(pd.Series(rets).skew()) if len(rets) > 2 else 0.0,
    }
    return {k: (v if np.isfinite(v) else 0.0) for k, v in feats.items()}


@dataclass
class UMPMainJudge:
    """主裁: GMM 聚类标记坏簇。"""
    n_clusters: int = 12
    fail_rate_threshold: float = 0.55   # 簇失败率超此值
    min_cluster_size: int = 3
    feature_names: List[str] = field(default_factory=list)
    _model: object = None
    _bad_clusters: set = field(default_factory=set)
    _mean: Optional[np.ndarray] = None
    _std: Optional[np.ndarray] = None
    _fitted: bool = False

    def fit(self, X: np.ndarray, wins: np.ndarray) -> "UMPMainJudge":
        """X: (n, d) 交易特征; wins: (n,) 1=盈利 0=亏损。"""
        from sklearn.mixture import GaussianMixture
        if len(X) < self.n_clusters * 2:
            self._fitted = False
            return self
        self._mean = X.mean(axis=0)
        self._std = X.std(axis=0) + 1e-9
        Xn = (X - self._mean) / self._std
        k = min(self.n_clusters, len(X) // 2)
        self._model = GaussianMixture(n_components=k, covariance_type="full",
                                      random_state=42, max_iter=100)
        labels = self._model.fit_predict(Xn)
        # 找坏簇: 失败率高 且 簇内总收益为负方向 (用 win 比例近似)
        self._bad_clusters = set()
        for c in range(k):
            mask = labels == c
            n = int(mask.sum())
            if n < self.min_cluster_size:
                continue
            fail_rate = 1.0 - wins[mask].mean()
            if fail_rate >= self.fail_rate_threshold:
                self._bad_clusters.add(c)
        self._fitted = True
        logger.info(f"[ump-main] fitted: {k} clusters, {len(self._bad_clusters)} bad")
        return self

    def predict_block(self, x: np.ndarray) -> bool:
        """新交易特征向量 → 是否落入坏簇 (True=否决)。"""
        if not self._fitted or self._model is None:
            return False
        xn = (x.reshape(1, -1) - self._mean) / self._std
        cluster = int(self._model.predict(xn)[0])
        return cluster in self._bad_clusters


@dataclass
class UMPEdgeJudge:
    """边裁: 相似度投票 (KNN 欧氏距离 + 相关性)。"""
    n_neighbors: int = 30
    block_threshold: float = 0.6        # 相似历史交易中亏损占比超此值则否决
    _X: Optional[np.ndarray] = None
    _wins: Optional[np.ndarray] = None
    _mean: Optional[np.ndarray] = None
    _std: Optional[np.ndarray] = None
    _fitted: bool = False

    def fit(self, X: np.ndarray, wins: np.ndarray) -> "UMPEdgeJudge":
        if len(X) < self.n_neighbors:
            self._fitted = False
            return self
        self._mean = X.mean(axis=0)
        self._std = X.std(axis=0) + 1e-9
        self._X = (X - self._mean) / self._std
        self._wins = wins
        self._fitted = True
        return self

    def predict_block(self, x: np.ndarray) -> bool:
        """找最相似的 N 笔历史交易, 若其亏损占比超阈值则否决。"""
        if not self._fitted or self._X is None:
            return False
        xn = (x.reshape(1, -1) - self._mean) / self._std
        dists = np.linalg.norm(self._X - xn, axis=1)
        k = min(self.n_neighbors, len(dists))
        nearest = np.argsort(dists)[:k]
        fail_rate = 1.0 - self._wins[nearest].mean()
        return fail_rate >= self.block_threshold


@dataclass
class UMPManager:
    """组织主裁 + 边裁; 任一否决即拦截 (可配置为需双否决)。"""
    require_both: bool = False          # True=需主+边都否决才拦; False=任一否决即拦
    feature_names: List[str] = field(default_factory=list)
    main: UMPMainJudge = field(default_factory=UMPMainJudge)
    edge: UMPEdgeJudge = field(default_factory=UMPEdgeJudge)
    _fitted: bool = False
    _n_train: int = 0

    def fit(self, trades_df: pd.DataFrame, feature_cols: List[str],
            outcome_col: str = "pnl") -> "UMPManager":
        """trades_df: 每行一笔历史交易, 含特征列 + 盈亏列。"""
        if trades_df is None or trades_df.empty or len(trades_df) < 20:
            self._fitted = False
            return self
        self.feature_names = feature_cols
        X = trades_df[feature_cols].to_numpy(dtype=float)
        wins = (trades_df[outcome_col].to_numpy(dtype=float) > 0).astype(float)
        self.main.feature_names = feature_cols
        self.main.fit(X, wins)
        self.edge.fit(X, wins)
        self._fitted = self.main._fitted or self.edge._fitted
        self._n_train = len(trades_df)
        return self

    def block_decision(self, features: Dict[str, float]) -> Dict:
        """对一笔候选交易做否决裁定。返回 {block, main_block, edge_block, reason}。"""
        if not self._fitted:
            return {"block": False, "main_block": False, "edge_block": False,
                    "reason": "UMP 未训练, 放行"}
        x = np.array([features.get(n, 0.0) for n in self.feature_names], dtype=float)
        mb = self.main.predict_block(x)
        eb = self.edge.predict_block(x)
        block = (mb and eb) if self.require_both else (mb or eb)
        reasons = []
        if mb:
            reasons.append("主裁: 落入历史高亏损簇")
        if eb:
            reasons.append("边裁: 相似历史交易多数亏损")
        return {"block": block, "main_block": mb, "edge_block": eb,
                "reason": "; ".join(reasons) or "通过两裁, 放行",
                "n_train": self._n_train}

