# Phase 4 — 策略军火库 + ML 自动迭代 + 反馈闭环 + LLM 智能体 Specification

> 架构师: 冷域 | 开发者: Claude Code | 版本: v1.0
> 本文件包含 5 个独立模块，可并行实现。

---

## 目录

- **A 篇 — 策略目录 + 草稿补齐**
- **B 篇 — ML 自动迭代 Pipeline**
- **C 篇 — 反馈闭环（锦标赛 → 策略/ML）**
- **D 篇 — LLM 智能体集成**
- **E 篇 — ML+期权 一键分析页**

---

# A 篇 — 策略目录 + 草稿补齐

## A.1 现状

```
signals/strategies/
├── __init__.py            # 空
├── trend_strategies.py    ❌ 0 字节 (空文件)
├── trend_extended.py      ❌ 0 字节 (空文件)
├── momentum_strategies.py  ❌ 0 字节
├── momentum_extended.py    ❌ 0 字节
├── breakout_strategies.py  ❌ 0 字节
├── breakout_extended.py    ❌ 0 字节
├── mean_reversion_extended.py ❌ 0 字节 (空文件)
├── arbitrage_carry.py      ❌ 0 字节
├── arbitrage_extended.py   ❌ 0 字节
├── reversal_strategies.py  ❌ 0 字节
├── filter_strategies.py    ❌ 0 字节
└── layer_strategies.py     ❌ 0 字节 (空文件)
```

**全部是空文件**，需要补齐实现。

## A.2 新增/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `signals/strategies/trend_strategies.py` | 🆕 实现 | 趋势跟踪策略族 (补全完整代码) |
| `signals/strategies/trend_extended.py` | 🆕 实现 | 趋势增强版 (多时间框架/自适应) |
| `signals/strategies/momentum_strategies.py` | 🆕 实现 | 动量策略族 |
| `signals/strategies/momentum_extended.py` | 🆕 实现 | 动量增强版 |
| `signals/strategies/breakout_strategies.py` | 🆕 实现 | 突破策略族 |
| `signals/strategies/breakout_extended.py` | 🆕 实现 | 突破增强版 |
| `signals/strategies/mean_reversion_strategies.py` | 🆕 实现 | 均值回归策略族 |
| `signals/strategies/mean_reversion_extended.py` | 🆕 实现 | 均值回归增强版 |
| `signals/strategies/arbitrage_carry.py` | 🆕 实现 | 套利/展期策略 |
| `signals/strategies/arbitrage_extended.py` | 🆕 实现 | 套利增强版 |
| `signals/strategies/reversal_strategies.py` | 🆕 实现 | 反转策略族 |
| `signals/strategies/filter_strategies.py` | 🆕 实现 | 过滤/辅助策略 |
| `signals/strategies/layer_strategies.py` | 🆕 实现 | 分层叠加策略 |
| `signals/catalog.py` | 🆕 新建 | 策略目录系统 (核心!) |
| `signals/strategies/__init__.py` | 🟡 改 | 导出所有策略 |
| `api/routes/strategy_routes.py` | 🆕 新建 | 策略目录 API |
| `frontend/src/pages/StrategyLibrary.tsx` | 🆕 新建 | 策略库前端页 |
| `frontend/src/services/strategyApi.ts` | 🆕 新建 | 策略 API 服务 |

## A.3 策略目录系统 — signals/catalog.py（核心）

```python
"""
策略目录系统 — 让 Agent 可发现/可查询所有策略。

每个策略在注册时自动采集元数据:
  - 名称/分类/描述
  - 适合市态 (trending/ranging/volatile/crash)
  - 时间框架偏好
  - 历史表现 (夏普/胜率/最大回撤)
  - 当前是否活跃

Agent 查询:
    catalog = StrategyCatalog()
    
    # 查适合当前市态的策略
    catalog.query(regime="BULL", top_k=5)
    
    # 查某个品种上表现最好的
    catalog.best_for("RB2510")
    
    # Agent 用自然语言查:
    "给我推荐目前适合螺纹钢的趋势策略"
    → catalog.query(regime="trending", symbol="RB", strategy_type="trend")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import pandas as pd
from loguru import logger


class StrategyType(Enum):
    TREND = "trend"              # 趋势跟踪
    MOMENTUM = "momentum"        # 动量
    BREAKOUT = "breakout"        # 突破
    MEAN_REVERSION = "mean_reversion"  # 均值回归
    ARBITRAGE = "arbitrage"      # 套利
    REVERSAL = "reversal"        # 反转
    FILTER = "filter"            # 过滤/辅助
    LAYER = "layer"              # 分层叠加


class RegimeFit(Enum):
    """策略适合的市态"""
    TRENDING = "trending"        # 趋势市
    RANGING = "ranging"          # 震荡市
    VOLATILE = "volatile"        # 高波动
    CRASH = "crash"              # 崩盘
    RECOVERY = "recovery"        # 复苏
    ALL = "all"                  # 全适应


@dataclass
class StrategyMeta:
    """策略元数据 — 供目录检索"""
    name: str                    # 策略名 (与 registry 一致)
    strategy_type: StrategyType
    chinese_name: str            # 中文名
    description: str             # 一句话描述
    regime_fit: List[RegimeFit]  # 适合市态
    timeframes: List[str]        # 时间框架 ["1m","5m","1d"]
    params: Dict = field(default_factory=dict)
    
    # 运行期更新的字段 (由监控填充)
    sharpe: float = 0.0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    total_trades: int = 0
    is_active: bool = True
    last_used: str = ""
    symbol_performance: Dict[str, float] = field(default_factory=dict)


class StrategyCatalog:
    """
    策略目录 — 单例, 全局可访问。
    
    用法:
        catalog = StrategyCatalog()
        
        # 注册一个策略到目录
        catalog.register(StrategyMeta(
            name="trend_ma", strategy_type=StrategyType.TREND,
            chinese_name="双均线趋势", description="MA5上穿MA20做多...",
            regime_fit=[RegimeFit.TRENDING],
            timeframes=["1d", "4h"],
        ))
        
        # Agent 查询
        results = catalog.query(regime="trending", top_k=3)
        for r in results:
            print(f"{r.chinese_name}: {r.sharpe:.2f}")
    """
    
    def __init__(self):
        self._strategies: Dict[str, StrategyMeta] = {}
    
    def register(self, meta: StrategyMeta):
        self._strategies[meta.name] = meta
        logger.info(f"📋 策略注册: {meta.chinese_name} ({meta.strategy_type.value})")
    
    def query(
        self,
        regime: Optional[str] = None,         # 市态过滤
        strategy_type: Optional[str] = None,  # 策略类型过滤
        symbol: Optional[str] = None,         # 品种过滤
        top_k: int = 10,
        min_sharpe: float = -99,
        active_only: bool = True,
    ) -> List[StrategyMeta]:
        """
        查询策略。
        
        Agent 调用示例:
            catalog.query(regime="BULL", strategy_type="trend", top_k=5)
        """
        results = list(self._strategies.values())
        
        if active_only:
            results = [s for s in results if s.is_active]
        if regime:
            regime_lower = regime.lower()
            results = [s for s in results 
                       if any(r.value == regime_lower for r in s.regime_fit)
                       or RegimeFit.ALL in s.regime_fit]
        if strategy_type:
            results = [s for s in results if s.strategy_type.value == strategy_type]
        if symbol:
            results = [s for s in results 
                       if symbol in s.symbol_performance]
        
        results.sort(key=lambda s: s.sharpe, reverse=True)
        return results[:top_k]
    
    def best_for(
        self, symbol: str, top_k: int = 3
    ) -> List[StrategyMeta]:
        """某个品种上表现最好的策略。"""
        scored = []
        for s in self._strategies.values():
            if symbol in s.symbol_performance:
                scored.append((s.symbol_performance[symbol], s))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:top_k]]
    
    def list_by_type(self) -> Dict[str, List[StrategyMeta]]:
        """按类型分组列出。"""
        result = {}
        for s in self._strategies.values():
            t = s.strategy_type.value
            if t not in result:
                result[t] = []
            result[t].append(s)
        return result
    
    def update_performance(
        self, name: str, sharpe: float = None,
        win_rate: float = None, total_trades: int = None,
    ):
        """更新策略表现 (由监控/锦标赛回调)。"""
        if name in self._strategies:
            if sharpe is not None:
                self._strategies[name].sharpe = sharpe
            if win_rate is not None:
                self._strategies[name].win_rate = win_rate
            if total_trades is not None:
                self._strategies[name].total_trades = total_trades
            self._strategies[name].last_used = str(pd.Timestamp.now())
```

## A.4 策略实现规格

每个策略文件必须:
1. 继承 `signals/base.BaseStrategy`
2. 使用 `@register` 装饰器注册
3. 有完整的 `compute(df, symbol) -> Signal` 实现

### A.4.1 trend_strategies.py — 趋势跟踪策略族

至少包含 3 个策略:

```python
@register
class MASimpleStrategy(BaseStrategy):
    """双均线交叉趋势跟踪。"""
    name = "trend_ma_simple"
    description = "MA5 上穿 MA20 做多, 下穿做空"
    timeframes = ["1d", "4h"]
    
    def compute(self, df, symbol=""):
        close = df["close"]
        ma5 = close.rolling(5).mean()
        ma20 = close.rolling(20).mean()
        # 金叉/死叉检测
        ...

@register
class MACrossSignalStrategy(BaseStrategy):
    """MACD 趋势信号。"""
    name = "trend_macd"
    description = "MACD 柱变正做多, 变负做空"
    ...

@register
class ADXTrendStrategy(BaseStrategy):
    """ADX 趋势强度过滤 + 方向。"""
    name = "trend_adx"
    description = "ADX>25 且有方向时跟随趋势"
    ...
```

### A.4.2 momentum_strategies.py — 动量策略族

```python
@register
class ROCCrossStrategy(BaseStrategy):
    """过去 N 天收益率动量。"""
    name = "momentum_roc"
    description = "过去20天涨幅最大时做多, 跌幅最大时做空"
    ...

@register
class RSIMomentumStrategy(BaseStrategy):
    """RSI 动量。"""
    name = "momentum_rsi"
    description = "RSI>70 超买做空, RSI<30 超卖做多"
    ...

@register
class AvgMomentumStrategy(BaseStrategy):
    """多周期动量综合。"""
    name = "momentum_multi"
    description = "5/10/20 天动量投票"
    ...
```

### A.4.3 breakout_strategies.py — 突破策略族

```python
@register
class DonchianBreakoutStrategy(BaseStrategy):
    """唐奇安通道突破。"""
    name = "breakout_donchian"
    description = "价格突破过去20天最高点做多, 跌破最低点做空"
    ...

@register
class BollingerBreakoutStrategy(BaseStrategy):
    """布林带突破。"""
    name = "breakout_bollinger"
    description = "突破布林上轨做多, 跌破下轨做空"
    ...

@register
class VolumeBreakoutStrategy(BaseStrategy):
    """放量突破。"""
    name = "breakout_volume"
    description = "价格突破 + 成交量放大 2 倍确认"
    ...
```

### A.4.4 其他策略族简要规格

**mean_reversion_strategies.py (均值回归)**:
- `ReversionBollingerStrategy`: 布林带超买超卖回归
- `ReversionRSIStrategy`: RSI 极端值回归
- `ReversionSpreadStrategy`: 价差回归

**arbitrage_carry.py (套利/展期)**:
- `FuturesSpreadStrategy`: 跨期价差套利
- `CrossMarketArbitrageStrategy`: 跨市场价差
- `CarryTradeStrategy`: 展期收益策略

**reversal_strategies.py (反转)**:
- `PriceReversalStrategy`: 涨跌停/极值反转
- `VolumeClimaxStrategy`: 天量反转
- `GapFillStrategy`: 跳空回补

**filter_strategies.py (过滤/辅助)**:
- `VolatilityFilterStrategy`: 波动率过高时不开仓
- `TrendFilterStrategy`: 无趋势时不开仓
- `TimeFilterStrategy`: 特定时段/日期不开仓

**layer_strategies.py (分层叠加)**:
- `MultiTimeframeStrategy`: 多周期信号叠加
- `ConfirmationStrategy`: 多个策略同时确认才开仓
- `WeightedVoteStrategy`: 多策略加权投票

## A.5 前端 — 策略库页面

`frontend/src/pages/StrategyLibrary.tsx`:

```
┌─────────────────────────────────────────────────┐
│  📋 策略军火库                                     │
│  ┌─────────────────────────────────────────────┐ │
│  │ 过滤: [全部] [趋势] [动量] [突破] [反转] ...  │ │
│  │ 市态: [全部] [趋势市] [震荡市] [高波动]       │ │
│  │ 搜索: [输入策略名...]                       │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │ 趋势跟踪 (5)              活跃:4 停用:1     │ │
│  │ ┌───────────┬──────┬─────┬──────┬────────┐ │ │
│  │ │ 策略       │ 夏普  │ 胜率 │ 交易 │ 适合   │ │
│  │ ├───────────┼──────┼─────┼──────┼────────┤ │ │
│  │ │ 双均线趋势 │ 1.23 │ 58% │ 45   │ 趋势市  │ │ │
│  │ │ MACD 趋势  │ 0.89 │ 52% │ 32   │ 趋势市  │ │ │
│  │ │ ADX 趋势   │ 1.05 │ 55% │ 28   │ 趋势市  │ │ │
│  │ └───────────┴──────┴─────┴──────┴────────┘ │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  Agent 查询入口:                                   │
│  ┌─────────────────────────────────────────┐     │
│  │ 观山: 正在使用 trend_ma_simple + ...     │     │
│  │ 楚风: 正在使用 reversion_bollinger      │     │
│  │ 听海: 正在使用 volatility_short         │     │
│  │ 牧野: 综合调用 5 个策略                  │     │
│  └─────────────────────────────────────────┘     │
└─────────────────────────────────────────────────┘
```

---

# B 篇 — ML 自动迭代 Pipeline

## B.1 现状

ML 模块已有:
- 特征工程: ✅
- 模型注册中心: ✅
- 超参搜索: ✅
- 模型集成: ✅
- Sklearn 模型: ✅

缺的:
- ❌ 自动重训 (模型训练完就再也不更新)
- ❌ 模型性能监控 (不知道模型什么时候退化)
- ❌ 自动模型选择 (多个模型自动选最优)
- ❌ 定时触发 (每天收盘后自动重训)

## B.2 新增文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `ml/auto_pipeline.py` | 🆕 新建 | 自动重训 Pipeline + 调度 |
| `ml/model_monitor.py` | 🆕 新建 | 模型性能监控 (退化检测) |
| `ml/model_selector.py` | 🆕 新建 | 自动模型选择器 |
| `api/routes/ml_routes.py` | 🆕 新建 | ML 状态 API |
| `frontend/src/pages/ML.tsx` | 🟡 改 | ML 仪表盘升级 |

## B.3 ml/auto_pipeline.py — 自动重训 Pipeline

```python
"""
自动 ML Pipeline — 定期重训 + 模型选择 + 性能监控。

调度流程 (可 cron 触发):
  1. 采集最新数据
  2. 构建特征
  3. 训练多个候选模型
  4. 交叉验证评估
  5. 选最优模型 → 注册到 ModelRegistry
  6. 监控旧模型性能 → 退化则自动替换

用法:
    pipeline = AutoMLPipeline()
    result = pipeline.run(symbol="RB2510")
    # → 新模型已注册, 旧模型已归档
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from loguru import logger

from ml.registry import ModelRegistry
from ml.features.pipeline import FeaturePipeline
from ml.features.technical_features import TechnicalFeatureSet
from ml.hyperopt import HyperoptSearcher
from ml.models.sklearn_wrapper import SklearnModel


@dataclass
class AutoMLResult:
    """一次自动重训的结果"""
    symbol: str
    best_model_name: str
    best_model_type: str
    best_score: float
    candidates_trained: int
    old_model_replaced: bool
    feature_count: int
    data_points: int


class AutoMLPipeline:
    """
    自动 ML Pipeline。
    
    用法 (cron 每日收盘后):
        pipeline = AutoMLPipeline()
        result = pipeline.run("RB2510")
        print(f"新模型: {result.best_model_name} (score={result.best_score:.4f})")
    """
    
    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        searcher: Optional[HyperoptSearcher] = None,
    ):
        self.registry = registry or ModelRegistry()
        self.searcher = searcher or HyperoptSearcher()
        self.feature_pipeline = FeaturePipeline()
        self.feature_pipeline.register_module(TechnicalFeatureSet())
    
    def run(
        self,
        symbol: str,
        data: Optional[pd.DataFrame] = None,
        candidate_types: List[str] = None,
        n_trials: int = 10,
    ) -> AutoMLResult:
        """
        执行一次完整的自动重训。
        
        流程:
          1. 获取/接收行情数据
          2. 构建特征矩阵
          3. 准备标签 (未来 N 天收益)
          4. 对每个候选模型类型:
             a. 超参搜索
             b. 交叉验证
             c. 记录最佳分数
          5. 选择最佳模型
          6. 与 ModelRegistry 中已有模型比较
          7. 如果更好 → 注册新版本
        """
        # 1. 数据
        # 2. 特征
        # 3. 训练多个模型
        # 4. 选优
        # 5. 注册
        pass
    
    def train_candidate(
        self, model_type: str, X_train, y_train, X_val, y_val
    ) -> tuple:
        """训练一个候选模型 + 超参搜索。"""
        pass


# ──── 便捷 CLI ────
# python -m ml.auto_pipeline --symbol RB2510 --candidates rf,lgbm,xgb
```

## B.4 ml/model_monitor.py — 模型性能监控

```python
"""
模型性能监控 — 检测模型退化, 触发自动重训。

检测指标:
  - 滚动预测 IC 是否下降 (与上线时比较)
  - 预测误差是否增大
  - 特征分布是否漂移 (data drift)

用法:
    monitor = ModelMonitor()
    report = monitor.check("lgb_rb_v3", new_data, new_predictions)
    if report.needs_retrain:
        pipeline.run("RB2510")
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class MonitorReport:
    model_name: str
    current_ic: float
    baseline_ic: float
    ic_decay: float          # 负值 = 退化
    prediction_error: float
    data_drift_score: float  # 0~1
    needs_retrain: bool
    reason: str = ""


class ModelMonitor:
    """
    模型性能监控。
    
    对比当前性能与注册时保存的 baseline 性能。
    """
    
    def __init__(self, decay_threshold: float = -0.3):
        """
        Args:
            decay_threshold: IC 衰减超过此值触发重训
        """
        self.decay_threshold = decay_threshold
    
    def check(
        self,
        model_name: str,
        predictions: np.ndarray,
        actuals: np.ndarray,
        baseline_ic: Optional[float] = None,
    ) -> MonitorReport:
        """
        检查模型是否退化。
        
        Args:
            model_name: 模型名
            predictions: 最近 N 次预测值
            actuals: 对应的实际值
            baseline_ic: 注册时的 IC (如不提供从 registry 读取)
        """
        current_ic = float(np.corrcoef(predictions, actuals)[0, 1]) \
            if len(predictions) > 2 else 0.0
        # ... 计算退化
        pass
    
    def batch_check(self, registry) -> List[MonitorReport]:
        """检查所有已注册模型。"""
        pass
```

## B.5 ml/model_selector.py — 自动模型选择

```python
"""
自动模型选择器 — 从多个候选模型中选最优。

策略:
  - 滚动窗口 IC 对比
  - 集成 vs 单模型对比
  - 复杂度惩罚 (防止过拟合)

用法:
    selector = ModelSelector()
    best = selector.select(models_dict, X_val, y_val)
    # → {"rf_lgbm_ensemble": 0.62}  (选 ensemble)
"""

class ModelSelector:
    def select(
        self,
        models: Dict[str, object],
        X_val, y_val,
        metric: str = "ic",
    ) -> str:
        """从多个模型中选择最佳。"""
        pass
    
    def select_with_hyperopt(
        self, candidate_types, X_train, y_train, X_val, y_val
    ) -> str:
        """超参搜索 + 选优一步完成。"""
        pass
```

---

# C 篇 — 反馈闭环（锦标赛 → 策略/ML）

## C.1 现状

锦标赛系统有 `tournament/` (4 文件)：
- 策略在锦标赛中 PK
- 有排名/评分
- 但结果**没有回流**到策略系统和 ML 系统

## C.2 新增/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `core/feedback_loop.py` | 🆕 新建 | 反馈闭环核心 (锦标赛→策略/ML) |
| `core/feedback_config.py` | 🆕 新建 | 反馈参数配置 |
| `api/routes/feedback_routes.py` | 🆕 新建 | 反馈状态 API |
| `frontend/src/pages/Feedback.tsx` | 🆕 新建 | 反馈可视化面板 |
| `tournament/tournament_manager.py` | 🟡 改 | 赛后触发反馈 |
| `signals/catalog.py` | 🟡 改 | 接收表现更新 |

## C.3 core/feedback_loop.py — 反馈闭环

```python
"""
反馈闭环 — 锦标赛结果 → 策略权重/ML 迭代。

流程:
  锦标赛结束
    │
    ▼
  收集所有参赛策略的完整表现数据
    │
    ├──→ 更新 StrategyCatalog 中每个策略的 sharpe/win_rate
    │
    ├──→ 表现差的策略 → 自动降低权重或停用
    │
    ├──→ ML 模型: 用锦标赛数据作为新训练样本
    │
    └──→ 生成反馈报告 → 存入反馈历史
    
Agent 查询:
    牧野可以问:
    "过去一周哪个策略表现最好?"
    "trend_ma_simple 最近是不是失效了?"
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from loguru import logger


@dataclass
class FeedbackEntry:
    """一次反馈记录"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tournament_id: str = ""
    n_strategies: int = 0
    top_strategy: str = ""
    top_sharpe: float = 0.0
    worst_strategy: str = ""
    worst_sharpe: float = 0.0
    strategies_retired: List[str] = field(default_factory=list)
    models_retrained: int = 0


class FeedbackLoop:
    """
    反馈闭环 — 锦标赛 → 策略/ML。
    
    用法:
        loop = FeedbackLoop()
        
        # 锦标赛结束后调用
        loop.process_tournament_results(results)
        
        # 查询反馈历史
        loop.get_history(limit=10)
    """
    
    def __init__(
        self,
        catalog=None,
        ml_pipeline=None,
        registry=None,
    ):
        self.catalog = catalog      # StrategyCatalog
        self.ml_pipeline = ml_pipeline  # AutoMLPipeline
        self.registry = registry    # ModelRegistry
        self.history: List[FeedbackEntry] = []
    
    def process_tournament_results(self, results):
        """
        处理锦标赛结果。
        
        Args:
            results: 锦标赛结果数据, 含每个策略的表现
        """
        entry = FeedbackEntry(tournament_id=results.get("id", ""))
        
        for strategy_result in results.get("strategies", []):
            name = strategy_result["name"]
            sharpe = strategy_result.get("sharpe", 0)
            win_rate = strategy_result.get("win_rate", 0)
            trades = strategy_result.get("total_trades", 0)
            
            # 1. 更新策略目录
            if self.catalog:
                self.catalog.update_performance(
                    name, sharpe=sharpe, win_rate=win_rate,
                    total_trades=trades,
                )
            
            # 2. 策略退化判定
            if sharpe < -0.5:
                entry.strategies_retired.append(name)
                logger.warning(f"⚠️ 策略 {name} 持续失效, 建议下线")
        
        entry.n_strategies = len(results.get("strategies", []))
        # ... 更新 ML 模型
        
        self.history.append(entry)
        return entry
    
    def get_strategy_rankings(
        self, min_trades: int = 10
    ) -> List[Dict]:
        """获取策略表现排名 (锦标赛验证后)。"""
        pass
    
    def get_history(self, limit: int = 20) -> List[FeedbackEntry]:
        return self.history[-limit:]
```

---

# D 篇 — LLM 智能体集成

## D.1 现状

`core/llm/` 已有 14 个文件，包含:
- `llm_client.py`, `market_analyzer.py`
- `strategy_generator.py`, `strategy_factory.py`
- Providers: OpenAI, Anthropic, Ollama

缺的:
- ❌ 策略目录 → LLM prompt 模板 (让 LLM 能理解策略库)
- ❌ Agent → LLM 查询接口 (四大金刚怎么调 LLM)
- ❌ LLM 生成策略 → 自动注册到目录
- ❌ 前端 LLM 配置页

## D.2 新增/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `core/llm/strategy_advisor.py` | 🆕 新建 | LLM 策略建议器 |
| `core/llm/strategy_agent_prompt.py` | 🆕 新建 | Agent prompt 模板 |
| `core/llm/config_schema.py` | 🆕 新建 | LLM 配置架构 |
| `api/routes/llm_routes.py` | 🟡 改 | 新增 Agent 接口 |
| `frontend/src/pages/LLMConfig.tsx` | 🆕 新建 | LLM 配置页 |
| `.env.example` | 🟡 改 | 添加 LLM API key 说明 |

## D.3 core/llm/strategy_advisor.py

```python
"""
LLM 策略建议器 — 让 LLM 理解当前策略状态并给出建议。

功能:
  1. 分析当前市场状态 → 推荐匹配的策略
  2. 解释为什么某个策略在某个品种上有效/失效
  3. 根据用户描述生成新策略草稿

用法:
    advisor = LLMStrategyAdvisor()
    
    # Agent 查询
    advice = advisor.ask("螺纹钢目前适合用什么策略?")
    print(advice)
    # → "基于当前市场状态(趋势市), 推荐trend_ma_simple...
    #    该策略近一周夏普1.23, 在RB上表现稳定"
"""

from typing import Dict, List, Optional
from loguru import logger


class LLMStrategyAdvisor:
    """
    LLM 驱动的策略建议器。
    
    将策略目录 + 市场状态 + 历史表现 打包为 prompt,
    让 LLM 给出可执行的建议。
    """
    
    def __init__(
        self,
        catalog=None,
        llm_client=None,
        model: str = "auto",
    ):
        self.catalog = catalog
        self.llm_client = llm_client
        self.model = model
    
    def ask(
        self,
        question: str,
        context: Optional[Dict] = None,
    ) -> str:
        """
        向 LLM 查询策略建议。
        
        Args:
            question: 自然语言问题
            context: 上下文 (当前市态/品种/持仓等)
            
        Returns:
            LLM 回答
        """
        prompt = self._build_prompt(question, context)
        return self._call_llm(prompt)
    
    def _build_prompt(self, question, context) -> str:
        """构建包含策略目录上下文的 prompt。"""
        catalog_context = ""
        if self.catalog:
            strategies = self.catalog.list_by_type()
            catalog_context = f"""
当前策略库概览:
{self._format_catalog_for_llm(strategies)}

查询要求: {question}
"""
        return catalog_context
    
    def _format_catalog_for_llm(self, strategies: Dict) -> str:
        """格式化为 LLM 可读的文本。"""
        lines = []
        for stype, strats in strategies.items():
            lines.append(f"[{stype}]")
            for s in strats[:3]:  # 每类最多3个
                lines.append(
                    f"  - {s.chinese_name} ({s.name}): "
                    f"夏普={s.sharpe:.2f}, 胜率={s.win_rate:.1%}, "
                    f"适合={[r.value for r in s.regime_fit]}"
                )
            if len(strats) > 3:
                lines.append(f"  ... 还有 {len(strats)-3} 个")
        return "\n".join(lines)
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM。"""
        if self.llm_client:
            return self.llm_client.chat(prompt)
        return "[LLM 未配置] 请先在设置中配置 LLM API"
    
    def generate_strategy(
        self, description: str
    ) -> Dict:
        """
        根据自然语言描述生成策略草稿。
        
        例如:
            "我想做一个策略, 当价格突破20日高点且成交量放大2倍时做多"
            → 返回策略代码模板
        """
        prompt = f"""
根据以下描述生成一个策略类的 Python 代码。
描述: {description}

要求:
- 继承 BaseStrategy
- 使用 @register 装饰器
- 包含完整的 compute 方法
- 添加中文注释

只返回代码, 不返回解释。
"""
        code = self._call_llm(prompt)
        return {"code": code, "description": description}
```

## D.4 前端 LLM 配置页

```
LLM 配置:
┌─────────────────────────────────────┐
│ 提供商: [OpenAI ▼]                  │
│ 模型:   [gpt-4o         ▼]          │
│ API Key: [••••••••••••••••]         │
│ 基础URL: [https://api.openai.com/v1]│
│                                      │
│ 测试连接: [🔄 测试]                  │
│ 状态: ✅ 连接正常                     │
│                                      │
│ 可用功能:                             │
│  ✅ 策略建议  ✅ 市场分析  ✅ 代码生成 │
└─────────────────────────────────────┘

Agent 对话:
┌─────────────────────────────────────┐
│ 观山: 当前趋势市, 推荐 trend_adx    │
│       (夏普1.05, 适合趋势市)         │
│                                      │
│ 楚风: 我想试一个反转策略,             │
│       帮我生成一个代码模板            │
│ ┌─────────────────────────────────┐ │
│ │ LLM: 已生成 reversal_pinbar     │ │
│ │      策略, 已注册到目录          │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

# E 篇 — ML+期权 一键分析页

## E.1 目标

像因子研究一样，输入合约代码 → 给出 ML 预测结论 + 期权分析结论。

## E.2 新增/修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `api/routes/ml_routes.py` | 🆕 新建 | ML 分析 API (含 full-analysis) |
| `api/routes/phase3_routes.py` | 🟡 改 | 期权分析 API 增强 |
| `frontend/src/pages/MLAnalyzer.tsx` | 🆕 新建 | ML+期权一键分析页 |
| `frontend/src/App.tsx` | 🟡 改 | 添加菜单路由 |

## E.3 前端页面

菜单新增:
```
📊 因子研究     (原有)
🧠 ML+期权分析   (新增)
📋 策略军火库   (新增)
🔄 反馈闭环     (新增)
⚙️ LLM 配置     (新增)
```

ML+期权分析页面:

```
┌─────────────────────────────────────────────┐
│  🧠 ML + 期权 完整分析                        │
│                                             │
│  ┌─────────────────────────┐ ┌────────────┐ │
│  │ 输入合约代码: RB2510     │ │  🧠 分析   │ │
│  └─────────────────────────┘ └────────────┘ │
│  ⚡ 数据直连仓库 · ML预测 + 期权分析          │
└─────────────────────────────────────────────┘

加载完成后展示:

┌─ 🤖 ML 预测结论 ───────────────────────────┐
│  🟢 未来5天预测上涨 +2.3%                    │
│  置信度: 中高 (ICIR=0.68)                   │
│  模型: rf_ensemble v3 (2024-06-19 训练)      │
│  特征: 22个技术面特征                        │
│  模型健康: ✅ 正常 (IC衰减 -0.05)             │
└─────────────────────────────────────────────┘

┌─ 🎯 期权分析结论 ───────────────────────────┐
│  IV Rank: 65% (中等)                        │
│  Skew: +0.08 (Put轻微溢价, 正常)            │
│  期限结构: Contango (远月贵近月)              │
│  套利信号: 1个                               │
│    ⚠️ K=3800 IV异常凸起 (+3.2%)             │
│  联合策略建议:                                │
│    🟢 看多 → covered_call (卖Call收权利金)   │
│    理由: IV偏高, 用卖Call增厚持仓收益         │
└─────────────────────────────────────────────┘

┌─ 📈 详细图表 ───────────────────────────────┐
│  [ML 预测 vs 实际曲线]  [期权波动率曲面]       │
│  [策略选择决策树]        [特征重要性排行]       │
└─────────────────────────────────────────────┘
```

## E.4 后端 API

```python
@router.post("/ml-options/analyze")
async def ml_options_analyze(request: AnalysisRequest):
    """
    ML + 期权 一键分析。
    
    返回:
      ml_prediction: 未来N天预测方向+置信度
      option_analysis: IV/skew/期限结构/套利信号
      combo_advice: 联合策略建议
    """
```

## E.5 前端数据结构

```typescript
interface MLAnalysisResult {
  symbol: string;
  ml_prediction: {
    direction: "BUY" | "SELL" | "HOLD";
    confidence: string;        // "高" | "中高" | "中" | "低"
    confidence_score: number;  // 0~1
    predicted_return: number;  // 预测收益率
    model_name: string;
    model_health: string;      // "HEALTHY" | "WARNING" | "DECAYED"
    feature_count: number;
    trained_at: string;
  };
  option_analysis: {
    iv_rank: number;
    skew: number;
    term_structure: "CONTANGO" | "BACKWARD" | "FLAT";
    arb_signals: Array<{
      type: string;
      direction: string;
      score: number;
      reason: string;
    }>;
  };
  combo_advice: {
    strategy_name: string;
    direction: string;
    reason: string;
    risk_notes: string;
  };
}
```

---

## 验收标准

| # | 验收项 | 归属 | 验证方式 |
|---|--------|------|---------|
| 1 | 全部策略文件有完整实现, 非 0 字节 | A | `wc -c signals/strategies/*.py` 均 > 100 |
| 2 | 策略目录可查询 (按市态/类型/品种) | A | `catalog.query(regime="BULL")` 返回结果 |
| 3 | 前端的策略库页面展示所有策略 | A | 页面显示 7 个分类 + 各策略数据 |
| 4 | 自动重训 Pipeline 可运行 | B | `pipeline.run("RB2510")` 返回 AutoMLResult |
| 5 | 模型监控可检测退化 | B | 伪造退化数据 → `needs_retrain=True` |
| 6 | 锦标赛结果触发策略目录更新 | C | 赛后 `catalog` 中 sharpe 更新 |
| 7 | LLM 策略建议器可回答策略问题 | D | `advisor.ask("推荐趋势策略")` 返回非空 |
| 8 | LLM 配置页可保存 API key | D | 配置保存后可用 |
| 9 | ML+期权分析输入代码出结论 | E | 输入 RB2510 → 展示 ML 结论+期权分析 |
| 10 | 所有测试通过 | AB | `pytest tests/` 无失败 |
