# 策略智能化全栈升级实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对交易策略中心进行智能化升级，实现自适应参数、强化学习、Alpha挖掘、市场状态预测、策略组合智能五大功能模块

**Architecture:** 新增`core/adaptive/`、`core/alpha/`、`core/rl/`三个模块，重构`core/market_state/`、`core/resonance/`、`core/evolution/`三个现有模块，修复ML Pipeline和策略引擎的关键问题

**Tech Stack:** Python 3.11+, optuna, hmmlearn, gymnasium, torch, pandas, numpy, scikit-learn

---

## Phase 1: 基础修复与框架搭建 (Week 1-2)

### Task 1: 修复ML Pipeline命名欺诈

**Files:**
- Modify: `ml/pipeline.py:46`
- Test: `tests/unit/test_ml_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_ml_pipeline.py
import pytest
from ml.pipeline import MLPipeline

def test_pipeline_uses_xgboost_not_random_forest():
    """验证pipeline确实使用XGBoost而非RandomForest"""
    pipeline = MLPipeline()
    
    # 检查模型类型
    assert hasattr(pipeline, 'models')
    
    # 创建测试数据
    import pandas as pd
    import numpy as np
    np.random.seed(42)
    n_samples = 100
    test_data = pd.DataFrame({
        'open': np.random.randn(n_samples).cumsum() + 100,
        'high': np.random.randn(n_samples).cumsum() + 101,
        'low': np.random.randn(n_samples).cumsum() + 99,
        'close': np.random.randn(n_samples).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, n_samples)
    })
    
    # 训练pipeline
    pipeline.train(test_data)
    
    # 检查xgboost层是否使用了正确的模型
    from xgboost import XGBRegressor
    assert isinstance(pipeline.models.get('xgboost'), XGBRegressor), \
        "XGBoost层应该使用XGBRegressor而非RandomForestRegressor"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_ml_pipeline.py::test_pipeline_uses_xgboost_not_random_forest -v`
Expected: FAIL with assertion error

- [ ] **Step 3: Write minimal implementation**

```python
# ml/pipeline.py 修改
# 找到xgboost层的实现，将RandomForestRegressor替换为XGBRegressor

# 原代码:
# self.models['xgboost'] = RandomForestRegressor(n_estimators=100)

# 修改为:
from xgboost import XGBRegressor
self.models['xgboost'] = XGBRegressor(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_ml_pipeline.py::test_pipeline_uses_xgboost_not_random_forest -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ml/pipeline.py tests/unit/test_ml_pipeline.py
git commit -m "fix: replace RandomForest with XGBoost in ML pipeline"
```

---

### Task 2: 补全Signal dataclass字段

**Files:**
- Modify: `signals/base.py`
- Test: `tests/unit/test_signal.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_signal.py
import pytest
from datetime import datetime
from signals.base import Signal

def test_signal_has_required_fields():
    """验证Signal包含所有必需字段"""
    signal = Signal(
        strategy_name="test_strategy",
        symbol="RB2410",
        direction="BUY",
        confidence=0.8,
        score=5.0,
        price=3850.0,
        timestamp=datetime.now(),
        reason="测试信号",
        source_system="guanshan",
        resonance_layer="trend",
        metadata={"atr": 50.0}
    )
    
    assert signal.source_system == "guanshan"
    assert signal.score == 5.0
    assert signal.resonance_layer == "trend"
    assert signal.metadata == {"atr": 50.0}

def test_signal_default_values():
    """验证Signal默认值"""
    signal = Signal(
        strategy_name="test",
        symbol="RB2410",
        direction="BUY",
        confidence=0.8,
        score=5.0,
        price=3850.0,
        timestamp=datetime.now(),
        reason="test"
    )
    
    assert signal.source_system == ""
    assert signal.resonance_layer == ""
    assert signal.metadata == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_signal.py -v`
Expected: FAIL with TypeError (unexpected keyword argument)

- [ ] **Step 3: Write minimal implementation**

```python
# signals/base.py 修改
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Dict, Any

@dataclass
class Signal:
    strategy_name: str
    symbol: str
    direction: Literal["BUY", "SELL", "HOLD"]
    confidence: float  # 0.0 ~ 1.0
    score: float  # -10 ~ +10（共振加权用）
    price: float
    timestamp: datetime
    reason: str
    source_system: str = ""  # "guanshan" / "chufeng" / "tinghai"
    resonance_layer: str = ""  # 共振层信息
    metadata: Dict[str, Any] = field(default_factory=dict)  # 扩展字段
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_signal.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add signals/base.py tests/unit/test_signal.py
git commit -m "feat: add source_system, score, resonance_layer, metadata fields to Signal"
```

---

### Task 3: 修复共振引擎分组逻辑

**Files:**
- Modify: `resonance/engine.py`
- Test: `tests/unit/test_resonance.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_resonance.py
import pytest
from datetime import datetime
from signals.base import Signal
from resonance.engine import ResonanceEngine

def test_resonance_engine_groups_by_source_system():
    """验证共振引擎按source_system分组而非随机分组"""
    engine = ResonanceEngine()
    
    # 创建来自不同系统的信号
    signals = [
        Signal("strategy1", "RB", "BUY", 0.8, 5.0, 3850, datetime.now(), "test", source_system="guanshan"),
        Signal("strategy2", "RB", "SELL", 0.7, -3.0, 3850, datetime.now(), "test", source_system="chufeng"),
        Signal("strategy3", "RB", "BUY", 0.9, 7.0, 3850, datetime.now(), "test", source_system="tinghai"),
    ]
    
    # 计算共振
    result = engine.calculate("RB", signals, "TRENDING")
    
    # 验证分组正确
    assert hasattr(result, 'score_G')
    assert hasattr(result, 'score_C')
    assert hasattr(result, 'score_T')
    
    # 验证分数不是随机分配的
    assert result.score_G != result.score_C  # 不同系统应该有不同分数

def test_signal_without_source_system_gets_inferred():
    """验证没有source_system的信号能被正确推断"""
    engine = ResonanceEngine()
    
    signals = [
        Signal("trend_ma_cross", "RB", "BUY", 0.8, 5.0, 3850, datetime.now(), "test"),
        Signal("reversal_rsi", "RB", "SELL", 0.7, -3.0, 3850, datetime.now(), "test"),
    ]
    
    result = engine.calculate("RB", signals, "TRENDING")
    
    # trend_ma_cross应该被推断为chufeng
    # reversal_rsi应该被推断为chufeng
    assert result.score_C != 0  # 应该有分数
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_resonance.py -v`
Expected: FAIL with assertion error

- [ ] **Step 3: Write minimal implementation**

```python
# resonance/engine.py 修改
def _group_signals_by_source(self, signals):
    """按source_system字段分组，而非随机分组"""
    groups = {"guanshan": [], "chufeng": [], "tinghai": []}
    
    for signal in signals:
        source = getattr(signal, 'source_system', None)
        if source and source in groups:
            groups[source].append(signal)
        else:
            # 根据strategy_name推断来源
            inferred = self._infer_source(signal.strategy_name)
            groups[inferred].append(signal)
    
    return groups

def _infer_source(self, strategy_name):
    """根据策略名推断来源系统"""
    # 观山策略前缀
    guanshan_prefixes = ['TT7_', 'OI_', 'Enhanced_']
    # 楚风策略前缀
    chufeng_prefixes = ['trend_', 'reversal_', 'breakout_', 'momentum_']
    # 听海策略前缀
    tinghai_prefixes = ['filter_', 'layer_', 'chan_', 'ml_']
    
    for prefix in guanshan_prefixes:
        if strategy_name.startswith(prefix):
            return "guanshan"
    for prefix in chufeng_prefixes:
        if strategy_name.startswith(prefix):
            return "chufeng"
    for prefix in tinghai_prefixes:
        if strategy_name.startswith(prefix):
            return "tinghai"
    
    return "chufeng"  # 默认

def _score_signals(self, signals):
    """计算信号分数，考虑confidence差异"""
    if not signals:
        return 0.0
    
    total_score = 0.0
    total_weight = 0.0
    
    for signal in signals:
        # 使用confidence作为权重
        weight = signal.confidence
        total_score += signal.score * weight
        total_weight += weight
    
    return total_score / (total_weight + 1e-8) if total_weight > 0 else 0.0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_resonance.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add resonance/engine.py tests/unit/test_resonance.py
git commit -m "fix: group signals by source_system instead of random assignment"
```

---

### Task 4: 创建adaptive模块目录结构

**Files:**
- Create: `core/adaptive/__init__.py`
- Create: `core/adaptive/bayesian_optimizer.py`
- Create: `core/adaptive/regime_aware_optimizer.py`
- Create: `core/adaptive/walk_forward_validator.py`
- Create: `core/adaptive/parameter_store.py`
- Create: `core/adaptive/scheduler.py`

- [ ] **Step 1: Create directory and __init__.py**

```bash
mkdir -p core/adaptive
```

```python
# core/adaptive/__init__.py
from .bayesian_optimizer import BayesianOptimizer
from .regime_aware_optimizer import RegimeAwareOptimizer
from .walk_forward_validator import WalkForwardValidator
from .parameter_store import ParameterStore
from .scheduler import OptimizationScheduler

__all__ = [
    'BayesianOptimizer',
    'RegimeAwareOptimizer', 
    'WalkForwardValidator',
    'ParameterStore',
    'OptimizationScheduler'
]
```

- [ ] **Step 2: Create bayesian_optimizer.py skeleton**

```python
# core/adaptive/bayesian_optimizer.py
import logging
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class OptimizationResult:
    """优化结果"""
    best_params: Dict[str, Any]
    best_score: float
    history: List[Dict[str, Any]]
    duration_seconds: float
    n_trials: int

class BayesianOptimizer:
    """基于贝叶斯优化的参数搜索"""
    
    def __init__(self, objective_fn: Callable, param_space: Dict, n_trials: int = 100):
        self.objective_fn = objective_fn
        self.param_space = param_space
        self.n_trials = n_trials
        self.history = []
        self.best_params = None
        self.best_score = -float('inf')
        self.start_time = None
    
    def optimize(self) -> OptimizationResult:
        """执行优化，返回最优参数"""
        import optuna
        import time
        
        self.start_time = time.time()
        
        def objective(trial):
            params = {}
            for name, space in self.param_space.items():
                if space['type'] == 'int':
                    params[name] = trial.suggest_int(name, space['low'], space['high'])
                elif space['type'] == 'float':
                    params[name] = trial.suggest_float(name, space['low'], space['high'])
                elif space['type'] == 'categorical':
                    params[name] = trial.suggest_categorical(name, space['choices'])
            
            try:
                score = self.objective_fn(params)
                self.history.append({
                    'params': params,
                    'score': score,
                    'trial': len(self.history),
                    'timestamp': datetime.now().isoformat()
                })
                
                if score > self.best_score:
                    self.best_score = score
                    self.best_params = params
                
                return score
            except Exception as e:
                logger.error(f"Trial {len(self.history)} failed: {e}")
                return -float('inf')
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=self.n_trials)
        
        duration = time.time() - self.start_time
        
        return OptimizationResult(
            best_params=self.best_params,
            best_score=self.best_score,
            history=self.history,
            duration_seconds=duration,
            n_trials=len(self.history)
        )
    
    def suggest_next(self) -> Optional[Dict[str, Any]]:
        """建议下一组探索参数"""
        if not self.history:
            # 随机探索第一组
            params = {}
            for name, space in self.param_space.items():
                if space['type'] == 'int':
                    import random
                    params[name] = random.randint(space['low'], space['high'])
                elif space['type'] == 'float':
                    import random
                    params[name] = random.uniform(space['low'], space['high'])
                elif space['type'] == 'categorical':
                    import random
                    params[name] = random.choice(space['choices'])
            return params
        
        # 基于历史数据的EI (Expected Improvement)
        # 简化实现：返回历史最优附近的参数
        if self.best_params:
            import random
            suggested = {}
            for name, value in self.best_params.items():
                space = self.param_space[name]
                if space['type'] == 'int':
                    delta = max(1, (space['high'] - space['low']) // 10)
                    suggested[name] = max(space['low'], min(space['high'], 
                                        value + random.randint(-delta, delta)))
                elif space['type'] == 'float':
                    delta = (space['high'] - space['low']) * 0.1
                    suggested[name] = max(space['low'], min(space['high'],
                                        value + random.uniform(-delta, delta)))
                else:
                    suggested[name] = value
            return suggested
        
        return None
    
    def update(self, result: Dict[str, Any]):
        """更新优化器状态"""
        self.history.append(result)
        if result['score'] > self.best_score:
            self.best_score = result['score']
            self.best_params = result['params']
```

- [ ] **Step 3: Create other module skeletons**

```python
# core/adaptive/regime_aware_optimizer.py
"""市场状态感知的参数优化器"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RegimeAwareOptimizer:
    """根据市场状态切换参数"""
    
    def __init__(self):
        self.regime_params = {}  # {regime: {strategy: params}}
        self.current_regime = None
    
    def optimize_by_regime(self, symbol: str, strategy: str, regime: str) -> Dict[str, Any]:
        """为特定市场状态优化参数"""
        # TODO: 实现
        pass
    
    def switch_regime(self, new_regime: str):
        """市场状态切换时调整参数"""
        if new_regime != self.current_regime:
            self.current_regime = new_regime
            logger.info(f"Regime switched to {new_regime}")
```

```python
# core/adaptive/walk_forward_validator.py
"""Walk-forward验证框架"""
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

class WalkForwardValidator:
    """Walk-forward验证，防止过拟合"""
    
    def __init__(self, n_splits: int = 5, train_ratio: float = 0.7):
        self.n_splits = n_splits
        self.train_ratio = train_ratio
    
    def validate(self, strategy, params: Dict, data: pd.DataFrame) -> Dict[str, Any]:
        """执行walk-forward验证"""
        # TODO: 实现
        pass
    
    def detect_overfitting(self, is_metrics: Dict, oos_metrics: Dict) -> bool:
        """检测过拟合"""
        is_sharpe = is_metrics.get('sharpe', 0)
        oos_sharpe = oos_metrics.get('sharpe_oos', 0)
        return is_sharpe > oos_sharpe * 1.5
```

```python
# core/adaptive/parameter_store.py
"""参数版本管理"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ParameterStore:
    """参数存储，支持版本管理"""
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.cache = {}  # 内存缓存
    
    def save(self, strategy_name: str, params: Dict, metrics: Dict, version: int = None):
        """保存参数版本"""
        if version is None:
            version = self._get_next_version(strategy_name)
        
        record = {
            'strategy_name': strategy_name,
            'version': version,
            'params': params,
            'metrics': metrics,
            'created_at': datetime.now().isoformat(),
            'is_active': True
        }
        
        self.cache[f"{strategy_name}:{version}"] = record
        logger.info(f"Saved params for {strategy_name} v{version}")
    
    def load_latest(self, strategy_name: str) -> Optional[Dict]:
        """加载最新参数"""
        # TODO: 实现数据库查询
        pass
    
    def rollback(self, strategy_name: str, version: int):
        """回滚到指定版本"""
        # TODO: 实现
        pass
    
    def _get_next_version(self, strategy_name: str) -> int:
        """获取下一个版本号"""
        versions = [k.split(':')[1] for k in self.cache.keys() 
                   if k.startswith(f"{strategy_name}:")]
        if versions:
            return max(int(v) for v in versions) + 1
        return 1
```

```python
# core/adaptive/scheduler.py
"""优化调度器"""
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class OptimizationScheduler:
    """优化任务调度"""
    
    def __init__(self):
        self.scheduled_tasks = []
    
    def schedule_daily(self, strategy_list: List[str]):
        """调度每日优化任务"""
        for strategy in strategy_list:
            self.scheduled_tasks.append({
                'strategy': strategy,
                'schedule': 'daily',
                'last_run': None,
                'status': 'pending'
            })
        logger.info(f"Scheduled daily optimization for {len(strategy_list)} strategies")
    
    def schedule_weekly(self, full_reoptimize: bool = True):
        """调度每周优化任务"""
        # TODO: 实现
        pass
    
    def trigger_on_regime_change(self, regime: str):
        """市场状态变化时触发优化"""
        # TODO: 实现
        pass
```

- [ ] **Step 4: Create tests for adaptive module**

```python
# tests/unit/test_adaptive.py
import pytest
from core.adaptive import BayesianOptimizer, ParameterStore

def test_bayesian_optimizer_initialization():
    """测试贝叶斯优化器初始化"""
    def objective(params):
        return params['x'] ** 2
    
    param_space = {
        'x': {'type': 'float', 'low': -10, 'high': 10}
    }
    
    optimizer = BayesianOptimizer(objective, param_space, n_trials=10)
    assert optimizer.n_trials == 10
    assert optimizer.best_score == -float('inf')

def test_parameter_store_save_and_load():
    """测试参数存储"""
    store = ParameterStore()
    
    params = {'atr_period': 14, 'stop_loss': 2.0}
    metrics = {'sharpe': 1.5, 'win_rate': 0.6}
    
    store.save('test_strategy', params, metrics)
    loaded = store.load_latest('test_strategy')
    
    assert loaded is not None
    assert loaded['params'] == params

def test_parameter_store_versioning():
    """测试参数版本管理"""
    store = ParameterStore()
    
    params_v1 = {'atr_period': 14}
    params_v2 = {'atr_period': 20}
    
    store.save('test_strategy', params_v1, {}, version=1)
    store.save('test_strategy', params_v2, {}, version=2)
    
    assert store.cache['test_strategy:1']['params'] == params_v1
    assert store.cache['test_strategy:2']['params'] == params_v2
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/unit/test_adaptive.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add core/adaptive/ tests/unit/test_adaptive.py
git commit -m "feat: create adaptive module with BayesianOptimizer and ParameterStore"
```

---

### Task 5: 创建alpha模块目录结构

**Files:**
- Create: `core/alpha/__init__.py`
- Create: `core/alpha/factor_library.py`
- Create: `core/alpha/factor_evaluator.py`
- Create: `core/alpha/factor_combiner.py`

- [ ] **Step 1: Create directory and __init__.py**

```bash
mkdir -p core/alpha/alpha101
```

```python
# core/alpha/__init__.py
from .factor_library import FactorLibrary
from .factor_evaluator import FactorEvaluator
from .factor_combiner import FactorCombiner

__all__ = ['FactorLibrary', 'FactorEvaluator', 'FactorCombiner']
```

- [ ] **Step 2: Create factor_library.py**

```python
# core/alpha/factor_library.py
import logging
import pandas as pd
from typing import Dict, List, Callable, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FactorMeta:
    """因子元数据"""
    name: str
    category: str
    description: str
    compute_fn: Callable

class FactorLibrary:
    """因子库管理器"""
    
    def __init__(self):
        self.factors: Dict[str, FactorMeta] = {}
        self.compute_fns: Dict[str, Callable] = {}
    
    def register(self, compute_fn: Callable, name: str, category: str, description: str = ""):
        """注册新因子"""
        self.factors[name] = FactorMeta(
            name=name,
            category=category,
            description=description,
            compute_fn=compute_fn
        )
        self.compute_fns[name] = compute_fn
        logger.info(f"Registered factor: {name} ({category})")
    
    def compute_all(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算所有因子"""
        results = {}
        for name, fn in self.compute_fns.items():
            try:
                results[name] = fn(df)
            except Exception as e:
                logger.warning(f"Factor {name} computation failed: {e}")
        return results
    
    def get_factor(self, name: str) -> Callable:
        """获取单个因子"""
        return self.compute_fns.get(name)
    
    def list_factors(self, category: str = None) -> List[FactorMeta]:
        """列出因子"""
        if category:
            return [f for f in self.factors.values() if f.category == category]
        return list(self.factors.values())
```

- [ ] **Step 3: Create factor_evaluator.py**

```python
# core/alpha/factor_evaluator.py
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FactorReport:
    """因子评价报告"""
    name: str
    ic: float
    ir: float
    turnover: float
    half_life: int
    grade: str

class FactorEvaluator:
    """因子有效性评价"""
    
    def calculate_ic(self, factor: pd.Series, returns: pd.Series, method: str = 'spearman') -> float:
        """计算信息系数 (IC)"""
        if method == 'spearman':
            return factor.rank().corr(returns.rank())
        return factor.corr(returns)
    
    def calculate_ir(self, factor: pd.Series, returns: pd.Series, period: int = 20) -> float:
        """计算信息比率 (IR)"""
        rolling_ic = factor.rolling(period).corr(returns)
        return rolling_ic.mean() / (rolling_ic.std() + 1e-8)
    
    def calculate_turnover(self, factor: pd.Series, quantiles: int = 5) -> float:
        """计算因子换手率"""
        try:
            quantile_labels = pd.qcut(factor, quantiles, labels=False, duplicates='drop')
            return (quantile_labels.diff() != 0).mean()
        except:
            return 0.0
    
    def decay_analysis(self, factor: pd.Series, returns: pd.Series, max_lag: int = 20) -> Dict[str, Any]:
        """因子衰减分析"""
        decays = []
        for lag in range(1, max_lag + 1):
            ic = factor.corr(returns.shift(-lag))
            decays.append({'lag': lag, 'ic': ic})
        
        # 找到半衰期
        initial_ic = decays[0]['ic'] if decays else 0
        half_life = max_lag
        for d in decays:
            if abs(d['ic']) < abs(initial_ic) / 2:
                half_life = d['lag']
                break
        
        return {
            'decays': decays,
            'half_life': half_life,
            'is_persistent': decays[4]['ic'] > decays[0]['ic'] * 0.5 if len(decays) > 4 else False
        }
    
    def generate_report(self, name: str, factor: pd.Series, returns: pd.Series) -> FactorReport:
        """生成因子评价报告"""
        ic = self.calculate_ic(factor, returns)
        ir = self.calculate_ir(factor, returns)
        turnover = self.calculate_turnover(factor)
        decay = self.decay_analysis(factor, returns)
        
        # 评级
        if abs(ic) > 0.05 and abs(ir) > 1.0:
            grade = 'A'
        elif abs(ic) > 0.03 and abs(ir) > 0.5:
            grade = 'B'
        elif abs(ic) > 0.02:
            grade = 'C'
        else:
            grade = 'D'
        
        return FactorReport(
            name=name,
            ic=ic,
            ir=ir,
            turnover=turnover,
            half_life=decay['half_life'],
            grade=grade
        )
```

- [ ] **Step 4: Create factor_combiner.py**

```python
# core/alpha/factor_combiner.py
import logging
import pandas as pd
from typing import Dict

logger = logging.getLogger(__name__)

class FactorCombiner:
    """因子组合器"""
    
    def equal_weight(self, factors: Dict[str, pd.Series]) -> pd.Series:
        """等权重组合"""
        combined = pd.DataFrame(factors)
        return combined.mean(axis=1)
    
    def ic_weight(self, factors: Dict[str, pd.Series], returns: pd.Series) -> pd.Series:
        """IC加权组合"""
        from .factor_evaluator import FactorEvaluator
        evaluator = FactorEvaluator()
        
        weights = {}
        for name, factor in factors.items():
            ic = abs(evaluator.calculate_ic(factor, returns))
            weights[name] = ic
        
        # 归一化权重
        total = sum(weights.values())
        if total > 0:
            weights = {k: v/total for k, v in weights.items()}
        else:
            weights = {k: 1.0/len(factors) for k in factors.keys()}
        
        combined = pd.DataFrame(factors)
        return combined.mul(weights, axis=1).sum(axis=1)
    
    def regime_weight(self, factors: Dict[str, pd.Series], regime: str) -> pd.Series:
        """市场状态加权"""
        regime_weights = {
            'BULL': {'momentum': 0.4, 'value': 0.3, 'quality': 0.3},
            'BEAR': {'momentum': 0.2, 'value': 0.5, 'quality': 0.3},
            'RANGING': {'momentum': 0.3, 'value': 0.3, 'quality': 0.4},
        }
        
        weights = regime_weights.get(regime, {})
        if not weights:
            return self.equal_weight(factors)
        
        # 按类别分配权重
        combined = pd.DataFrame(factors)
        weighted_sum = pd.Series(0.0, index=combined.index)
        
        for factor_name, factor_data in factors.items():
            # 简化：假设因子名包含类别
            category = self._infer_category(factor_name)
            weight = weights.get(category, 1.0/len(factors))
            weighted_sum += factor_data * weight
        
        return weighted_sum
    
    def _infer_category(self, factor_name: str) -> str:
        """推断因子类别"""
        if 'momentum' in factor_name.lower() or 'roc' in factor_name.lower():
            return 'momentum'
        elif 'value' in factor_name.lower() or 'pe' in factor_name.lower():
            return 'value'
        elif 'quality' in factor_name.lower() or 'roe' in factor_name.lower():
            return 'quality'
        return 'other'
```

- [ ] **Step 5: Create tests for alpha module**

```python
# tests/unit/test_alpha.py
import pytest
import pandas as pd
import numpy as np
from core.alpha import FactorLibrary, FactorEvaluator, FactorCombiner

def test_factor_library_register_and_compute():
    """测试因子注册和计算"""
    library = FactorLibrary()
    
    def momentum_factor(df):
        return df['close'].pct_change(20)
    
    library.register(momentum_factor, 'momentum_20d', 'momentum', '20日动量因子')
    
    # 创建测试数据
    np.random.seed(42)
    df = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    results = library.compute_all(df)
    assert 'momentum_20d' in results
    assert len(results['momentum_20d']) == 100

def test_factor_evaluator_ic():
    """测试因子IC计算"""
    evaluator = FactorEvaluator()
    
    np.random.seed(42)
    factor = pd.Series(np.random.randn(100))
    returns = pd.Series(np.random.randn(100))
    
    ic = evaluator.calculate_ic(factor, returns)
    assert -1 <= ic <= 1

def test_factor_combiner_equal_weight():
    """测试等权重组合"""
    combiner = FactorCombiner()
    
    factors = {
        'factor_a': pd.Series([1, 2, 3, 4, 5]),
        'factor_b': pd.Series([5, 4, 3, 2, 1])
    }
    
    result = combiner.equal_weight(factors)
    assert len(result) == 5
    assert result.mean() == 3.0
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/unit/test_alpha.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add core/alpha/ tests/unit/test_alpha.py
git commit -m "feat: create alpha module with FactorLibrary, Evaluator, Combiner"
```

---

### Task 6: 创建rl模块目录结构

**Files:**
- Create: `core/rl/__init__.py`
- Create: `core/rl/environments.py`
- Create: `core/rl/agents.py`
- Create: `core/rl/config.py`

- [ ] **Step 1: Create directory and __init__.py**

```bash
mkdir -p core/rl
```

```python
# core/rl/__init__.py
from .environments import TradingEnvironment
from .agents import PPOAgent
from .config import RL_CONFIG

__all__ = ['TradingEnvironment', 'PPOAgent', 'RL_CONFIG']
```

- [ ] **Step 2: Create environments.py**

```python
# core/rl/environments.py
import logging
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

class TradingEnvironment:
    """强化学习交易环境"""
    
    def __init__(self, data: pd.DataFrame, initial_capital: float = 100000,
                 commission: float = 0.001, slippage: float = 0.0005):
        self.data = data
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        # 状态空间维度
        self.state_dim = 20
        # 动作空间: 3个方向 x 10个仓位大小 = 30个动作
        self.action_dim = 30
        
        self.reset()
    
    def reset(self) -> np.ndarray:
        """重置环境"""
        self.current_step = 0
        self.equity = self.initial_capital
        self.position = 0  # -1, 0, 1
        self.entry_price = 0
        self.total_trades = 0
        self.win_trades = 0
        self.max_equity = self.initial_capital
        
        return self._get_observation()
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """执行一步交易"""
        # 解析动作
        direction = action // 10 - 1  # -1, 0, 1
        size_pct = (action % 10 + 1) / 10  # 0.1 ~ 1.0
        
        # 记录当前状态
        old_equity = self.equity
        
        # 执行交易
        if direction != 0 and self.position == 0:
            self._open_position(direction, size_pct)
        elif direction == 0 and self.position != 0:
            self._close_position()
        elif direction * self.position < 0:
            self._close_position()
            self._open_position(direction, size_pct)
        
        # 更新持仓价值
        self._update_equity()
        
        # 计算奖励
        reward = self._calculate_reward(old_equity)
        
        # 检查是否结束
        done = self.current_step >= len(self.data) - 1
        
        # 获取新观察
        obs = self._get_observation()
        
        info = {
            'equity': self.equity,
            'position': self.position,
            'total_trades': self.total_trades,
            'win_rate': self.win_trades / (self.total_trades + 1e-8)
        }
        
        self.current_step += 1
        
        return obs, reward, done, info
    
    def _get_observation(self) -> np.ndarray:
        """获取观察向量"""
        if self.current_step >= len(self.data):
            return np.zeros(self.state_dim, dtype=np.float32)
        
        row = self.data.iloc[self.current_step]
        
        # 计算特征
        features = []
        
        # 价格特征
        if self.current_step > 0:
            features.append(row['close'] / self.data.iloc[self.current_step-1]['close'] - 1)
        else:
            features.append(0.0)
        
        # 成交量特征
        avg_volume = self.data['volume'].rolling(20).mean().iloc[self.current_step] if self.current_step >= 20 else row['volume']
        features.append(row['volume'] / (avg_volume + 1e-8) - 1)
        
        # 价格偏离
        avg_close = self.data['close'].rolling(20).mean().iloc[self.current_step] if self.current_step >= 20 else row['close']
        features.append(row['close'] / avg_close - 1)
        
        # 填充到state_dim
        while len(features) < self.state_dim - 3:
            features.append(0.0)
        
        # 添加持仓状态
        features.append(self.position)
        features.append(self.equity / self.initial_capital - 1)
        features.append((self.current_step - self.entry_price) / (self.entry_price + 1e-8) if self.position != 0 else 0)
        
        return np.array(features[:self.state_dim], dtype=np.float32)
    
    def _open_position(self, direction: int, size_pct: float):
        """开仓"""
        price = self.data.iloc[self.current_step]['close']
        cost = self.commission + self.slippage
        
        self.position = direction
        self.entry_price = price * (1 + cost * direction)
        self.total_trades += 1
    
    def _close_position(self):
        """平仓"""
        if self.position == 0:
            return
        
        price = self.data.iloc[self.current_step]['close']
        cost = self.commission + self.slippage
        
        exit_price = price * (1 - cost * self.position)
        pnl = (exit_price - self.entry_price) * self.position
        
        self.equity += pnl
        if pnl > 0:
            self.win_trades += 1
        
        self.position = 0
        self.entry_price = 0
    
    def _update_equity(self):
        """更新持仓价值"""
        if self.position != 0:
            price = self.data.iloc[self.current_step]['close']
            unrealized = (price - self.entry_price) * self.position
            # 简化：不计算未实现盈亏到equity
            pass
        
        self.max_equity = max(self.max_equity, self.equity)
    
    def _calculate_reward(self, old_equity: float) -> float:
        """计算奖励"""
        pnl = (self.equity - old_equity) / (old_equity + 1e-8)
        
        # 交易成本惩罚
        cost_penalty = abs(pnl) * 0.1 if pnl != 0 else 0
        
        # 风险惩罚（回撤）
        drawdown = max(0, 1 - self.equity / self.max_equity)
        risk_penalty = drawdown * 0.5
        
        return pnl - cost_penalty - risk_penalty
```

- [ ] **Step 3: Create agents.py**

```python
# core/rl/agents.py
import logging
import numpy as np
from typing import Tuple, List

logger = logging.getLogger(__name__)

class PPOAgent:
    """PPO强化学习Agent (简化版，不依赖torch)"""
    
    def __init__(self, state_dim: int, action_dim: int, lr: float = 0.001,
                 gamma: float = 0.99, epsilon: float = 0.2):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon
        
        # 简化的策略网络（使用线性模型）
        self.policy_weights = np.random.randn(state_dim, action_dim) * 0.01
        self.value_weights = np.random.randn(state_dim, 1) * 0.01
        
        # 经验缓存
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
    
    def select_action(self, state: np.ndarray) -> Tuple[int, float, float]:
        """选择动作"""
        # 计算动作概率
        logits = state @ self.policy_weights
        probs = self._softmax(logits)
        
        # 采样动作
        action = np.random.choice(self.action_dim, p=probs)
        
        # 计算log概率
        log_prob = np.log(probs[action] + 1e-8)
        
        # 计算价值
        value = (state @ self.value_weights).item()
        
        return action, log_prob, value
    
    def store_experience(self, state, action, reward, value, log_prob):
        """存储经验"""
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.values.append(value)
        self.log_probs.append(log_prob)
    
    def update(self) -> float:
        """更新策略"""
        if len(self.states) < 10:
            return 0.0
        
        # 计算折扣回报
        returns = self._compute_returns()
        returns = np.array(returns)
        
        # 计算优势函数
        values = np.array(self.values)
        advantages = returns - values
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # 简化更新：使用梯度上升
        states = np.array(self.states)
        actions = np.array(self.actions)
        old_log_probs = np.array(self.log_probs)
        
        # 计算当前策略的概率
        logits = states @ self.policy_weights
        probs = self._softmax(logits)
        
        # 计算新旧概率比
        new_log_probs = np.log(probs[np.arange(len(actions)), actions] + 1e-8)
        ratio = np.exp(new_log_probs - old_log_probs)
        
        # PPO clipping
        clipped_ratio = np.clip(ratio, 1 - self.epsilon, 1 + self.epsilon)
        
        # 计算损失
        actor_loss = -np.mean(np.minimum(ratio * advantages, clipped_ratio * advantages))
        
        # 梯度上升更新
        grad = np.zeros_like(self.policy_weights)
        for i in range(len(states)):
            for a in range(self.action_dim):
                if a == actions[i]:
                    grad[:, a] += (probs[i, a] - 1) * advantages[i]
                else:
                    grad[:, a] += probs[i, a] * advantages[i]
        
        self.policy_weights += 0.001 * grad
        
        # 更新价值网络
        value_pred = states @ self.value_weights
        value_grad = -2 * (returns.reshape(-1, 1) - value_pred) * states
        self.value_weights += 0.001 * value_grad.mean(axis=0).reshape(-1, 1)
        
        # 清空缓存
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        
        return actor_loss
    
    def _compute_returns(self) -> List[float]:
        """计算折扣回报"""
        returns = []
        R = 0
        for r in reversed(self.rewards):
            R = r + self.gamma * R
            returns.insert(0, R)
        return returns
    
    def _softmax(self, x):
        """softmax函数"""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()
    
    def save(self, path: str):
        """保存模型"""
        np.savez(path, 
                 policy_weights=self.policy_weights,
                 value_weights=self.value_weights)
    
    def load(self, path: str):
        """加载模型"""
        data = np.load(path)
        self.policy_weights = data['policy_weights']
        self.value_weights = data['value_weights']
```

- [ ] **Step 4: Create config.py**

```python
# core/rl/config.py
"""RL模块配置"""

RL_CONFIG = {
    'ppo': {
        'learning_rate': 0.001,
        'gamma': 0.99,
        'epsilon': 0.2,
        'batch_size': 64,
        'hidden_dim': 256,
        'n_episodes': 1000,
        'max_steps': 1000,
        'update_interval': 10,
    },
    'environment': {
        'initial_capital': 100000,
        'commission': 0.001,
        'slippage': 0.0005,
        'max_position_pct': 0.3,
    },
    'training': {
        'save_interval': 100,
        'log_interval': 10,
        'eval_interval': 50,
    }
}
```

- [ ] **Step 5: Create tests for rl module**

```python
# tests/unit/test_rl.py
import pytest
import numpy as np
import pandas as pd
from core.rl import TradingEnvironment, PPOAgent, RL_CONFIG

def test_trading_environment_initialization():
    """测试交易环境初始化"""
    np.random.seed(42)
    data = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 101,
        'low': np.random.randn(100).cumsum() + 99,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    env = TradingEnvironment(data)
    assert env.state_dim == 20
    assert env.action_dim == 30
    assert env.equity == 100000

def test_trading_environment_step():
    """测试环境step函数"""
    np.random.seed(42)
    data = pd.DataFrame({
        'open': np.random.randn(10).cumsum() + 100,
        'high': np.random.randn(10).cumsum() + 101,
        'low': np.random.randn(10).cumsum() + 99,
        'close': np.random.randn(10).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 10)
    })
    
    env = TradingEnvironment(data)
    obs = env.reset()
    
    assert len(obs) == 20
    
    # 执行一步
    obs, reward, done, info = env.step(15)  # BUY with 60% size
    
    assert len(obs) == 20
    assert isinstance(reward, float)
    assert isinstance(done, bool)

def test_ppo_agent_initialization():
    """测试PPO Agent初始化"""
    agent = PPOAgent(state_dim=20, action_dim=30)
    assert agent.state_dim == 20
    assert agent.action_dim == 30

def test_ppo_agent_select_action():
    """测试Agent选择动作"""
    agent = PPOAgent(state_dim=20, action_dim=30)
    state = np.random.randn(20)
    
    action, log_prob, value = agent.select_action(state)
    
    assert 0 <= action < 30
    assert isinstance(log_prob, float)
    assert isinstance(value, float)

def test_rl_config():
    """测试RL配置"""
    assert 'ppo' in RL_CONFIG
    assert 'environment' in RL_CONFIG
    assert RL_CONFIG['ppo']['gamma'] == 0.99
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/unit/test_rl.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add core/rl/ tests/unit/test_rl.py
git commit -m "feat: create rl module with TradingEnvironment and PPOAgent"
```

---

## Phase 2: 市场状态与参数优化 (Week 3-4)

### Task 7: 实现HMM市场状态检测器

**Files:**
- Create: `core/market_state/regime_detector_v2.py`
- Test: `tests/unit/test_market_state.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_market_state.py
import pytest
import numpy as np
import pandas as pd
from core.market_state.regime_detector_v2 import HMMDetector

def test_hmm_detector_initialization():
    """测试HMM检测器初始化"""
    detector = HMMDetector(n_regimes=4)
    assert detector.n_regimes == 4
    assert len(detector.regime_labels) == 4

def test_hmm_detector_fit_and_predict():
    """测试HMM训练和预测"""
    np.random.seed(42)
    returns = pd.Series(np.random.randn(200) * 0.02)
    
    detector = HMMDetector(n_regimes=4)
    detector.fit(returns)
    
    predictions = detector.predict(returns)
    
    assert len(predictions) == 200
    assert all(p in ['QUIET', 'TRENDING', 'VOLATILE', 'CRISIS'] for p in predictions)

def test_hmm_detector_predict_proba():
    """测试概率预测"""
    np.random.seed(42)
    returns = pd.Series(np.random.randn(100) * 0.02)
    
    detector = HMMDetector(n_regimes=4)
    detector.fit(returns)
    
    probs = detector.predict_proba(returns)
    
    assert probs.shape == (100, 4)
    assert all(abs(probs.sum(axis=1) - 1) < 0.01)

def test_hmm_detector_change_point():
    """测试变点检测"""
    np.random.seed(42)
    # 创建有明显状态变化的数据
    returns1 = np.random.randn(50) * 0.01  # 低波动
    returns2 = np.random.randn(50) * 0.05  # 高波动
    returns = pd.Series(np.concatenate([returns1, returns2]))
    
    detector = HMMDetector(n_regimes=4)
    detector.fit(returns)
    
    change_points = detector.detect_change_point(returns, threshold=0.2)
    
    assert isinstance(change_points, list)
    # 应该在50附近检测到变化
    assert any(40 <= cp <= 60 for cp in change_points)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_market_state.py::test_hmm_detector_initialization -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write implementation**

```python
# core/market_state/regime_detector_v2.py
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from hmmlearn import GaussianHMM

logger = logging.getLogger(__name__)

class HMMDetector:
    """基于隐马尔可夫模型的市场状态检测"""
    
    def __init__(self, n_regimes: int = 4, covariance_type: str = 'full', n_iter: int = 100):
        self.n_regimes = n_regimes
        self.covariance_type = covariance_type
        self.n_iter = n_iter
        
        self.model = GaussianHMM(
            n_components=n_regimes,
            covariance_type=covariance_type,
            n_iter=n_iter,
            random_state=42
        )
        
        self.regime_labels = {
            0: 'QUIET',      # 平静期
            1: 'TRENDING',   # 趋势期
            2: 'VOLATILE',   # 高波动
            3: 'CRISIS'      # 危机期
        }
        
        self.is_fitted = False
    
    def fit(self, returns: pd.Series):
        """训练HMM模型"""
        X = returns.values.reshape(-1, 1)
        self.model.fit(X)
        self.is_fitted = True
        logger.info(f"HMM model fitted with {self.n_regimes} regimes")
    
    def predict(self, returns: pd.Series) -> List[str]:
        """预测市场状态"""
        if not self.is_fitted:
            raise ValueError("Model not fitted yet. Call fit() first.")
        
        X = returns.values.reshape(-1, 1)
        states = self.model.predict(X)
        return [self.regime_labels[s] for s in states]
    
    def predict_proba(self, returns: pd.Series) -> pd.DataFrame:
        """预测各状态概率"""
        if not self.is_fitted:
            raise ValueError("Model not fitted yet. Call fit() first.")
        
        X = returns.values.reshape(-1, 1)
        probs = self.model.predict_proba(X)
        return pd.DataFrame(probs, columns=list(self.regime_labels.values()))
    
    def detect_change_point(self, returns: pd.Series, threshold: float = 0.3) -> List[int]:
        """检测状态切换点"""
        probs = self.predict_proba(returns)
        
        change_points = []
        for i in range(1, len(probs)):
            max_prob_change = (probs.iloc[i] - probs.iloc[i-1]).abs().max()
            if max_prob_change > threshold:
                change_points.append(i)
        
        return change_points
    
    def get_current_regime(self, returns: pd.Series) -> Tuple[str, float]:
        """获取当前市场状态和置信度"""
        probs = self.predict_proba(returns)
        last_probs = probs.iloc[-1]
        
        max_idx = last_probs.idxmax()
        confidence = last_probs[max_idx]
        
        return max_idx, confidence
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_market_state.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/market_state/regime_detector_v2.py tests/unit/test_market_state.py
git commit -m "feat: implement HMM-based market regime detector"
```

---

### Task 8: 实现增强状态机

**Files:**
- Create: `core/market_state/state_machine_v2.py`
- Test: `tests/unit/test_state_machine.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_state_machine.py
import pytest
from core.market_state.state_machine_v2 import EnhancedStateMachine

def test_state_machine_initialization():
    """测试状态机初始化"""
    sm = EnhancedStateMachine(min_duration=5)
    assert sm.current_state == 'QUIET'
    assert sm.current_duration == 0

def test_state_machine_same_state():
    """测试同一状态持续"""
    sm = EnhancedStateMachine(min_duration=5)
    
    # 连续5次相同状态
    for i in range(5):
        state, conf = sm.next_state('TRENDING', 0.8)
    
    assert state == 'TRENDING'
    assert sm.current_duration == 5

def test_state_machine_switch_with_penalty():
    """测试状态切换带惩罚"""
    sm = EnhancedStateMachine(min_duration=5, penalty_factor=0.8)
    
    # 先进入TRENDING状态
    for i in range(3):  # 只持续3次，不足min_duration
        state, conf = sm.next_state('TRENDING', 0.8)
    
    # 尝试切换到VOLATILE，应该被惩罚
    state, conf = sm.next_state('VOLATILE', 0.8)
    
    # 应该保持原状态，置信度降低
    assert state == 'TRENDING'
    assert conf < 0.8

def test_state_machine_switch_after_min_duration():
    """测试持续时间足够后切换"""
    sm = EnhancedStateMachine(min_duration=5, penalty_factor=0.8)
    
    # 先进入TRENDING状态5次
    for i in range(5):
        state, conf = sm.next_state('TRENDING', 0.8)
    
    # 持续时间足够，应该允许切换
    state, conf = sm.next_state('VOLATILE', 0.9)
    
    assert state == 'VOLATILE'
    assert sm.current_duration == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_state_machine.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write implementation**

```python
# core/market_state/state_machine_v2.py
import logging
from typing import Tuple, Dict

logger = logging.getLogger(__name__)

class EnhancedStateMachine:
    """增强状态机，带持续时间约束"""
    
    def __init__(self, transition_matrix: Dict = None, min_duration: int = 5, 
                 penalty_factor: float = 0.8):
        self.min_duration = min_duration
        self.penalty_factor = penalty_factor
        
        # 默认转移矩阵
        self.transition_matrix = transition_matrix or {
            'QUIET': {'QUIET': 0.7, 'TRENDING': 0.2, 'VOLATILE': 0.08, 'CRISIS': 0.02},
            'TRENDING': {'QUIET': 0.15, 'TRENDING': 0.65, 'VOLATILE': 0.15, 'CRISIS': 0.05},
            'VOLATILE': {'QUIET': 0.1, 'TRENDING': 0.2, 'VOLATILE': 0.5, 'CRISIS': 0.2},
            'CRISIS': {'QUIET': 0.05, 'TRENDING': 0.1, 'VOLATILE': 0.3, 'CRISIS': 0.55},
        }
        
        self.current_state = 'QUIET'
        self.current_duration = 0
    
    def next_state(self, observation: str, confidence: float) -> Tuple[str, float]:
        """下一个状态，带持续时间惩罚"""
        if observation == self.current_state:
            # 同一状态，增加持续时间
            self.current_duration += 1
            return self.current_state, confidence
        else:
            # 尝试切换
            if self.current_duration < self.min_duration:
                # 持续时间不足，降低切换置信度
                adjusted_confidence = confidence * (self.penalty_factor ** (self.min_duration - self.current_duration))
                logger.debug(f"State switch penalized: {self.current_state} -> {observation}, "
                           f"confidence {confidence:.2f} -> {adjusted_confidence:.2f}")
                return self.current_state, adjusted_confidence
            else:
                # 允许切换，检查转移概率
                transition_prob = self.transition_matrix.get(self.current_state, {}).get(observation, 0)
                
                if confidence * transition_prob > 0.3:  # 切换阈值
                    old_state = self.current_state
                    self.current_state = observation
                    self.current_duration = 0
                    logger.info(f"State switched: {old_state} -> {observation}")
                    return observation, confidence
                else:
                    # 转移概率太低，保持原状态
                    return self.current_state, confidence * 0.5
    
    def get_transition_probability(self, from_state: str, to_state: str) -> float:
        """获取转移概率"""
        return self.transition_matrix.get(from_state, {}).get(to_state, 0.0)
    
    def reset(self):
        """重置状态机"""
        self.current_state = 'QUIET'
        self.current_duration = 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_state_machine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/market_state/state_machine_v2.py tests/unit/test_state_machine.py
git commit -m "feat: implement enhanced state machine with duration constraint"
```

---

### Task 9: 实现参数存储数据库集成

**Files:**
- Modify: `core/adaptive/parameter_store.py`
- Create: `db/models.py` (添加ParameterVersion表)
- Test: `tests/integration/test_parameter_store_db.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_parameter_store_db.py
import pytest
from datetime import datetime
from core.db.session import get_session
from core.adaptive.parameter_store import ParameterStore

def test_parameter_store_persistence():
    """测试参数持久化到数据库"""
    session = get_session()
    store = ParameterStore(session)
    
    params = {'atr_period': 14, 'stop_loss': 2.0}
    metrics = {'sharpe': 1.5, 'win_rate': 0.6}
    
    # 保存
    store.save('test_strategy', params, metrics)
    
    # 重新加载
    loaded = store.load_latest('test_strategy')
    
    assert loaded is not None
    assert loaded['params'] == params
    
    # 清理
    session.rollback()

def test_parameter_store_version_rollback():
    """测试版本回滚"""
    session = get_session()
    store = ParameterStore(session)
    
    params_v1 = {'atr_period': 14}
    params_v2 = {'atr_period': 20}
    
    store.save('test_strategy', params_v1, {}, version=1)
    store.save('test_strategy', params_v2, {}, version=2)
    
    # 回滚到v1
    store.rollback('test_strategy', 1)
    
    loaded = store.load_latest('test_strategy')
    assert loaded['params'] == params_v1
    
    # 清理
    session.rollback()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_parameter_store_db.py -v`
Expected: FAIL with database error

- [ ] **Step 3: Add database model**

```python
# db/models.py 添加
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from datetime import datetime

class ParameterVersion(Base):
    """参数版本表"""
    __tablename__ = "parameter_versions"
    
    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(100), index=True, nullable=False)
    version = Column(Integer, nullable=False)
    params = Column(Text, nullable=False)  # JSON
    metrics = Column(Text)  # JSON
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        {'extend_existing': True}
    )
```

- [ ] **Step 4: Update parameter_store.py**

```python
# core/adaptive/parameter_store.py 修改
import json
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ParameterStore:
    """参数存储，支持版本管理和数据库持久化"""
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.cache = {}  # 内存缓存
    
    def save(self, strategy_name: str, params: Dict, metrics: Dict, version: int = None):
        """保存参数版本"""
        if version is None:
            version = self._get_next_version(strategy_name)
        
        # 内存缓存
        record = {
            'strategy_name': strategy_name,
            'version': version,
            'params': params,
            'metrics': metrics,
            'created_at': datetime.now().isoformat(),
            'is_active': True
        }
        self.cache[f"{strategy_name}:{version}"] = record
        
        # 数据库持久化
        if self.db:
            try:
                from db.models import ParameterVersion
                db_record = ParameterVersion(
                    strategy_name=strategy_name,
                    version=version,
                    params=json.dumps(params),
                    metrics=json.dumps(metrics),
                    created_at=datetime.now(),
                    is_active=True
                )
                self.db.add(db_record)
                self.db.commit()
                logger.info(f"Saved params for {strategy_name} v{version} to database")
            except Exception as e:
                logger.error(f"Failed to save to database: {e}")
                self.db.rollback()
    
    def load_latest(self, strategy_name: str) -> Optional[Dict]:
        """加载最新参数"""
        # 先检查内存缓存
        versions = []
        for key, record in self.cache.items():
            if key.startswith(f"{strategy_name}:"):
                versions.append(record)
        
        if versions:
            latest = max(versions, key=lambda x: x['version'])
            return latest
        
        # 从数据库加载
        if self.db:
            try:
                from db.models import ParameterVersion
                record = self.db.query(ParameterVersion)\
                    .filter_by(strategy_name=strategy_name, is_active=True)\
                    .order_by(ParameterVersion.version.desc())\
                    .first()
                
                if record:
                    return {
                        'strategy_name': record.strategy_name,
                        'version': record.version,
                        'params': json.loads(record.params),
                        'metrics': json.loads(record.metrics) if record.metrics else {},
                        'created_at': record.created_at.isoformat()
                    }
            except Exception as e:
                logger.error(f"Failed to load from database: {e}")
        
        return None
    
    def rollback(self, strategy_name: str, version: int):
        """回滚到指定版本"""
        if self.db:
            try:
                from db.models import ParameterVersion
                
                # 标记所有版本为非活跃
                self.db.query(ParameterVersion)\
                    .filter_by(strategy_name=strategy_name)\
                    .update({'is_active': False})
                
                # 激活指定版本
                self.db.query(ParameterVersion)\
                    .filter_by(strategy_name=strategy_name, version=version)\
                    .update({'is_active': True})
                
                self.db.commit()
                logger.info(f"Rolled back {strategy_name} to version {version}")
            except Exception as e:
                logger.error(f"Failed to rollback: {e}")
                self.db.rollback()
    
    def _get_next_version(self, strategy_name: str) -> int:
        """获取下一个版本号"""
        # 从缓存获取
        versions = []
        for key in self.cache.keys():
            if key.startswith(f"{strategy_name}:"):
                v = int(key.split(':')[1])
                versions.append(v)
        
        # 从数据库获取
        if self.db:
            try:
                from db.models import ParameterVersion
                db_versions = self.db.query(ParameterVersion.version)\
                    .filter_by(strategy_name=strategy_name)\
                    .all()
                versions.extend([v[0] for v in db_versions])
            except:
                pass
        
        if versions:
            return max(versions) + 1
        return 1
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/integration/test_parameter_store_db.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add core/adaptive/parameter_store.py db/models.py tests/integration/test_parameter_store_db.py
git commit -m "feat: add database persistence to ParameterStore"
```

---

### Task 10: 实现Walk-forward验证器

**Files:**
- Modify: `core/adaptive/walk_forward_validator.py`
- Test: `tests/unit/test_walk_forward.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_walk_forward.py
import pytest
import numpy as np
import pandas as pd
from core.adaptive.walk_forward_validator import WalkForwardValidator

def test_walk_forward_validator_initialization():
    """测试Walk-forward验证器初始化"""
    validator = WalkForwardValidator(n_splits=5, train_ratio=0.7)
    assert validator.n_splits == 5
    assert validator.train_ratio == 0.7

def test_walk_forward_create_splits():
    """测试数据分割"""
    validator = WalkForwardValidator(n_splits=3, train_ratio=0.7)
    
    data = pd.DataFrame({
        'close': np.random.randn(300).cumsum() + 100
    })
    
    splits = validator._create_splits(data)
    
    assert len(splits) == 3
    for train, test in splits:
        assert len(train) > 0
        assert len(test) > 0

def test_walk_forward_detect_overfitting():
    """测试过拟合检测"""
    validator = WalkForwardValidator()
    
    # IS性能远好于OOS = 过拟合
    is_metrics = {'sharpe': 3.0}
    oos_metrics = {'sharpe_oos': 1.0}
    
    assert validator.detect_overfitting(is_metrics, oos_metrics) == True
    
    # IS和OOS相近 = 没有过拟合
    is_metrics2 = {'sharpe': 1.5}
    oos_metrics2 = {'sharpe_oos': 1.2}
    
    assert validator.detect_overfitting(is_metrics2, oos_metrics2) == False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_walk_forward.py -v`
Expected: FAIL with AttributeError

- [ ] **Step 3: Write implementation**

```python
# core/adaptive/walk_forward_validator.py
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Callable

logger = logging.getLogger(__name__)

class WalkForwardValidator:
    """Walk-forward验证，防止过拟合"""
    
    def __init__(self, n_splits: int = 5, train_ratio: float = 0.7):
        self.n_splits = n_splits
        self.train_ratio = train_ratio
    
    def validate(self, strategy_fn: Callable, params: Dict, data: pd.DataFrame) -> Dict[str, Any]:
        """执行walk-forward验证
        
        Args:
            strategy_fn: 策略函数，接收(data, params)返回returns
            params: 策略参数
            data: 历史数据
        
        Returns:
            验证指标
        """
        splits = self._create_splits(data)
        oos_returns = []
        
        for i, (train_data, test_data) in enumerate(splits):
            logger.info(f"Walk-forward split {i+1}/{self.n_splits}")
            
            # 在训练集上优化参数（简化：使用给定参数）
            train_params = params
            
            # 在测试集上验证
            try:
                oos_return = strategy_fn(test_data, train_params)
                oos_returns.append(oos_return)
            except Exception as e:
                logger.warning(f"Split {i+1} failed: {e}")
                continue
        
        if not oos_returns:
            return {'error': 'All splits failed'}
        
        # 计算统计指标
        oos_returns = np.array(oos_returns)
        metrics = {
            'mean_oos_return': float(np.mean(oos_returns)),
            'std_oos_return': float(np.std(oos_returns)),
            'sharpe_oos': float(np.mean(oos_returns) / (np.std(oos_returns) + 1e-8)),
            'min_oos_return': float(np.min(oos_returns)),
            'max_oos_return': float(np.max(oos_returns)),
            'n_splits': len(oos_returns),
            'is_stable': float(np.std(oos_returns)) < 0.1,
        }
        
        return metrics
    
    def _create_splits(self, data: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """创建训练/测试分割"""
        n = len(data)
        split_size = n // self.n_splits
        
        splits = []
        for i in range(self.n_splits):
            start = i * split_size
            end = min((i + 1) * split_size, n)
            
            # 训练集：前train_ratio%
            train_end = start + int((end - start) * self.train_ratio)
            
            train_data = data.iloc[start:train_end]
            test_data = data.iloc[train_end:end]
            
            if len(train_data) > 0 and len(test_data) > 0:
                splits.append((train_data, test_data))
        
        return splits
    
    def detect_overfitting(self, is_metrics: Dict, oos_metrics: Dict) -> bool:
        """检测过拟合"""
        is_sharpe = is_metrics.get('sharpe', 0)
        oos_sharpe = oos_metrics.get('sharpe_oos', 0)
        
        # IS性能远好于OOS = 过拟合
        return is_sharpe > oos_sharpe * 1.5
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_walk_forward.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/adaptive/walk_forward_validator.py tests/unit/test_walk_forward.py
git commit -m "feat: implement Walk-forward validator for overfitting detection"
```

---

## Phase 3: Alpha因子与策略增强 (Week 5-6)

### Task 11: 实现Alpha101因子库框架

**Files:**
- Create: `core/alpha/alpha101/__init__.py`
- Create: `core/alpha/alpha101/base.py`
- Create: `core/alpha/alpha101/alpha001.py`
- Create: `core/alpha/alpha101/alpha002.py`
- Create: `core/alpha/alpha101/alpha003.py`
- Test: `tests/unit/test_alpha101.py`

- [ ] **Step 1: Create base class**

```python
# core/alpha/alpha101/base.py
import pandas as pd
from abc import ABC, abstractmethod

class AlphaBase(ABC):
    """Alpha因子基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """因子名称"""
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """因子类别"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """因子描述"""
        pass
    
    @abstractmethod
    def compute(self, df: pd.DataFrame) -> pd.Series:
        """计算因子值"""
        pass
    
    def __call__(self, df: pd.DataFrame) -> pd.Series:
        return self.compute(df)
```

- [ ] **Step 2: Create Alpha001**

```python
# core/alpha/alpha101/alpha001.py
import pandas as pd
import numpy as np
from .base import AlphaBase

class Alpha001(AlphaBase):
    """Alpha001: rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5
    
    描述: 价格动量因子，捕捉趋势反转
    类别: 价格动量
    """
    
    @property
    def name(self) -> str:
        return "alpha001"
    
    @property
    def category(self) -> str:
        return "price_momentum"
    
    @property
    def description(self) -> str:
        return "价格动量因子，捕捉趋势反转"
    
    def compute(self, df: pd.DataFrame) -> pd.Series:
        returns = df['close'].pct_change()
        cond = returns < 0
        
        # 计算内层值
        inner = pd.Series(
            np.where(cond, returns.rolling(20).std(), df['close']),
            index=df.index
        )
        
        # SignedPower
        powered = np.sign(inner) * np.abs(inner) ** 2
        
        # Ts_ArgMax
        argmax = powered.rolling(5).apply(lambda x: np.argmax(x), raw=True)
        
        # 归一化到[-0.5, 0.5]
        return argmax / 4 - 0.5
```

- [ ] **Step 3: Create Alpha002**

```python
# core/alpha/alpha101/alpha002.py
import pandas as pd
import numpy as np
from .base import AlphaBase

class Alpha002(AlphaBase):
    """Alpha002: -1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6)
    
    描述: 量价相关性因子
    类别: 量价关系
    """
    
    @property
    def name(self) -> str:
        return "alpha002"
    
    @property
    def category(self) -> str:
        return "volume_price"
    
    @property
    def description(self) -> str:
        return "量价相关性因子"
    
    def compute(self, df: pd.DataFrame) -> pd.Series:
        # delta(log(volume), 2)
        vol_delta = np.log(df['volume']).diff(2)
        
        # (close - open) / open
        price_range = (df['close'] - df['open']) / df['open']
        
        # rank并计算相关性
        return -1 * vol_delta.rank().rolling(6).corr(price_range.rank())
```

- [ ] **Step 4: Create Alpha003**

```python
# core/alpha/alpha101/alpha003.py
import pandas as pd
import numpy as np
from .base import AlphaBase

class Alpha003(AlphaBase):
    """Alpha003: -1 * correlation(rank(open), rank(volume), 10)
    
    描述: 开盘价与成交量相关性
    类别: 量价关系
    """
    
    @property
    def name(self) -> str:
        return "alpha003"
    
    @property
    def category(self) -> str:
        return "volume_price"
    
    @property
    def description(self) -> str:
        return "开盘价与成交量相关性"
    
    def compute(self, df: pd.DataFrame) -> pd.Series:
        return -1 * df['open'].rank().rolling(10).corr(df['volume'].rank())
```

- [ ] **Step 5: Create __init__.py**

```python
# core/alpha/alpha101/__init__.py
from .alpha001 import Alpha001
from .alpha002 import Alpha002
from .alpha003 import Alpha003

ALPHA101_FACTORS = [
    Alpha001(),
    Alpha002(),
    Alpha003(),
]

def get_all_alpha101():
    """获取所有Alpha101因子"""
    return ALPHA101_FACTORS
```

- [ ] **Step 6: Create tests**

```python
# tests/unit/test_alpha101.py
import pytest
import numpy as np
import pandas as pd
from core.alpha.alpha101 import Alpha001, Alpha002, Alpha003, get_all_alpha101

@pytest.fixture
def sample_data():
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'open': np.random.randn(n).cumsum() + 100,
        'high': np.random.randn(n).cumsum() + 101,
        'low': np.random.randn(n).cumsum() + 99,
        'close': np.random.randn(n).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, n)
    })

def test_alpha001(sample_data):
    """测试Alpha001"""
    alpha = Alpha001()
    result = alpha.compute(sample_data)
    
    assert len(result) == len(sample_data)
    assert not result.isna().all()

def test_alpha002(sample_data):
    """测试Alpha002"""
    alpha = Alpha002()
    result = alpha.compute(sample_data)
    
    assert len(result) == len(sample_data)

def test_alpha003(sample_data):
    """测试Alpha003"""
    alpha = Alpha003()
    result = alpha.compute(sample_data)
    
    assert len(result) == len(sample_data)

def test_get_all_alpha101():
    """测试获取所有因子"""
    factors = get_all_alpha101()
    assert len(factors) == 3
    assert all(hasattr(f, 'compute') for f in factors)
```

- [ ] **Step 7: Run tests**

Run: `pytest tests/unit/test_alpha101.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add core/alpha/alpha101/ tests/unit/test_alpha101.py
git commit -m "feat: create Alpha101 factor framework with first 3 factors"
```

---

### Task 12: 补充缺失的技术指标

**Files:**
- Modify: `signals/indicators.py`
- Test: `tests/unit/test_indicators.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_indicators.py
import pytest
import numpy as np
import pandas as pd
from signals.indicators import (
    supertrend, williams_r, mfi, trix, aroon_oscillator
)

@pytest.fixture
def sample_ohlcv():
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'open': np.random.randn(n).cumsum() + 100,
        'high': np.random.randn(n).cumsum() + 102,
        'low': np.random.randn(n).cumsum() + 98,
        'close': np.random.randn(n).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, n)
    })

def test_supertrend(sample_ohlcv):
    """测试SuperTrend指标"""
    result = supertrend(sample_ohlcv, period=10, multiplier=3.0)
    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_ohlcv)

def test_williams_r(sample_ohlcv):
    """测试Williams %R指标"""
    result = williams_r(sample_ohlcv, period=14)
    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_ohlcv)
    # Williams %R应该在-100到0之间
    valid = result.dropna()
    assert (valid >= -100).all() and (valid <= 0).all()

def test_mfi(sample_ohlcv):
    """测试MFI指标"""
    result = mfi(sample_ohlcv, period=14)
    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_ohlcv)

def test_trix(sample_ohlcv):
    """测试TRIX指标"""
    result = trix(sample_ohlcv, period=15)
    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_ohlcv)

def test_aroon_oscillator(sample_ohlcv):
    """测试Aroon振荡器"""
    up, down, osc = aroon_oscillator(sample_ohlcv, period=25)
    assert isinstance(up, pd.Series)
    assert isinstance(down, pd.Series)
    assert isinstance(osc, pd.Series)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_indicators.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write implementations**

```python
# signals/indicators.py 添加以下函数

def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
    """SuperTrend指标"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    # ATR
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    
    # 上下轨
    hl2 = (high + low) / 2
    upper = hl2 + multiplier * atr
    lower = hl2 - multiplier * atr
    
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)
    
    supertrend.iloc[0] = upper.iloc[0]
    direction.iloc[0] = 1
    
    for i in range(1, len(df)):
        if close.iloc[i] > upper.iloc[i-1]:
            direction.iloc[i] = 1
        elif close.iloc[i] < lower.iloc[i-1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1]
        
        if direction.iloc[i] == 1:
            supertrend.iloc[i] = lower.iloc[i]
        else:
            supertrend.iloc[i] = upper.iloc[i]
    
    return supertrend

def williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Williams %R指标"""
    high = df['high'].rolling(period).max()
    low = df['low'].rolling(period).min()
    close = df['close']
    
    wr = -100 * (high - close) / (high - low)
    return wr

def mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """资金流量指标 (MFI)"""
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    money_flow = typical_price * df['volume']
    
    positive_flow = pd.Series(0.0, index=df.index)
    negative_flow = pd.Series(0.0, index=df.index)
    
    for i in range(1, len(df)):
        if typical_price.iloc[i] > typical_price.iloc[i-1]:
            positive_flow.iloc[i] = money_flow.iloc[i]
        elif typical_price.iloc[i] < typical_price.iloc[i-1]:
            negative_flow.iloc[i] = money_flow.iloc[i]
    
    positive_mf = positive_flow.rolling(period).sum()
    negative_mf = negative_flow.rolling(period).sum()
    
    mfi = 100 - (100 / (1 + positive_mf / (negative_mf + 1e-8)))
    return mfi

def trix(df: pd.DataFrame, period: int = 15) -> pd.Series:
    """TRIX指标"""
    close = df['close']
    
    # 三次EMA
    ema1 = close.ewm(span=period, adjust=False).mean()
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    ema3 = ema2.ewm(span=period, adjust=False).mean()
    
    # 计算变化率
    trix = ema3.pct_change() * 100
    return trix

def aroon_oscillator(df: pd.DataFrame, period: int = 25) -> tuple:
    """Aroon振荡器"""
    high = df['high']
    low = df['low']
    
    aroon_up = pd.Series(index=df.index, dtype=float)
    aroon_down = pd.Series(index=df.index, dtype=float)
    
    for i in range(period, len(df)):
        # Aroon Up: 距离最高点的周期数
        high_idx = high.iloc[i-period:i+1].idxmax()
        aroon_up.iloc[i] = ((i - high_idx) / period) * 100
        
        # Aroon Down: 距离最低点的周期数
        low_idx = low.iloc[i-period:i+1].idxmin()
        aroon_down.iloc[i] = ((i - low_idx) / period) * 100
    
    oscillator = aroon_up - aroon_down
    return aroon_up, aroon_down, oscillator
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_indicators.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add signals/indicators.py tests/unit/test_indicators.py
git commit -m "feat: add SuperTrend, Williams %R, MFI, TRIX, Aroon indicators"
```

---

## Phase 4: 强化学习与共振重构 (Week 7-8)

### Task 13: 实现共振引擎V2

**Files:**
- Create: `core/resonance/engine_v2.py`
- Create: `core/resonance/voter.py`
- Create: `core/resonance/matrix.py`
- Create: `core/resonance/scanner.py`
- Test: `tests/unit/test_resonance_v2.py`

- [ ] **Step 1: Create Voter engine**

```python
# core/resonance/voter.py
import logging
from typing import List
from signals.base import Signal

logger = logging.getLogger(__name__)

class VoterEngine:
    """观山加权投票引擎"""
    
    def calculate(self, signals: List[Signal]) -> float:
        """计算投票分数"""
        if not signals:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for signal in signals:
            # 使用confidence作为权重
            weight = signal.confidence
            total_score += signal.score * weight
            total_weight += weight
        
        return total_score / (total_weight + 1e-8) if total_weight > 0 else 0.0
```

- [ ] **Step 2: Create Matrix engine**

```python
# core/resonance/matrix.py
import logging
import pandas as pd
from typing import List
from signals.base import Signal

logger = logging.getLogger(__name__)

class MatrixEngine:
    """楚风相关矩阵引擎"""
    
    def calculate(self, signals: List[Signal]) -> float:
        """计算矩阵分数"""
        if not signals:
            return 0.0
        
        # 简化：计算信号一致性
        scores = [s.score for s in signals]
        
        if len(scores) < 2:
            return scores[0] if scores else 0.0
        
        # 计算分数的标准差作为一致性指标
        mean_score = sum(scores) / len(scores)
        std_score = (sum((s - mean_score) ** 2 for s in scores) / len(scores)) ** 0.5
        
        # 一致性越高，分数越可靠
        consistency = 1 - min(std_score / 5.0, 1.0)
        
        return mean_score * consistency
```

- [ ] **Step 3: Create Scanner engine**

```python
# core/resonance/scanner.py
import logging
from typing import List
from signals.base import Signal

logger = logging.getLogger(__name__)

class ScannerEngine:
    """听海阈值扫描引擎"""
    
    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold
    
    def calculate(self, signals: List[Signal]) -> float:
        """计算扫描分数"""
        if not signals:
            return 0.0
        
        # 过滤超过阈值的信号
        filtered = [s for s in signals if abs(s.score) >= self.threshold]
        
        if not filtered:
            return 0.0
        
        # 计算平均分数
        total = sum(s.score for s in filtered)
        return total / len(filtered)
```

- [ ] **Step 4: Create ResonanceEngineV2**

```python
# core/resonance/engine_v2.py
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from signals.base import Signal
from .voter import VoterEngine
from .matrix import MatrixEngine
from .scanner import ScannerEngine

logger = logging.getLogger(__name__)

@dataclass
class ResonanceOutputV2:
    """共振输出"""
    symbol: str
    score_G: float  # 观山分数
    score_C: float  # 楚风分数
    score_T: float  # 听海分数
    final_score: float
    direction: str  # BUY/SELL/HOLD
    confidence: float
    regime: str
    weight_G: float
    weight_C: float
    weight_T: float

class ResonanceEngineV2:
    """增强共振引擎"""
    
    def __init__(self):
        self.voter = VoterEngine()
        self.matrix = MatrixEngine()
        self.scanner = ScannerEngine()
        
        # 默认权重
        self.weights = {
            'guanshan': 0.33,
            'chufeng': 0.33,
            'tinghai': 0.34
        }
        
        # 市场状态权重调整
        self.regime_adjustments = {
            'BULL': {'guanshan': 0.15, 'chufeng': 0.0, 'tinghai': -0.15},
            'BEAR': {'guanshan': -0.15, 'chufeng': 0.15, 'tinghai': 0.0},
            'RANGING': {'guanshan': -0.1, 'chufeng': -0.1, 'tinghai': 0.2},
            'VOLATILE': {'guanshan': 0.0, 'chufeng': 0.1, 'tinghai': -0.1},
            'CRISIS': {'guanshan': -0.2, 'chufeng': 0.2, 'tinghai': 0.0},
        }
    
    def calculate(self, symbol: str, signals: List[Signal], 
                  regime: str = 'RANGING') -> ResonanceOutputV2:
        """计算共振"""
        # 按source_system分组
        groups = self._group_signals_by_source(signals)
        
        # 计算各系统分数
        score_G = self.voter.calculate(groups['guanshan'])
        score_C = self.matrix.calculate(groups['chufeng'])
        score_T = self.scanner.calculate(groups['tinghai'])
        
        # 获取调整后的权重
        weights = self._get_adjusted_weights(regime)
        
        # 计算最终分数
        final_score = (
            weights['guanshan'] * score_G +
            weights['chufeng'] * score_C +
            weights['tinghai'] * score_T
        )
        
        # 判断方向和置信度
        direction = 'BUY' if final_score > 2.0 else ('SELL' if final_score < -2.0 else 'HOLD')
        confidence = min(abs(final_score) / 10.0, 1.0)
        
        return ResonanceOutputV2(
            symbol=symbol,
            score_G=score_G,
            score_C=score_C,
            score_T=score_T,
            final_score=final_score,
            direction=direction,
            confidence=confidence,
            regime=regime,
            weight_G=weights['guanshan'],
            weight_C=weights['chufeng'],
            weight_T=weights['tinghai']
        )
    
    def _group_signals_by_source(self, signals: List[Signal]) -> Dict[str, List[Signal]]:
        """按source_system分组"""
        groups = {"guanshan": [], "chufeng": [], "tinghai": []}
        
        for signal in signals:
            source = getattr(signal, 'source_system', None)
            if source and source in groups:
                groups[source].append(signal)
            else:
                inferred = self._infer_source(signal.strategy_name)
                groups[inferred].append(signal)
        
        return groups
    
    def _infer_source(self, strategy_name: str) -> str:
        """推断信号来源"""
        if strategy_name.startswith(('TT7_', 'OI_', 'Enhanced_')):
            return "guanshan"
        elif strategy_name.startswith(('trend_', 'reversal_', 'breakout_', 'momentum_')):
            return "chufeng"
        elif strategy_name.startswith(('filter_', 'layer_', 'chan_', 'ml_')):
            return "tinghai"
        return "chufeng"
    
    def _get_adjusted_weights(self, regime: str) -> Dict[str, float]:
        """获取市场状态调整后的权重"""
        weights = self.weights.copy()
        adjustments = self.regime_adjustments.get(regime, {})
        
        for source, adj in adjustments.items():
            weights[source] = max(0.1, min(0.6, weights[source] + adj))
        
        # 归一化
        total = sum(weights.values())
        return {k: v/total for k, v in weights.items()}
```

- [ ] **Step 5: Create tests**

```python
# tests/unit/test_resonance_v2.py
import pytest
from datetime import datetime
from signals.base import Signal
from core.resonance.engine_v2 import ResonanceEngineV2

def test_resonance_engine_v2_initialization():
    """测试V2引擎初始化"""
    engine = ResonanceEngineV2()
    assert engine.weights['guanshan'] == 0.33

def test_resonance_engine_v2_calculate():
    """测试V2引擎计算"""
    engine = ResonanceEngineV2()
    
    signals = [
        Signal("trend_ma_cross", "RB", "BUY", 0.8, 5.0, 3850, datetime.now(), "test", source_system="chufeng"),
        Signal("reversal_rsi", "RB", "SELL", 0.7, -3.0, 3850, datetime.now(), "test", source_system="chufeng"),
    ]
    
    result = engine.calculate("RB", signals, "TRENDING")
    
    assert result.symbol == "RB"
    assert result.direction in ["BUY", "SELL", "HOLD"]
    assert 0 <= result.confidence <= 1

def test_resonance_engine_v2_regime_weights():
    """测试市场状态权重调整"""
    engine = ResonanceEngineV2()
    
    # BULL状态应该增加观山权重
    weights_bull = engine._get_adjusted_weights("BULL")
    weights_bear = engine._get_adjusted_weights("BEAR")
    
    assert weights_bull['guanshan'] > weights_bear['guanshan']
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/unit/test_resonance_v2.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add core/resonance/ tests/unit/test_resonance_v2.py
git commit -m "feat: implement ResonanceEngineV2 with Voter, Matrix, Scanner"
```

---

## Phase 5: 集成测试与优化 (Week 9-10)

### Task 14: 端到端集成测试

**Files:**
- Create: `tests/integration/test_intelligence_upgrade.py`

- [ ] **Step 1: Create integration test**

```python
# tests/integration/test_intelligence_upgrade.py
import pytest
import numpy as np
import pandas as pd
from datetime import datetime

def test_full_intelligence_pipeline():
    """测试完整的智能化流水线"""
    # 1. 创建测试数据
    np.random.seed(42)
    n = 200
    data = pd.DataFrame({
        'open': np.random.randn(n).cumsum() + 100,
        'high': np.random.randn(n).cumsum() + 102,
        'low': np.random.randn(n).cumsum() + 98,
        'close': np.random.randn(n).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, n)
    })
    
    # 2. 测试Alpha因子
    from core.alpha import FactorLibrary
    library = FactorLibrary()
    
    def momentum(df):
        return df['close'].pct_change(20)
    
    library.register(momentum, 'momentum_20d', 'momentum')
    factors = library.compute_all(data)
    assert 'momentum_20d' in factors
    
    # 3. 测试市场状态检测
    from core.market_state.regime_detector_v2 import HMMDetector
    returns = data['close'].pct_change().dropna()
    
    detector = HMMDetector(n_regimes=4)
    detector.fit(returns)
    regimes = detector.predict(returns)
    assert len(regimes) == len(returns)
    
    # 4. 测试强化学习
    from core.rl import TradingEnvironment, PPOAgent
    env = TradingEnvironment(data)
    agent = PPOAgent(state_dim=20, action_dim=30)
    
    obs = env.reset()
    action, _, _ = agent.select_action(obs)
    assert 0 <= action < 30
    
    # 5. 测试共振引擎
    from core.resonance.engine_v2 import ResonanceEngineV2
    from signals.base import Signal
    
    signals = [
        Signal("test", "RB", "BUY", 0.8, 5.0, 3850, datetime.now(), "test", source_system="chufeng")
    ]
    
    engine = ResonanceEngineV2()
    result = engine.calculate("RB", signals, regimes[-1] if regimes else "RANGING")
    assert result.direction in ["BUY", "SELL", "HOLD"]

def test_adaptive_optimization():
    """测试自适应参数优化"""
    from core.adaptive import BayesianOptimizer, ParameterStore
    
    # 测试贝叶斯优化
    def objective(params):
        return -(params['x'] - 5) ** 2  # 最优解x=5
    
    param_space = {'x': {'type': 'float', 'low': 0, 'high': 10}}
    optimizer = BayesianOptimizer(objective, param_space, n_trials=20)
    result = optimizer.optimize()
    
    assert abs(result.best_params['x'] - 5) < 1.0  # 接近最优解
    
    # 测试参数存储
    store = ParameterStore()
    store.save('test_strategy', result.best_params, {'score': result.best_score})
    loaded = store.load_latest('test_strategy')
    assert loaded is not None
```

- [ ] **Step 2: Run integration tests**

Run: `pytest tests/integration/test_intelligence_upgrade.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_intelligence_upgrade.py
git commit -m "test: add end-to-end integration tests for intelligence upgrade"
```

---

### Task 15: 文档更新

**Files:**
- Modify: `ARCHITECTURE.md`
- Create: `docs/INTELLIGENCE_UPGRADE.md`

- [ ] **Step 1: Create intelligence upgrade documentation**

```markdown
# 策略智能化升级文档

## 概述

本文档描述交易策略中心的智能化升级内容，包括：
- 自适应参数优化
- 多因子Alpha挖掘
- 强化学习交易Agent
- 高级市场状态预测
- 智能策略组合

## 新增模块

### core/adaptive/
自适应参数优化模块
- `bayesian_optimizer.py`: 贝叶斯优化器
- `regime_aware_optimizer.py`: 市场状态感知优化
- `walk_forward_validator.py`: Walk-forward验证
- `parameter_store.py`: 参数版本管理
- `scheduler.py`: 优化调度器

### core/alpha/
多因子Alpha工厂
- `factor_library.py`: 因子库管理
- `factor_evaluator.py`: 因子评价
- `factor_combiner.py`: 因子组合
- `alpha101/`: Alpha101因子库

### core/rl/
强化学习模块
- `environments.py`: 交易环境
- `agents.py`: PPO Agent
- `config.py`: RL配置

## 使用示例

### 参数优化
```python
from core.adaptive import BayesianOptimizer

def objective(params):
    # 回测策略，返回Sharpe
    return backtest(params)

optimizer = BayesianOptimizer(objective, param_space)
result = optimizer.optimize()
print(f"最优参数: {result.best_params}")
```

### Alpha因子计算
```python
from core.alpha import FactorLibrary

library = FactorLibrary()
library.register(my_factor, 'my_factor', 'custom')
factors = library.compute_all(data)
```

### 强化学习训练
```python
from core.rl import TradingEnvironment, PPOAgent

env = TradingEnvironment(data)
agent = PPOAgent(state_dim=20, action_dim=30)

for episode in range(1000):
    obs = env.reset()
    done = False
    while not done:
        action, _, _ = agent.select_action(obs)
        obs, reward, done, info = env.step(action)
```

## 配置

配置文件位于 `config/adaptive_config.yaml`, `config/alpha_config.yaml`, `config/rl_config.yaml`

## 测试

运行所有测试：
```bash
pytest tests/unit/test_adaptive.py tests/unit/test_alpha.py tests/unit/test_rl.py -v
```
```

- [ ] **Step 2: Commit**

```bash
git add docs/INTELLIGENCE_UPGRADE.md
git commit -m "docs: add intelligence upgrade documentation"
```

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-06-12-strategy-intelligence-upgrade.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - 我为每个任务分发一个新的子代理，任务之间进行审查，快速迭代

**2. Inline Execution** - 在当前会话中使用executing-plans执行任务，批量执行带检查点

**选择哪种方式？**
