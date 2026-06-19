# 因子研究升级 Phase 2 Specification
## 遗传因子挖掘 + 因子监控 + 行业中性化 + 报告系统

> 架构师: 冷域 | 开发者: Claude Code | 版本: v1.0
> 基准代码: https://github.com/wutongshanweng/trading-strategy-center (commit f220e89c)

---

## 1. 概述

### 1.1 目标

在已有 Alpha 101 因子库 + FactorAnalyzer 基础上，补齐四个核心能力：

1. **遗传因子挖掘** — 从基础算子自动生成新因子
2. **因子衰减监控** — 自动检测因子何时失效
3. **行业中性化** — 去除行业暴露偏差
4. **因子研究报告** — 一键跑全因子测试→排名→推荐组合

### 1.2 文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `core/alpha/mining/genetic_programming.py` | 🆕 新建 | 遗传编程因子挖掘引擎 |
| `core/alpha/mining/operator_set.py` | 🆕 新建 | 基础算子集合（可组合的数学/逻辑运算） |
| `core/alpha/management/factor_decay.py` | 🆕 新建 | 因子衰减/失效检测 |
| `core/alpha/management/industry_neutral.py` | 🆕 新建 | 行业中性化 |
| `core/alpha/management/report_generator.py` | 🆕 新建 | 全因子研究报告生成器 |
| `core/alpha/management/__init__.py` | 🟡 改 | 导出上述模块 |
| `core/alpha/mining/__init__.py` | 🟡 改 | 导出 genetic_programming + operator_set |
| `tests/unit/test_factor_mining.py` | 🆕 新建 | 因子挖掘单元测试 |
| `tests/unit/test_factor_management.py` | 🆕 新建 | 因子管理单元测试 |
| `requirements-dev.txt` | 🟡 改 | 新增依赖（如 deap、风险提示） |

---

## 2. 依赖说明

### 2.1 新增依赖（写进 requirements-dev.txt）

```
deap>=1.4.0          # 遗传编程框架 (遗传因子挖掘用)
```

**不硬依赖**：`deap` 的 import 放在函数内部，没有 deap 时回退到随机搜索。

### 2.2 已有依赖（不需要动）

```
pandas, numpy, scipy, loguru    # 已有
```

---

## 3. 模块一：遗传因子挖掘（核心）

### 3.1 目录结构

```
core/alpha/mining/
├── __init__.py              # 导出 GeneticFactorMiner + OperatorSet
├── operator_set.py          # 可组合的基础算子
└── genetic_programming.py   # 遗传编程引擎
```

### 3.2 operator_set.py — 基础算子

```python
"""
基础算子集合 — 遗传因子挖掘的构建单元。

每个算子是一个纯函数，输入 pd.Series，输出 pd.Series。
算子分三类：
  1. 时间序列算子 (ts_*) — 对单条序列操作
  2. 截面算子 (cs_*) — 对多个标的的横截面操作  
  3. 数学算子 (op_*) — 合并两条序列

用法:
    from core.alpha.mining.operator_set import get_operators, apply_operator
    op = get_operators()
    result = apply_operator("ts_rank", close, d=10)
"""

from typing import Callable, Dict, List, Optional, Union
import numpy as np
import pandas as pd


# ═══════════════════════════════════════════
# 时间序列算子 (输入一条序列 → 输出一条序列)
# ═══════════════════════════════════════════

def ts_rank(s: pd.Series, d: int = 5) -> pd.Series:
    """过去 d 天的排名百分位"""
    return s.rolling(d, min_periods=max(1, d // 2)).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) > 0 else 0.5
    )

def ts_sum(s: pd.Series, d: int = 5) -> pd.Series:
    """过去 d 天求和"""
    return s.rolling(d, min_periods=1).sum()

def ts_mean(s: pd.Series, d: int = 5) -> pd.Series:
    """过去 d 天均值"""
    return s.rolling(d, min_periods=1).mean()

def ts_std(s: pd.Series, d: int = 5) -> pd.Series:
    """过去 d 天标准差"""
    return s.rolling(d, min_periods=2).std()

def ts_min(s: pd.Series, d: int = 5) -> pd.Series:
    """过去 d 天最小值"""
    return s.rolling(d, min_periods=1).min()

def ts_max(s: pd.Series, d: int = 5) -> pd.Series:
    """过去 d 天最大值"""
    return s.rolling(d, min_periods=1).max()

def ts_argmax(s: pd.Series, d: int = 5) -> pd.Series:
    """过去 d 天中最大值出现在几天前"""
    return s.rolling(d, min_periods=1).apply(lambda x: np.argmax(x) if len(x) > 0 else 0)

def ts_argmin(s: pd.Series, d: int = 5) -> pd.Series:
    """过去 d 天中最小值出现在几天前"""

def ts_corr(s1: pd.Series, s2: pd.Series, d: int = 5) -> pd.Series:
    """两条序列过去 d 天的相关系数"""

def ts_cov(s1: pd.Series, s2: pd.Series, d: int = 5) -> pd.Series:
    """两条序列过去 d 天的协方差"""

def delay(s: pd.Series, d: int = 1) -> pd.Series:
    """延迟 d 天"""
    return s.shift(d)

def delta(s: pd.Series, d: int = 1) -> pd.Series:
    """当前值 - d 天前的值"""
    return s - s.shift(d)

def ts_rank_decay(s: pd.Series, d: int = 5) -> pd.Series:
    """衰减加权排名（近期权重更大）"""
    weights = np.array([0.5**i for i in range(d)])
    weights /= weights.sum()
    return s.rolling(d).apply(lambda x: np.sum(x * weights[-len(x):]) if len(x) > 0 else 0)

def scale(s: pd.Series, target: float = 1.0) -> pd.Series:
    """缩放到目标绝对值"""
    return s / (s.abs().mean() + 1e-10) * target


# ═══════════════════════════════════════════
# 数学算子 (输入两条序列 → 输出一条序列)
# ═══════════════════════════════════════════

def op_add(s1: pd.Series, s2: pd.Series) -> pd.Series:
    return s1 + s2

def op_sub(s1: pd.Series, s2: pd.Series) -> pd.Series:
    return s1 - s2

def op_mul(s1: pd.Series, s2: pd.Series) -> pd.Series:
    return s1 * s2

def op_div(s1: pd.Series, s2: pd.Series) -> pd.Series:
    return s1 / (s2 + 1e-10)

def op_max(s1: pd.Series, s2: pd.Series) -> pd.Series:
    return pd.concat([s1, s2], axis=1).max(axis=1)

def op_min(s1: pd.Series, s2: pd.Series) -> pd.Series:
    return pd.concat([s1, s2], axis=1).min(axis=1)


# ═══════════════════════════════════════════
# 算子注册表 — 所有算子的统一入口
# ═══════════════════════════════════════════

TS_OPERATORS: Dict[str, Callable] = { ... }
# 注册所有 ts_* 算子，包含参数信息

MATH_OPERATORS: Dict[str, Callable] = { ... }
# 注册所有 op_* 算子


def get_operator(name: str) -> Optional[Callable]:
    """按名称获取算子"""
    return TS_OPERATORS.get(name) or MATH_OPERATORS.get(name)

def get_operators() -> Dict[str, Callable]:
    """获取所有算子"""
    return {**TS_OPERATORS, **MATH_OPERATORS}

def apply_operator(name: str, *args, **kwargs) -> pd.Series:
    """应用算子（带参数）"""
    op = get_operator(name)
    if op is None:
        raise ValueError(f"Unknown operator: {name}")
    return op(*args, **kwargs)
```

### 3.3 genetic_programming.py — 遗传编程引擎

```python
"""
遗传编程因子挖掘引擎。

核心思想:
  1. 用算子随机组合成因子表达式树
  2. 用 IC/ICIR 评估适应度
  3. 交叉 + 变异产生下一代
  4. 多代演化后筛选最优因子

两种模式:
  - normal: 标准 DEAP 遗传编程 (需要 deap)
  - fallback: 纯 numpy 随机搜索 (无额外依赖)
"""

from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class MinedFactor:
    """一个挖掘出的因子"""
    name: str                               # 自动生成名 "GF_001"
    expression: str                         # 表达式树描述
    operators: List[str]                    # 所用算子列表
    ic_mean: float                          # 训练集 IC 均值
    icir: float                             # 训练集 ICIR
    sharpe: float                           # 分层多空夏普 (Q5-Q1)
    turnover: float                         # 因子换手率
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneticConfig:
    """遗传编程配置"""
    population_size: int = 100              # 种群大小
    generations: int = 20                   # 迭代代数
    max_depth: int = 5                      # 表达式树最大深度
    mutation_rate: float = 0.2              # 变异率
    crossover_rate: float = 0.7             # 交叉率
    elite_ratio: float = 0.1                # 精英保留比例
    tournament_size: int = 3                # 锦标赛选择大小
    
    # 可用算子
    ts_operators: List[str] = field(
        default_factory=lambda: [
            "ts_rank", "ts_sum", "ts_mean", "ts_std",
            "ts_min", "ts_max", "ts_argmax", "ts_argmin",
            "delay", "delta", "scale", "ts_rank_decay",
        ]
    )
    math_operators: List[str] = field(
        default_factory=lambda: ["op_add", "op_sub", "op_mul", "op_div"]
    )
    ts_windows: List[int] = field(
        default_factory=lambda: [3, 5, 10, 20, 30, 60]
    )
    
    # 评估配置
    eval_metric: str = "icir"               # 适应度指标
    train_split: float = 0.7                # 训练集比例
    early_stop_generations: int = 5         # 早停代数


class GeneticFactorMiner:
    """
    遗传因子挖掘引擎。
    
    用法:
        miner = GeneticFactorMiner(config=GeneticConfig())
        df = load_data()  # 需含 open/high/low/close/volume
        results = miner.mine(df, n_factors=20)
        
        for f in results:
            print(f"{f.name}: IC={f.ic_mean:.3f}, ICIR={f.icir:.2f}")
    """
    
    def __init__(self, config: Optional[GeneticConfig] = None):
        self.config = config or GeneticConfig()
        self._history: Dict[int, List[MinedFactor]] = {}
        self._best_factors: List[MinedFactor] = []
    
    def mine(
        self,
        data: pd.DataFrame,
        n_factors: int = 20,
        seed: int = 42,
    ) -> List[MinedFactor]:
        """
        运行遗传因子挖掘。
        
        Args:
            data: 行情数据 (open/high/low/close/volume)
            n_factors: 最终返回的最优因子数
            seed: 随机种子
            
        Returns:
            按适应度排序的 MinedFactor 列表
        """
        # 1. 准备数据（计算日收益率）
        # 2. 分割训练/验证集
        # 3. 初始化种群
        # 4. 迭代演化:
        #    a. 评估适应度 → compute_fitness(expression)
        #    b. 精英保留
        #    c. 锦标赛选择
        #    d. 交叉
        #    e. 变异
        # 5. 验证集上最终评估
        # 6. 返回 Top-N
        
        # 实现细节:
        # - 使用 DEAP 库 (优先) 或 纯 numpy 实现 (回退)
        # - 表达式用嵌套元组表示: ("op_add", ("ts_rank", "close", 10), ("ts_mean", "volume", 20))
        # - 适应度 = ICIR (默认) 或 RankIC
        # - 每代记录最佳因子到 self._history
        pass
    
    def _build_expression(self, depth: int = None) -> tuple:
        """随机生成因子表达式树"""
        pass
    
    def _evaluate_expression(
        self, 
        expr: tuple, 
        data: pd.DataFrame,
        forward_returns: pd.Series,
    ) -> float:
        """计算一个表达式的适应度"""
        pass
    
    def _crossover(self, expr1: tuple, expr2: tuple) -> Tuple[tuple, tuple]:
        """交叉操作 — 交换子树"""
        pass
    
    def _mutate(self, expr: tuple) -> tuple:
        """变异操作 — 替换子树"""
        pass
    
    def _expression_to_string(self, expr: tuple) -> str:
        """表达式 → 可读字符串"""
        pass
    
    def get_history(self) -> Dict[int, List[MinedFactor]]:
        """获取每代最优因子"""
        return self._history
    
    def save_factors(self, factors: List[MinedFactor], path: str):
        """保存挖掘出的因子到 JSON"""
        import json
        serializable = [
            {
                "name": f.name,
                "expression": f.expression,
                "ic_mean": round(f.ic_mean, 4),
                "icir": round(f.icir, 4),
                "sharpe": round(f.sharpe, 4),
                "turnover": round(f.turnover, 4),
                "operators": f.operators,
                "params": f.params,
            }
            for f in factors
        ]
        with open(path, "w") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(factors)} mined factors to {path}")
```

---

## 4. 模块二：因子衰减监控

### 4.1 factor_decay.py

```python
"""
因子衰减监控 — 自动检测因子何时失效。

检测维度:
  1. IC 衰减: 滑动窗口 IC 是否持续下降
  2. ICIR 衰减: 风险调整后 IC 是否下降
  3. 换手率突变: 因子稳定性是否变差
  4. 分组单调性: 分层收益是否丧失单调性

状态定义:
  - HEALTHY: 正常
  - WARNING: 需关注 (IC < 阈值 或 持续下降)
  - DECAYED: 已失效 (需下线)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from loguru import logger


class FactorHealth(Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    DECAYED = "DECAYED"


@dataclass
class FactorHealthReport:
    factor_name: str
    health: FactorHealth
    current_ic: float
    ic_trend: float                    # 正 = 改善, 负 = 衰减
    ic_mean_3m: float                  # 近3个月IC均值
    ic_mean_6m: float                  # 近6个月IC均值
    icir: float
    turnover: float
    monotonicity: float                # 分层单调性评分 0~1
    reasons: List[str] = field(default_factory=list)
    alert_level: str = "info"          # "info" / "warning" / "critical"


class FactorDecayDetector:
    """
    因子衰减检测器。
    
    用法:
        detector = FactorDecayDetector()
        report = detector.check(factor_name, factor_values, returns)
        if report.health == FactorHealth.DECAYED:
            print(f"⚠️ {factor_name} 已失效! ")
    """
    
    def __init__(
        self,
        ic_threshold: float = 0.02,         # IC 低于此值告警
        decay_slope_threshold: float = -0.005,  # IC 斜率低于此值视为衰减
        lookback_windows: List[int] = None,  # 检测窗口
    ):
        self.ic_threshold = ic_threshold
        self.decay_slope_threshold = decay_slope_threshold
        self.lookback_windows = lookback_windows or [20, 60, 120]
    
    def check(
        self,
        factor_name: str,
        factor_values: pd.Series,
        forward_returns: pd.Series,
    ) -> FactorHealthReport:
        """
        全面检查一个因子的健康状况。
        
        检测项:
          1. 当前 IC 绝对值
          2. IC 时间序列趋势 (线性回归斜率)
          3. 短/中/长期 IC 对比
          4. 换手率
          5. 分层单调性
        """
        # 计算各项指标
        # 综合判定健康状态
        pass
    
    def _compute_ic_trend(self, ic_series: pd.Series) -> float:
        """计算 IC 趋势斜率 (正=改善, 负=衰减)"""
        x = np.arange(len(ic_series))
        mask = ~ic_series.isna()
        if mask.sum() < 5:
            return 0.0
        slope = np.polyfit(x[mask], ic_series[mask], 1)[0]
        return float(slope)
    
    def _compute_monotonicity(
        self, 
        factor_values: pd.Series, 
        forward_returns: pd.Series,
        n_quantiles: int = 5,
    ) -> float:
        """计算分层单调性评分 0~1"""
        # Q1 到 Q5 的收益应该单调递增（正因子）或递减（负因子）
        # 用 Spearman 相关系数衡量单调性
        pass
    
    def batch_check(
        self,
        factors_df: pd.DataFrame,
        forward_returns: pd.Series,
    ) -> Dict[str, FactorHealthReport]:
        """批量检查多个因子"""
        return {
            name: self.check(name, factors_df[name], forward_returns)
            for name in factors_df.columns
        }
```

---

## 5. 模块三：行业中性化

### 5.1 industry_neutral.py

```python
"""
行业中性化 — 去除因子中的行业暴露偏差。

因为因子值可能受行业影响（比如某个行业整体表现好），
行业中性化把因子值减去行业均值，得到"行业内相对强弱"。

方法:
  1. 行业均值法: factor - industry_mean (默认)
  2. 行业回归法: factor ~ industry_dummies, 取残差
  3. 行业 Z-score: (factor - industry_mean) / industry_std
"""

from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from loguru import logger


class IndustryNeutralizer:
    """
    行业中性化处理器。
    
    用法:
        neutralizer = IndustryNeutralizer()
        
        # 1. 行业均值法
        neutral = neutralizer.neutralize_by_mean(
            factor_values=df["alpha_001"],
            industry_labels=df["industry"],
        )
        
        # 2. 行业回归法
        neutral = neutralizer.neutralize_by_regression(
            factor_values=df["alpha_001"],
            industry_dummies=industry_dummies,
        )
    """
    
    def neutralize_by_mean(
        self,
        factor_values: pd.Series,
        industry_labels: pd.Series,
    ) -> pd.Series:
        """
        行业均值中性化。
        
        Args:
            factor_values: 因子值 (index=品种/股票)
            industry_labels: 行业标签 (index=品种/股票)
            
        Returns:
            中性化后的因子值
        """
        industry_mean = factor_values.groupby(industry_labels).transform("mean")
        return factor_values - industry_mean
    
    def neutralize_by_zscore(
        self,
        factor_values: pd.Series,
        industry_labels: pd.Series,
    ) -> pd.Series:
        """
        行业 Z-score 中性化。
        
        (factor - industry_mean) / industry_std
        更鲁棒，考虑了行业内部分散度。
        """
        industry_mean = factor_values.groupby(industry_labels).transform("mean")
        industry_std = factor_values.groupby(industry_labels).transform("std")
        return (factor_values - industry_mean) / (industry_std + 1e-10)
    
    def neutralize_by_regression(
        self,
        factor_values: pd.Series,
        industry_dummies: pd.DataFrame,
    ) -> pd.Series:
        """
        行业回归中性化（最严谨）。
        
        用量化工具更高效:
            import statsmodels.api as sm
            res = sm.OLS(factor_values, industry_dummies).fit()
            return res.resid
        
        但不引入新依赖，用 numpy 实现:
        """
        # 伪逆法求残差
        X = industry_dummies.values.astype(float)
        y = factor_values.values.astype(float)
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        residual = y - X @ beta
        return pd.Series(residual, index=factor_values.index, name=factor_values.name)
    
    def neutralize_market(
        self,
        factor_values: pd.Series,
        market_return: pd.Series,
    ) -> pd.Series:
        """市场中性化 — 去除大盘 Beta 暴露"""
        # 计算因子对市场的 Beta
        # factor_adj = factor - beta * market_return
        pass
```

---

## 6. 模块四：全因子研究报告

### 6.1 report_generator.py

```python
"""
全因子研究报告生成器。

一键对全因子库执行:
  1. 因子计算
  2. IC/ICIR 评估
  3. 分层回测
  4. 衰减分析
  5. 相关性分析（避免冗余因子）
  6. 行业中性化效果对比
  7. 输出排名 + 推荐组合

输出格式:
  - HTML 报告 (可视化)
  - JSON 原始数据
  - 控制台摘要
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from loguru import logger


@dataclass
class FactorRanking:
    """因子排名条目"""
    rank: int
    name: str
    ic_mean: float
    icir: float
    sharpe_q5q1: float      # 分层多空夏普
    turnover: float
    health: str              # "HEALTHY" / "WARNING" / "DECAYED"
    category: str
    is_recommended: bool = False


@dataclass
class FactorResearchReport:
    """完整研究报告"""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 总体统计
    total_factors: int = 0
    healthy_count: int = 0
    warning_count: int = 0
    decayed_count: int = 0
    
    # 因子排名
    top_factors: List[FactorRanking] = field(default_factory=list)
    
    # 推荐组合
    recommended_ic: float = 0.0
    recommended_icir: float = 0.0
    recommended_sharpe: float = 0.0
    
    # 冗余分析
    high_correlation_pairs: List[Tuple[str, str, float]] = field(
        default_factory=list
    )
    
    # 行业暴露
    industry_exposure_before: float = 0.0  # 中性化前最大行业暴露
    industry_exposure_after: float = 0.0   # 中性化后最大行业暴露
    
    # 原始数据 (可选)
    raw_json: str = ""


class FactorReportGenerator:
    """
    全因子研究报告生成器。
    
    用法:
        generator = FactorReportGenerator()
        report = generator.generate(
            factor_functions=factor_dict,  # {"name": compute_fn}
            data=price_data,
            industry_labels=industries,
        )
        print(report.top_factors[:5])
        generator.save_html(report, "factor_report.html")
    """
    
    def __init__(
        self,
        decay_detector=None,
        neutralizer=None,
        analyzer=None,
    ):
        self.decay_detector = decay_detector or FactorDecayDetector()
        self.neutralizer = neutralizer or IndustryNeutralizer()
        self.analyzer = analyzer  # FactorAnalyzer from factor_lab
    
    def generate(
        self,
        factor_functions: Dict[str, Callable],
        data: pd.DataFrame,
        industry_labels: Optional[pd.Series] = None,
        top_n: int = 20,
    ) -> FactorResearchReport:
        """
        执行全因子研究流程。
        
        Pipeline:
          1. 计算所有因子值
          2. 计算各因子 IC/ICIR → FactorRanking
          3. 对排名前 N 的因子做分层回测
          4. 检测因子衰减
          5. 分析因子间相关性
          6. 如果提供了行业标签，做行业中性化并对比
          7. 输出推荐组合（等权/IC加权）
          8. 生成报告
        """
        pass
    
    def _compute_all_factors(
        self,
        factor_functions: Dict[str, Callable],
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """并行计算所有因子"""
        pass
    
    def _rank_factors(
        self,
        factors_df: pd.DataFrame,
        forward_returns: pd.Series,
    ) -> List[FactorRanking]:
        """给所有因子排序"""
        pass
    
    def _detect_redundancy(
        self,
        factors_df: pd.DataFrame,
        correlation_threshold: float = 0.85,
    ) -> List[Tuple[str, str, float]]:
        """检测高度相关的冗余因子对"""
        corr = factors_df.corr().abs()
        pairs = []
        for i in range(len(corr.columns)):
            for j in range(i+1, len(corr.columns)):
                if corr.iloc[i, j] >= correlation_threshold:
                    pairs.append((
                        corr.columns[i], corr.columns[j],
                        round(corr.iloc[i, j], 3),
                    ))
        return pairs
    
    def _build_recommended(
        self,
        rankings: List[FactorRanking],
        max_factors: int = 10,
        max_correlation: float = 0.7,
    ) -> List[FactorRanking]:
        """构建推荐组合 (排名高 + 低相关)"""
        # 从排名最高的开始，逐个加入组合
        # 保持组合内因子间平均相关性 < max_correlation
        pass
    
    def save_html(self, report: FactorResearchReport, path: str):
        """
        输出 HTML 报告。
        
        包含:
          1. 头部总览 (总数/健康/警告/失效)
          2. 因子排名表 (Top 20)
          3. 推荐组合
          4. 冗余因子对
          5. 行业暴露对比图
          6. 健康状态分布
        """
        pass
    
    def save_json(self, report: FactorResearchReport, path: str):
        """输出 JSON 原始数据"""
        pass
    
    def print_summary(self, report: FactorResearchReport):
        """控制台打印摘要"""
        print(f"\n{'='*60}")
        print(f"  因子研究报告 — {report.generated_at[:10]}")
        print(f"{'='*60}")
        print(f"  总因子数: {report.total_factors}")
        print(f"  健康: {report.healthy_count}  |  警告: {report.warning_count}  |  失效: {report.decayed_count}")
        print()
        print(f"  Top 5 因子:")
        for f in report.top_factors[:5]:
            flag = "✅" if f.is_recommended else "  "
            print(f"    {flag} #{f.rank:2d} {f.name:20s}  IC={f.ic_mean:.4f}  ICIR={f.icir:.2f}  H={f.health}")
        print()
        print(f"  推荐组合: IC={report.recommended_ic:.4f}, ICIR={report.recommended_icir:.2f}")
        print(f"{'='*60}")
```

---

## 7. 测试验证

### 7.1 test_factor_mining.py

```python
"""因子挖掘 — 单元测试"""

import pytest
import pandas as pd
import numpy as np
from core.alpha.mining.operator_set import (
    get_operator, get_operators, apply_operator,
    ts_rank, ts_sum, op_add, op_sub,
)

class TestOperatorSet:
    def test_ts_rank_basic(self):
        s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        result = ts_rank(s, d=5)
        assert not result.isna().all()
        assert 0 <= result.iloc[-1] <= 1
    
    def test_ts_sum_basic(self):
        s = pd.Series([1, 2, 3, 4, 5])
        result = ts_sum(s, d=3)
        assert result.iloc[-1] == 12  # 3+4+5
    
    def test_op_add(self):
        a = pd.Series([1, 2, 3])
        b = pd.Series([4, 5, 6])
        assert (op_add(a, b) == pd.Series([5, 7, 9])).all()
    
    def test_operator_registry(self):
        ops = get_operators()
        assert "ts_rank" in ops
        assert "ts_sum" in ops
        assert "op_add" in ops
        assert len(ops) >= 15


class TestGeneticFactorMiner:
    def test_miner_basic(self):
        """测试基本挖掘流程"""
        miner = GeneticFactorMiner()
        data = _make_sample_data(200)
        results = miner.mine(data, n_factors=5, seed=42)
        assert len(results) <= 5
        if len(results) > 0:
            assert hasattr(results[0], 'ic_mean')
            assert hasattr(results[0], 'expression')
    
    def test_miner_different_data(self):
        """不同数据量下稳定"""
        for n in [50, 100, 500]:
            data = _make_sample_data(n)
            miner = GeneticFactorMiner()
            results = miner.mine(data, n_factors=3)
            assert len(results) <= 3
    
    def test_save_and_load(self, tmp_path):
        """保存/加载因子"""
        miner = GeneticFactorMiner()
        data = _make_sample_data(100)
        results = miner.mine(data, n_factors=3)
        path = tmp_path / "mined_factors.json"
        miner.save_factors(results, str(path))
        assert path.exists()
```

### 7.2 test_factor_management.py

```python
"""因子管理 — 单元测试"""

import pytest
import pandas as pd
import numpy as np
from core.alpha.management.factor_decay import (
    FactorDecayDetector, FactorHealth
)
from core.alpha.management.industry_neutral import IndustryNeutralizer


class TestFactorDecay:
    def test_healthy_factor(self):
        """确认健康因子状态正确"""
        detector = FactorDecayDetector()
        # 模拟一个稳定有效的因子
        np.random.seed(42)
        ic_series = pd.Series(np.random.normal(0.05, 0.02, 200))
        # 检查应该返回 HEALTHY
        pass
    
    def test_decayed_factor(self):
        """确认失效因子被识别"""
        pass
    
    def test_batch_check(self):
        """批量检测正常"""
        pass


class TestIndustryNeutralizer:
    def test_neutralize_by_mean(self):
        """行业中性能消除行业偏差"""
        neutralizer = IndustryNeutralizer()
        # 构造一个带行业偏差的因子
        n = 100
        factor = pd.Series(np.random.randn(n))
        industries = pd.Series(
            ["A"] * 40 + ["B"] * 30 + ["C"] * 30
        )
        # 给行业 A 加一个偏移
        factor[:40] += 0.5
        
        neutral = neutralizer.neutralize_by_mean(factor, industries)
        
        # 中性化后各行业均值应接近 0
        for ind in industries.unique():
            mask = industries == ind
            assert abs(neutral[mask].mean()) < 0.1
    
    def test_neutralize_by_zscore(self):
        """Z-score 中性化正常"""
        pass
    
    def test_neutralize_by_regression(self):
        """回归中性化正常"""
        pass
```

---

## 8. 验收标准

| # | 验收项 | 验证方式 |
|---|--------|---------|
| 1 | 算子集合 ≥ 15 个 | `len(get_operators()) >= 15` |
| 2 | 遗传挖掘能产出因子 | `miner.mine(data)` 返回非空列表 |
| 3 | 因子有 IC/ICIR/Sharpe 评估 | 每个 MinedFactor 有完整指标 |
| 4 | 衰减检测能区分健康/失效 | HEALTHY ≠ DECAYED |
| 5 | 行业中性化后各行业均值接近0 | `abs(neutral[mask].mean()) < 0.1` |
| 6 | 报告生成器可输出 HTML/JSON | `save_html()` / `save_json()` 创建文件 |
| 7 | 推荐组合内因子低相关 | 平均相关性 < 0.7 |
| 8 | 无 deap 时回退到随机搜索 | `import deap` 失败时可用 |
| 9 | 所有测试通过 | `pytest tests/unit/test_factor_mining.py tests/unit/test_factor_management.py -v` |

---

## 9. 代码风格要求

1. 类型注解：所有函数参数和返回值必须有类型注解
2. 中文注释 + English API names
3. Google docstring 格式
4. 行宽 100 字符
5. 不修改已有代码的现有函数签名
6. 所有新模块要有 `__init__.py` 导出公共 API
7. 幂等：多次调用不产生副作用

---

## 10. 集成路径

```
已有代码                                 新增代码
─────────                             ─────────
alpha101/  (101个因子)                 mining/operator_set.py  (算子)
FactorLibrary  (因子注册表)              mining/genetic_programming.py (挖掘引擎)
FactorAnalyzer (IC/分层/衰减分析) ───→   management/factor_decay.py
FactorCombiner (等权/IC加权)            management/industry_neutral.py
FactorEvaluator (IC/IR/报告)            management/report_generator.py
                                       └────→ 输出到 research/factor_lab/
```

FactorResearchReport 的输出结果可以被上层消费：
- `signals/` 引擎引入推荐因子作为信号
- `resonance/` 引擎把因子信号加入投票
- `portfolio/` 管理器用因子做权重分配
