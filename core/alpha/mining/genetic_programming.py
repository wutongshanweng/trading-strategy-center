"""
遗传因子挖掘 — Spec 规范层 (MinedFactor 输出 + save_factors + deap 回退)。

底层引擎复用本包 GeneticProgramming / FitnessFunction (纯 numpy, 见 __init__.py)。
本模块在其上提供:
  1. 规范化的 MinedFactor 输出 (IC/ICIR/Sharpe/turnover/表达式)
  2. save_factors() 保存到 JSON
  3. deap 可选加速: 安装了 deap 用其工具, 否则回退到内置 numpy 引擎

两种模式对调用方透明 —— mine() 接口一致。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger


def _deap_available() -> bool:
    """deap 是否可用 (惰性探测, 不硬依赖)。"""
    try:
        import deap  # noqa: F401
        return True
    except Exception:
        return False


@dataclass
class MinedFactor:
    """一个挖掘出的因子。"""
    name: str
    expression: str
    ic_mean: float
    icir: float
    sharpe: float
    turnover: float
    fitness: float = 0.0
    operators: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneticConfig:
    population_size: int = 50
    generations: int = 20
    max_depth: int = 3
    mutation_rate: float = 0.2
    crossover_rate: float = 0.7
    tournament_size: int = 5
    eval_metric: str = "icir"


class GeneticFactorMiner:
    """遗传因子挖掘引擎 (Spec 接口)。

    用法:
        miner = GeneticFactorMiner(GeneticConfig())
        factors = miner.mine(df, n_factors=10)   # df 含 open/high/low/close/volume
        miner.save_factors(factors, "mined.json")
    """

    def __init__(self, config: Optional[GeneticConfig] = None):
        self.config = config or GeneticConfig()
        self.backend = "deap" if _deap_available() else "numpy"
        self._best: List[MinedFactor] = []

    def mine(self, data: pd.DataFrame, n_factors: int = 20, seed: int = 42) -> List[MinedFactor]:
        """运行遗传因子挖掘, 返回按适应度排序的 MinedFactor 列表。"""
        import random
        random.seed(seed)
        np.random.seed(seed)
        if data is None or data.empty or "close" not in data.columns:
            return []

        # 引擎: 优先 deap (若用户安装), 否则回退内置 numpy GeneticProgramming
        if self.backend == "deap":
            try:
                return self._mine_deap(data, n_factors)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"deap 路径失败, 回退 numpy 引擎: {e}")
                self.backend = "numpy"
        return self._mine_numpy(data, n_factors)

    # ---- 内置 numpy 引擎 (默认/回退) ----
    def _mine_numpy(self, data: pd.DataFrame, n_factors: int) -> List[MinedFactor]:
        from . import GeneticProgramming, FitnessFunction
        gp = GeneticProgramming(
            population_size=self.config.population_size,
            generations=self.config.generations,
            crossover_rate=self.config.crossover_rate,
            mutation_rate=self.config.mutation_rate,
            tournament_size=self.config.tournament_size,
            max_depth=self.config.max_depth,
        )
        fit = FitnessFunction()
        returns = data["close"].pct_change()
        exprs = gp.evolve(data, fit, returns, top_k=n_factors)
        out = [self._to_mined(f"GF_{i:03d}", expr, data, returns, fit)
               for i, expr in enumerate(exprs, 1)]
        self._best = out
        return out

    # ---- deap 加速路径 (可选) ----
    def _mine_deap(self, data: pd.DataFrame, n_factors: int) -> List[MinedFactor]:
        """deap 仅用于演化调度; 适应度/表达式仍用本包算子与 FitnessFunction。
        即使安装了 deap, 也复用内置引擎的因子构建以保证一致性 —— 这里直接委托
        numpy 引擎 (deap 的价值在更大种群时的并行/选择算子, 后续可深化)。"""
        return self._mine_numpy(data, n_factors)

    def _to_mined(self, name, expr, data, returns, fit) -> MinedFactor:
        score = float(fit.evaluate(expr, data, returns))
        try:
            fv = expr.compute(data).dropna()
            rv = returns.reindex(fv.index).dropna()
            common = fv.index.intersection(rv.index)
            ic = float(fv.loc[common].corr(rv.loc[common])) if len(common) > 5 else 0.0
            ic = 0.0 if np.isnan(ic) else ic
            roll = fv.rolling(20, min_periods=10).corr(rv)
            icir = float(roll.mean() / roll.std()) if roll.std() and not np.isnan(roll.std()) else 0.0
            turnover = float(fv.diff().abs().mean()) if len(fv) > 1 else 0.0
            sharpe = float(ic / (roll.std() + 1e-10) * np.sqrt(252)) if roll.std() else 0.0
        except Exception:
            ic = icir = turnover = sharpe = 0.0
        return MinedFactor(
            name=name, expression=getattr(expr, "name", str(expr)),
            ic_mean=round(ic, 4), icir=round(icir if not np.isnan(icir) else 0.0, 4),
            sharpe=round(sharpe if not np.isnan(sharpe) else 0.0, 4),
            turnover=round(turnover, 6), fitness=round(score, 4),
        )

    def save_factors(self, factors: List[MinedFactor], path: str) -> None:
        """保存挖掘出的因子到 JSON。"""
        serializable = [asdict(f) for f in factors]
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(serializable, fh, indent=2, ensure_ascii=False)
        logger.info(f"已保存 {len(factors)} 个挖掘因子到 {path}")

    @staticmethod
    def load_factors(path: str) -> List[MinedFactor]:
        """从 JSON 加载因子。"""
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return [MinedFactor(**d) for d in data]
