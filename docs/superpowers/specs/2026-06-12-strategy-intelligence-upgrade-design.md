# 策略智能化全栈升级设计文档

> 版本: v1.0  
> 日期: 2026-06-12  
> 项目路径: `D:\完整项目\trading-strategy-center\`  
> 目标: 实现策略智能化全栈升级，覆盖自适应参数、强化学习、Alpha挖掘、市场状态预测、策略组合智能

---

## 目录

1. [项目概述](#1-项目概述)
2. [当前状态分析](#2-当前状态分析)
3. [升级架构设计](#3-升级架构设计)
4. [模块详细设计](#4-模块详细设计)
5. [数据流设计](#5-数据流设计)
6. [API设计](#6-api设计)
7. [数据库设计](#7-数据库设计)
8. [实施计划](#8-实施计划)
9. [风险与缓解](#9-风险与缓解)
10. [验收标准](#10-验收标准)

---

## 1. 项目概述

### 1.1 项目目标

对现有交易策略中心进行智能化升级，实现：

- **自适应策略参数**: 参数根据市场状态自动调整，无需人工干预
- **强化学习优化**: 使用PPO/A2C等RL算法优化交易策略和仓位管理
- **多因子Alpha挖掘**: 自动发现和组合Alpha因子，提升策略超额收益
- **市场状态预测**: 更精准的市场regime预测和趋势识别
- **策略组合智能**: 策略间的动态配置和风险平价优化

### 1.2 约束条件

- 无特殊约束，追求功能完善和丰富性
- 渐进式升级，不影响现有系统稳定性
- 支持VPS部署环境

### 1.3 成功标准

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 策略智能化覆盖率 | >80% | 智能化模块数/总模块数 |
| 参数优化效率 | >5x | 优化时间缩短比例 |
| Alpha因子数量 | >50个 | 注册因子总数 |
| 市场状态识别准确率 | >75% | 回测验证 |
| 系统稳定性 | 99.9% | 可用性监控 |

---

## 2. 当前状态分析

### 2.1 模块完成度评估

| 模块 | 架构描述 | 实际实现 | 差距 |
|------|----------|----------|------|
| ML Pipeline | 12个子模块，5层管线 | 1个pipeline.py (4层简化版) | ~85% |
| 策略引擎 | 46+策略 + Alpha101 | 14策略 + 3过滤器 | ~70% |
| 共振引擎 | Voter+Matrix+Scanner | 单一ResonanceEngine | ~85% |
| 市场状态 | HMM+多因子+状态机 | 线性回归斜率 | ~75% |
| 进化引擎 | Tracker+ABTest+Scheduler | 单一遗传算法 | ~80% |

### 2.2 关键问题

#### 2.2.1 ML Pipeline问题
- **命名欺诈**: `pipeline.py`中"XGBoost"层实际使用RandomForestRegressor
- **模型为空壳**: `ml/models/`目录完全为空
- **训练不持久化**: 模型训练后仅存在内存中
- **无集成学习**: 缺少Stacking集成框架
- **无PPO RL Agent**: 架构文档提及但未实现
- **无LSTM预测器**: BiLSTM预测完全缺失

#### 2.2.2 策略引擎问题
- **策略数量不足**: 14策略 vs 46+目标
- **BaseStrategy未使用ABC**: 缺少抽象方法约束
- **Signal dataclass不完整**: 缺少score, source_system等字段
- **Registry无自动发现**: 需手动import注册
- **缺少关键指标**: SuperTrend, Williams %R, MFI等

#### 2.2.3 共振引擎问题
- **分组逻辑错误**: 按索引轮询分配而非按source_system分组
- **缺少三大子引擎**: Voter/Matrix/Scanner全部缺失
- **缺少WeightLearner**: 动态权重学习未实现
- **评分过于简单**: 未考虑confidence差异

#### 2.2.4 市场状态问题
- **无HMM实现**: 仅用线性回归斜率
- **StateMachine未集成**: 独立模块未被调用
- **无持续时间惩罚**: 易频繁切换
- **regime_detector与entropy_analyzer未集成**

#### 2.2.5 进化引擎问题
- **缺少架构组件**: PerformanceTracker/ABTester/Scheduler缺失
- **适应度函数单一**: 仅用Sharpe Ratio
- **无过拟合防护**: 缺少walk-forward验证
- **选择/交叉/变异策略粗糙**

---

## 3. 升级架构设计

### 3.1 目标架构

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 8: 智能决策层 (新增)                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ 自适应参数    │ │ Alpha工厂    │ │ 智能组合配置              │ │
│  │ 贝叶斯优化    │ │ 因子挖掘     │ │ 动态风险平价              │ │
│  │ + RL调参     │ │ + 因子评价   │ │ + 策略协同                │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Layer 7: 前端 (现有，增强可视化)                                 │
├─────────────────────────────────────────────────────────────────┤
│  Layer 6: API Gateway (现有)                                     │
├─────────────────────────────────────────────────────────────────┤
│  Layer 5: 核心引擎 (重构)                                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ 策略引擎v2   │ │ 共振引擎v2   │ │ 市场状态v2               │ │
│  │ 46+策略      │ │ Voter+Matrix │ │ HMM+多因子+状态机        │ │
│  │ +自动发现    │ │ +Scanner     │ │ +持续时间惩罚            │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: 异步任务层 (现有)                                      │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: ML 管线 (重构)                                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ 5层标准管线  │ │ Stacking集成 │ │ PPO RL Agent             │ │
│  │ HMM/XGB/LSTM│ │ + Meta学习   │ │ + LSTM预测               │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: 市场状态 + Cross-Symbol (现有，增强)                    │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: 数据层 (现有)                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 目录结构

```
trading-strategy-center/
├── core/
│   ├── adaptive/              # 自适应参数优化 (新增)
│   │   ├── __init__.py
│   │   ├── bayesian_optimizer.py
│   │   ├── regime_aware_optimizer.py
│   │   ├── walk_forward_validator.py
│   │   ├── parameter_store.py
│   │   └── scheduler.py
│   │
│   ├── alpha/                 # 多因子Alpha工厂 (新增)
│   │   ├── __init__.py
│   │   ├── factor_library.py
│   │   ├── alpha101/
│   │   ├── factor_evaluator.py
│   │   ├── factor_combiner.py
│   │   ├── factor_miner.py
│   │   └── factor_registry.py
│   │
│   ├── rl/                    # 强化学习 (新增)
│   │   ├── __init__.py
│   │   ├── environments.py
│   │   ├── agents.py
│   │   ├── rewards.py
│   │   ├── trainers.py
│   │   ├── adapters.py
│   │   └── config.py
│   │
│   ├── signals/               # 策略引擎 (重构)
│   │   ├── base.py            # 使用ABC
│   │   ├── registry.py        # 添加自动发现
│   │   ├── engine.py
│   │   ├── indicators.py      # 补充指标
│   │   ├── price_action.py
│   │   ├── layering/
│   │   └── strategies/        # 补充策略
│   │
│   ├── resonance/             # 共振引擎 (重构)
│   │   ├── engine_v2.py
│   │   ├── voter.py
│   │   ├── matrix.py
│   │   ├── scanner.py
│   │   ├── weight_learner.py
│   │   ├── synergy_analyzer.py
│   │   └── config.py
│   │
│   ├── market_state/          # 市场状态 (重构)
│   │   ├── regime_detector_v2.py
│   │   ├── multi_factor_detector.py
│   │   ├── regime_classifier.py
│   │   ├── state_machine_v2.py
│   │   ├── entropy_analyzer_v2.py
│   │   └── ensemble_detector.py
│   │
│   ├── evolution/             # 进化引擎 (重构)
│   │   ├── strategy_evolution_v2.py
│   │   ├── performance_tracker.py
│   │   ├── ab_tester.py
│   │   └── evolution_scheduler.py
│   │
│   └── ml/                    # ML管线 (重构)
│       ├── pipeline_v2.py
│       ├── trainer.py
│       ├── ensemble.py
│       ├── hmm_state.py
│       ├── lstm_predictor.py
│       ├── ppo_agent.py
│       ├── garch_predictor.py
│       ├── retrain_pipeline.py
│       └── model_registry.py
```

---

## 4. 模块详细设计

### 4.1 自适应参数优化模块 (`core/adaptive/`)

#### 4.1.1 贝叶斯优化器 (`bayesian_optimizer.py`)

```python
class BayesianOptimizer:
    """基于贝叶斯优化的参数搜索"""
    
    def __init__(self, objective_fn, param_space, n_trials=100):
        self.objective_fn = objective_fn
        self.param_space = param_space
        self.n_trials = n_trials
        self.history = []
        self.best_params = None
        self.best_score = -float('inf')
    
    def optimize(self) -> Dict:
        """执行优化，返回最优参数"""
        import optuna
        
        def objective(trial):
            params = {}
            for name, space in self.param_space.items():
                if space['type'] == 'int':
                    params[name] = trial.suggest_int(name, space['low'], space['high'])
                elif space['type'] == 'float':
                    params[name] = trial.suggest_float(name, space['low'], space['high'])
                elif space['type'] == 'categorical':
                    params[name] = trial.suggest_categorical(name, space['choices'])
            
            score = self.objective_fn(params)
            self.history.append({'params': params, 'score': score})
            
            if score > self.best_score:
                self.best_score = score
                self.best_params = params
            
            return score
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=self.n_trials)
        
        return self.best_params
    
    def suggest_next(self) -> Dict:
        """建议下一组探索参数"""
        # 基于历史数据的EI (Expected Improvement)
        pass
    
    def update(self, result: Dict):
        """更新优化器状态"""
        self.history.append(result)
        if result['score'] > self.best_score:
            self.best_score = result['score']
            self.best_params = result['params']
```

#### 4.1.2 状态感知优化器 (`regime_aware_optimizer.py`)

```python
class RegimeAwareOptimizer:
    """根据市场状态切换参数"""
    
    def __init__(self):
        self.regime_params = {}  # {regime: {strategy: params}}
        self.current_regime = None
    
    def optimize_by_regime(self, symbol: str, strategy: str, regime: str) -> Dict:
        """为特定市场状态优化参数"""
        # 获取该状态下的历史最优参数
        if regime in self.regime_params and strategy in self.regime_params[regime]:
            return self.regime_params[regime][strategy]
        
        # 执行新优化
        optimizer = BayesianOptimizer(...)
        params = optimizer.optimize()
        
        # 缓存结果
        if regime not in self.regime_params:
            self.regime_params[regime] = {}
        self.regime_params[regime][strategy] = params
        
        return params
    
    def switch_regime(self, new_regime: str):
        """市场状态切换时调整参数"""
        if new_regime != self.current_regime:
            self.current_regime = new_regime
            # 触发参数切换
```

#### 4.1.3 Walk-forward验证器 (`walk_forward_validator.py`)

```python
class WalkForwardValidator:
    """Walk-forward验证框架，防止过拟合"""
    
    def __init__(self, n_splits=5, train_ratio=0.7):
        self.n_splits = n_splits
        self.train_ratio = train_ratio
    
    def validate(self, strategy, params, data: pd.DataFrame) -> Dict:
        """执行walk-forward验证"""
        splits = self._create_splits(data)
        oos_returns = []
        
        for train_data, test_data in splits:
            # 在训练集上优化参数
            train_params = self._optimize_on_train(strategy, train_data)
            
            # 在测试集上验证
            oos_return = self._evaluate_on_test(strategy, train_params, test_data)
            oos_returns.append(oos_return)
        
        # 计算统计指标
        metrics = {
            'mean_oos_return': np.mean(oos_returns),
            'std_oos_return': np.std(oos_returns),
            'sharpe_oos': np.mean(oos_returns) / (np.std(oos_returns) + 1e-8),
            'is_stable': np.std(oos_returns) < 0.1,  # 稳定性阈值
        }
        
        return metrics
    
    def detect_overfitting(self, is_metrics: Dict, oos_metrics: Dict) -> bool:
        """检测过拟合"""
        # IS性能远好于OOS = 过拟合
        is_sharpe = is_metrics.get('sharpe', 0)
        oos_sharpe = oos_metrics.get('sharpe_oos', 0)
        
        return is_sharpe > oos_sharpe * 1.5  # 50%以上衰减视为过拟合
```

#### 4.1.4 参数存储 (`parameter_store.py`)

```python
class ParameterStore:
    """参数版本管理，持久化到数据库"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def save(self, strategy_name: str, params: Dict, metrics: Dict, version: int = None):
        """保存参数版本"""
        if version is None:
            version = self._get_next_version(strategy_name)
        
        record = ParameterVersion(
            strategy_name=strategy_name,
            version=version,
            params=json.dumps(params),
            metrics=json.dumps(metrics),
            created_at=datetime.now()
        )
        self.db.add(record)
        self.db.commit()
    
    def load_latest(self, strategy_name: str) -> Dict:
        """加载最新参数"""
        record = self.db.query(ParameterVersion)\
            .filter_by(strategy_name=strategy_name)\
            .order_by(ParameterVersion.version.desc())\
            .first()
        
        return json.loads(record.params) if record else None
    
    def rollback(self, strategy_name: str, version: int):
        """回滚到指定版本"""
        pass
```

### 4.2 多因子Alpha工厂 (`core/alpha/`)

#### 4.2.1 因子库管理 (`factor_library.py`)

```python
class FactorLibrary:
    """因子库管理器"""
    
    def __init__(self):
        self.factors = {}  # {name: FactorMeta}
        self.compute_fns = {}  # {name: compute_fn}
    
    def register(self, compute_fn, name: str, category: str, description: str = ""):
        """注册新因子"""
        self.factors[name] = FactorMeta(
            name=name,
            category=category,
            description=description,
            compute_fn=compute_fn
        )
        self.compute_fns[name] = compute_fn
    
    def compute_all(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算所有因子"""
        results = {}
        for name, fn in self.compute_fns.items():
            try:
                results[name] = fn(df)
            except Exception as e:
                logger.warning(f"Factor {name} computation failed: {e}")
        return results
    
    def get_factor(self, name: str) -> pd.Series:
        """获取单个因子"""
        return self.compute_fns.get(name)
    
    def list_factors(self, category: str = None) -> List[FactorMeta]:
        """列出因子"""
        if category:
            return [f for f in self.factors.values() if f.category == category]
        return list(self.factors.values())
```

#### 4.2.2 Alpha101因子实现

```python
# alpha101/alpha001.py
class Alpha001:
    """Alpha001: rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5
    
    描述: 价格动量因子，捕捉趋势反转
    类别: 价格动量
    """
    
    @staticmethod
    def compute(df: pd.DataFrame) -> pd.Series:
        returns = df['close'].pct_change()
        cond = returns < 0
        inner = pd.Series(
            np.where(cond, returns.rolling(20).std(), df['close']),
            index=df.index
        )
        powered = np.sign(inner) * np.abs(inner) ** 2
        return powered.rolling(5).apply(lambda x: np.argmax(x)) / 4 - 0.5

# alpha101/alpha002.py
class Alpha002:
    """Alpha002: -1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6)
    
    描述: 量价相关性因子
    类别: 量价关系
    """
    
    @staticmethod
    def compute(df: pd.DataFrame) -> pd.Series:
        vol_delta = np.log(df['volume']).diff(2)
        price_range = (df['close'] - df['open']) / df['open']
        
        return -1 * vol_delta.rank().rolling(6).corr(price_range.rank())
```

#### 4.2.3 因子评价器 (`factor_evaluator.py`)

```python
class FactorEvaluator:
    """因子有效性评价"""
    
    def calculate_ic(self, factor: pd.Series, returns: pd.Series, method='spearman') -> float:
        """计算信息系数 (IC)"""
        if method == 'spearman':
            return factor.rank().corr(returns.rank())
        return factor.corr(returns)
    
    def calculate_ir(self, factor: pd.Series, returns: pd.Series, period=20) -> float:
        """计算信息比率 (IR)"""
        rolling_ic = factor.rolling(period).corr(returns)
        return rolling_ic.mean() / (rolling_ic.std() + 1e-8)
    
    def calculate_turnover(self, factor: pd.Series, quantiles=5) -> float:
        """计算因子换手率"""
        quantile_labels = pd.qcut(factor, quantiles, labels=False, duplicates='drop')
        return (quantile_labels.diff() != 0).mean()
    
    def decay_analysis(self, factor: pd.Series, returns: pd.Series, max_lag=20) -> Dict:
        """因子衰减分析"""
        decays = []
        for lag in range(1, max_lag + 1):
            ic = factor.corr(returns.shift(-lag))
            decays.append({'lag': lag, 'ic': ic})
        
        return {
            'decays': decays,
            'half_life': self._find_half_life(decays),
            'is_persistent': decays[5]['ic'] > decays[0]['ic'] * 0.5
        }
    
    def generate_report(self, factor: pd.Series, returns: pd.Series) -> FactorReport:
        """生成因子评价报告"""
        return FactorReport(
            ic=self.calculate_ic(factor, returns),
            ir=self.calculate_ir(factor, returns),
            turnover=self.calculate_turnover(factor),
            decay=self.decay_analysis(factor, returns),
            grade=self._grade_factor(...)
        )
```

#### 4.2.4 因子组合器 (`factor_combiner.py`)

```python
class FactorCombiner:
    """因子组合器"""
    
    def equal_weight(self, factors: Dict[str, pd.Series]) -> pd.Series:
        """等权重组合"""
        combined = pd.DataFrame(factors)
        return combined.mean(axis=1)
    
    def ic_weight(self, factors: Dict[str, pd.Series], returns: pd.Series) -> pd.Series:
        """IC加权组合"""
        evaluator = FactorEvaluator()
        weights = {}
        
        for name, factor in factors.items():
            ic = abs(evaluator.calculate_ic(factor, returns))
            weights[name] = ic
        
        # 归一化权重
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}
        
        combined = pd.DataFrame(factors)
        return combined.mul(weights, axis=1).sum(axis=1)
    
    def regime_weight(self, factors: Dict[str, pd.Series], regime: str) -> pd.Series:
        """市场状态加权"""
        regime_weights = {
            'BULL': {'momentum': 0.4, 'value': 0.3, 'quality': 0.3},
            'BEAR': {'momentum': 0.2, 'value': 0.5, 'quality': 0.3},
            'RANGING': {'momentum': 0.3, 'value': 0.3, 'quality': 0.4},
        }
        
        weights = regime_weights.get(regime, {'equal': 1.0/len(factors)})
        # ... 应用权重
```

### 4.3 强化学习模块 (`core/rl/`)

#### 4.3.1 交易环境 (`environments.py`)

```python
import gym
from gym import spaces

class TradingEnvironment(gym.Env):
    """强化学习交易环境"""
    
    def __init__(self, data: pd.DataFrame, initial_capital=100000, 
                 commission=0.001, slippage=0.0005):
        super().__init__()
        
        self.data = data
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        # 动作空间: [HOLD, BUY, SELL] x 仓位比例 [0.1, 0.2, ..., 1.0]
        self.action_space = spaces.Discrete(3 * 10)  # 30个动作
        
        # 观察空间: 市场特征 + 持仓状态
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, 
            shape=(20,),  # 20个特征
            dtype=np.float32
        )
        
        self.reset()
    
    def reset(self):
        """重置环境"""
        self.current_step = 0
        self.equity = self.initial_capital
        self.position = 0  # -1, 0, 1
        self.entry_price = 0
        self.total_trades = 0
        self.win_trades = 0
        
        return self._get_observation()
    
    def step(self, action):
        """执行一步交易"""
        # 解析动作
        direction = action // 10 - 1  # -1, 0, 1
        size_pct = (action % 10 + 1) / 10  # 0.1 ~ 1.0
        
        # 记录当前状态
        old_equity = self.equity
        
        # 执行交易
        if direction != 0 and self.position == 0:
            # 开仓
            self._open_position(direction, size_pct)
        elif direction == 0 and self.position != 0:
            # 平仓
            self._close_position()
        elif direction * self.position < 0:
            # 反向开仓
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
    
    def _get_observation(self):
        """获取观察向量"""
        row = self.data.iloc[self.current_step]
        
        features = [
            row['close'] / row['open'] - 1,  # 日内收益
            row['volume'] / self.data['volume'].rolling(20).mean().iloc[self.current_step] - 1,  # 成交量比率
            row['close'] / self.data['close'].rolling(20).mean().iloc[self.current_step] - 1,  # 价格偏离
            # ... 更多特征
        ]
        
        # 添加持仓状态
        features.extend([
            self.position,
            self.equity / self.initial_capital - 1,
            (self.current_step - self.entry_price) / (self.entry_price + 1e-8) if self.position != 0 else 0
        ])
        
        return np.array(features, dtype=np.float32)
    
    def _calculate_reward(self, old_equity):
        """计算奖励"""
        pnl = (self.equity - old_equity) / old_equity
        
        # 交易成本惩罚
        cost_penalty = abs(pnl) * 0.1 if pnl != 0 else 0
        
        # 风险惩罚
        drawdown = max(0, self._get_max_drawdown() - 0.1)
        risk_penalty = drawdown * 0.5
        
        return pnl - cost_penalty - risk_penalty
```

#### 4.3.2 PPO Agent (`agents.py`)

```python
import torch
import torch.nn as nn
import torch.optim as optim

class ActorCritic(nn.Module):
    """Actor-Critic网络"""
    
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super().__init__()
        
        # Actor网络
        self.actor = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Softmax(dim=-1)
        )
        
        # Critic网络
        self.critic = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(self, state):
        action_probs = self.actor(state)
        value = self.critic(state)
        return action_probs, value
    
    def get_action(self, state):
        action_probs, value = self.forward(state)
        dist = torch.distributions.Categorical(action_probs)
        action = dist.sample()
        return action.item(), dist.log_prob(action), value
    
    def evaluate(self, state, action):
        action_probs, value = self.forward(state)
        dist = torch.distributions.Categorical(action_probs)
        return dist.log_prob(action), dist.entropy(), value


class PPOAgent:
    """PPO强化学习Agent"""
    
    def __init__(self, state_dim, action_dim, lr=3e-4, gamma=0.99, 
                 epsilon=0.2, batch_size=64):
        self.gamma = gamma
        self.epsilon = epsilon
        self.batch_size = batch_size
        
        self.network = ActorCritic(state_dim, action_dim)
        self.optimizer = optim.Adam(self.network.parameters(), lr=lr)
        
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
    
    def select_action(self, state):
        """选择动作"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        action, log_prob, value = self.network.get_action(state_tensor)
        
        self.states.append(state)
        self.actions.append(action)
        self.log_probs.append(log_prob.item())
        self.values.append(value.item())
        
        return action
    
    def update(self):
        """PPO更新"""
        # 计算优势函数
        returns = self._compute_returns()
        advantages = returns - np.array(self.values)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # 转换为tensor
        states = torch.FloatTensor(np.array(self.states))
        actions = torch.LongTensor(self.actions)
        old_log_probs = torch.FloatTensor(self.log_probs)
        advantages = torch.FloatTensor(advantages)
        returns = torch.FloatTensor(returns)
        
        # 多轮更新
        for _ in range(4):  # 4 epochs
            _, new_log_probs, entropy, new_values = self.network.evaluate(states, actions)
            
            # PPO clipping
            ratio = torch.exp(new_log_probs - old_log_probs)
            clipped_ratio = torch.clamp(ratio, 1 - self.epsilon, 1 + self.epsilon)
            
            # 损失计算
            actor_loss = -torch.min(ratio * advantages, clipped_ratio * advantages).mean()
            critic_loss = (new_values.squeeze() - returns).pow(2).mean()
            entropy_loss = -entropy.mean() * 0.01
            
            total_loss = actor_loss + 0.5 * critic_loss + entropy_loss
            
            # 更新
            self.optimizer.zero_grad()
            total_loss.backward()
            self.optimizer.step()
        
        # 清空缓冲区
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
    
    def _compute_returns(self):
        """计算折扣回报"""
        returns = []
        R = 0
        for r in reversed(self.rewards):
            R = r + self.gamma * R
            returns.insert(0, R)
        return np.array(returns)
    
    def save(self, path):
        """保存模型"""
        torch.save(self.network.state_dict(), path)
    
    def load(self, path):
        """加载模型"""
        self.network.load_state_dict(torch.load(path))
```

### 4.4 市场状态预测模块 (`core/market_state/`)

#### 4.4.1 HMM检测器 (`regime_detector_v2.py`)

```python
from hmmlearn import GaussianHMM

class HMMDetector:
    """基于隐马尔可夫模型的市场状态检测"""
    
    def __init__(self, n_regimes=4, covariance_type='full', n_iter=100):
        self.n_regimes = n_regimes
        self.model = GaussianHMM(
            n_components=n_regimes,
            covariance_type=covariance_type,
            n_iter=n_iter
        )
        self.regime_labels = {
            0: 'QUIET',      # 平静期
            1: 'TRENDING',   # 趋势期
            2: 'VOLATILE',   # 高波动
            3: 'CRISIS'      # 危机期
        }
    
    def fit(self, returns: pd.Series):
        """训练HMM模型"""
        X = returns.values.reshape(-1, 1)
        self.model.fit(X)
    
    def predict(self, returns: pd.Series) -> List[str]:
        """预测市场状态"""
        X = returns.values.reshape(-1, 1)
        states = self.model.predict(X)
        return [self.regime_labels[s] for s in states]
    
    def predict_proba(self, returns: pd.Series) -> pd.DataFrame:
        """预测各状态概率"""
        X = returns.values.reshape(-1, 1)
        probs = self.model.predict_proba(X)
        return pd.DataFrame(probs, columns=list(self.regime_labels.values()))
    
    def detect_change_point(self, returns: pd.Series, threshold=0.3) -> List[int]:
        """检测状态切换点"""
        probs = self.predict_proba(returns)
        
        change_points = []
        for i in range(1, len(probs)):
            max_prob_change = (probs.iloc[i] - probs.iloc[i-1]).abs().max()
            if max_prob_change > threshold:
                change_points.append(i)
        
        return change_points
```

#### 4.4.2 状态机 (`state_machine_v2.py`)

```python
class EnhancedStateMachine:
    """增强状态机，带持续时间约束"""
    
    def __init__(self, transition_matrix=None, min_duration=5, penalty_factor=0.8):
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
                return self.current_state, adjusted_confidence
            else:
                # 允许切换
                transition_prob = self.transition_matrix[self.current_state].get(observation, 0)
                if confidence * transition_prob > 0.3:  # 切换阈值
                    self.current_state = observation
                    self.current_duration = 0
                    return observation, confidence
                else:
                    return self.current_state, confidence * 0.5
```

#### 4.4.3 集成检测器 (`ensemble_detector.py`)

```python
class EnsembleRegimeDetector:
    """集成多个检测器的市场状态判断"""
    
    def __init__(self):
        self.hmm_detector = HMMDetector()
        self.multi_factor = MultiFactorDetector()
        self.entropy = EntropyAnalyzer()
        self.state_machine = EnhancedStateMachine()
        self.classifier = RegimeClassifier()
    
    def detect(self, df: pd.DataFrame) -> RegimeResult:
        """集成检测"""
        returns = df['close'].pct_change()
        
        # HMM检测
        hmm_result = self.hmm_detector.predict(returns)
        hmm_probs = self.hmm_detector.predict_proba(returns)
        
        # 多因子检测
        factor_result = self.multi_factor.detect(df)
        
        # 熵分析
        entropy_result = self.entropy.analyze(returns)
        
        # 集成分类
        final_regime = self.classifier.classify(
            hmm_result=hmm_result,
            hmm_probs=hmm_probs,
            factor_result=factor_result,
            entropy_result=entropy_result
        )
        
        # 状态机平滑
        smoothed_regime, confidence = self.state_machine.next_state(
            final_regime.regime, 
            final_regime.confidence
        )
        
        return RegimeResult(
            regime=smoothed_regime,
            confidence=confidence,
            duration=self.state_machine.current_duration,
            components={
                'hmm': hmm_result,
                'factor': factor_result,
                'entropy': entropy_result
            }
        )
```

---

## 5. 数据流设计

### 5.1 自适应参数优化数据流

```
┌─────────────────────────────────────────────────────────────────┐
│                    参数优化数据流                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MarketData ──────────────────────────────────────────────────┐ │
│       │                                                       │ │
│       ▼                                                       │ │
│  RegimeDetector ──→ CurrentRegime                             │ │
│       │                                                       │ │
│       ▼                                                       │ │
│  ParameterStore ──→ CachedParams                              │ │
│       │                                                       │ │
│       ▼                                                       │ │
│  RegimeAwareOptimizer ──→ OptimizedParams                     │ │
│       │                                                       │ │
│       ├──→ Strategy.set_params(optimized_params)              │ │
│       │                                                       │ │
│       └──→ ParameterStore.save(params, metrics)               │ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Alpha因子计算数据流

```
┌─────────────────────────────────────────────────────────────────┐
│                    Alpha因子数据流                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MarketData ──────────────────────────────────────────────────┐ │
│       │                                                       │ │
│       ▼                                                       │ │
│  FactorLibrary.compute_all(df) ──→ RawFactors{50+}           │ │
│       │                                                       │ │
│       ▼                                                       │ │
│  FactorEvaluator ──→ FactorReports{ic, ir, turnover}          │ │
│       │                                                       │ │
│       ▼                                                       │ │
│  FactorCombiner ──→ CombinedFactor                            │ │
│       │                                                       │ │
│       ▼                                                       │ │
│  StrategySignals ──→ ResonanceEngine ──→ FinalSignal          │ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 强化学习训练数据流

```
┌─────────────────────────────────────────────────────────────────┐
│                    RL训练数据流                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HistoricalData ──→ TradingEnvironment                         │
│       │                                                       │ │
│       ▼                                                       │ │
│  PPOAgent.select_action(state) ──→ Action                      │ │
│       │                                                       │ │
│       ▼                                                       │ │
│  Environment.step(action) ──→ (next_state, reward, done)       │ │
│       │                                                       │ │
│       ▼                                                       │ │
│  ReplayBuffer ──→ PPOAgent.update()                            │ │
│       │                                                       │ │
│       ▼                                                       │ │
│  TrainedAgent ──→ RLStrategyAdapter ──→ TradingSignal         │ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. API设计

### 6.1 自适应参数API

| Method | Path | 描述 |
|--------|------|------|
| POST | `/api/v1/adaptive/optimize` | 触发参数优化 |
| GET | `/api/v1/adaptive/params/{strategy}` | 获取最优参数 |
| GET | `/api/v1/adaptive/history/{strategy}` | 参数优化历史 |
| POST | `/api/v1/adaptive/validate` | Walk-forward验证 |
| PUT | `/api/v1/adaptive/rollback/{strategy}/{version}` | 回滚参数 |

### 6.2 Alpha因子API

| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/alpha/factors` | 列出所有因子 |
| GET | `/api/v1/alpha/factor/{name}` | 因子详情 |
| POST | `/api/v1/alpha/compute` | 计算因子值 |
| GET | `/api/v1/alpha/report/{name}` | 因子评价报告 |
| POST | `/api/v1/alpha/combine` | 因子组合 |
| GET | `/api/v1/alpha/correlations` | 因子相关性矩阵 |

### 6.3 强化学习API

| Method | Path | 描述 |
|--------|------|------|
| POST | `/api/v1/rl/train` | 触发RL训练 |
| GET | `/api/v1/rl/status/{job_id}` | 训练状态 |
| GET | `/api/v1/rl/agent/{id}` | Agent详情 |
| POST | `/api/v1/rl/predict` | Agent预测 |
| GET | `/api/v1/rl/agents` | Agent列表 |

---

## 7. 数据库设计

### 7.1 新增表

```python
# 参数版本表
class ParameterVersion(Base):
    __tablename__ = "parameter_versions"
    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(100), index=True)
    version = Column(Integer)
    params = Column(Text)  # JSON
    metrics = Column(Text)  # JSON
    created_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

# 因子注册表
class FactorRegistration(Base):
    __tablename__ = "factor_registrations"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    category = Column(String(50))
    description = Column(Text)
    compute_fn = Column(String(200))
    ic_mean = Column(Float)
    ir_mean = Column(Float)
    turnover = Column(Float)
    grade = Column(String(10))
    version = Column(Integer)
    created_at = Column(DateTime)

# RL Agent表
class RLAgent(Base):
    __tablename__ = "rl_agents"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    agent_type = Column(String(50))  # PPO, A2C, SAC
    state_dim = Column(Integer)
    action_dim = Column(Integer)
    hyperparams = Column(Text)  # JSON
    metrics = Column(Text)  # JSON
    model_path = Column(String(200))
    created_at = Column(DateTime)
    last_trained = Column(DateTime)
```

---

## 8. 实施计划

### 8.1 优先级矩阵

| 优先级 | 模块 | 工作量 | 价值 | 依赖 |
|--------|------|--------|------|------|
| P0 | 修复命名欺诈(RandomForest→XGBoost) | 1天 | 高 | 无 |
| P0 | Signal字段补全(source_system/score) | 2天 | 高 | 无 |
| P0 | 共振引擎分组修复 | 2天 | 高 | Signal字段 |
| P1 | HMM市场状态检测器 | 3天 | 高 | hmmlearn |
| P1 | 自适应参数优化(贝叶斯) | 5天 | 高 | optuna |
| P1 | Alpha101因子库(前20个) | 5天 | 高 | 无 |
| P2 | 强化学习Agent(PPO) | 7天 | 中 | gym |
| P2 | 策略权重学习器 | 3天 | 中 | 历史数据 |
| P2 | 策略协同分析 | 3天 | 中 | 共振引擎 |
| P3 | 完整Alpha101(101个) | 10天 | 中 | 因子框架 |
| P3 | LSTM预测器 | 5天 | 中 | torch |
| P3 | 策略自动发现 | 2天 | 低 | pkgutil |

### 8.2 10周实施计划

```
Week 1-2: 基础修复与框架搭建
├── 修复命名欺诈和Signal字段
├── 搭建adaptive/、alpha/、rl/目录结构
├── 实现贝叶斯优化器核心
└── 实现Alpha101基础框架

Week 3-4: 市场状态与参数优化
├── 实现HMM检测器
├── 集成状态机到regime_detector
├── 实现状态感知参数切换
└── 实现Walk-forward验证

Week 5-6: Alpha因子与策略增强
├── 实现前20个Alpha101因子
├── 实现因子评价器
├── 实现因子组合器
└── 补充10个缺失策略

Week 7-8: 强化学习与共振重构
├── 实现交易环境
├── 实现PPO Agent
├── 重构共振引擎三大子引擎
└── 实现权重学习器

Week 9-10: 集成测试与优化
├── 端到端集成测试
├── 性能优化
├── 文档更新
└── 部署验证
```

---

## 9. 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| HMM训练收敛慢 | 高 | 中 | 限制迭代次数，使用更简单的协方差类型 |
| Alpha因子过拟合 | 高 | 高 | Walk-forward验证，样本外测试 |
| RL训练不稳定 | 中 | 高 | 课程学习，渐进式难度 |
| 系统复杂度增加 | 中 | 中 | 模块化设计，充分测试 |
| 计算资源不足 | 中 | 低 | 异步任务，批量处理 |

---

## 10. 验收标准

### 10.1 功能验收

| 功能 | 验收标准 |
|------|----------|
| 自适应参数 | 1. 能根据regime自动切换参数<br>2. 优化后策略Sharpe提升>10%<br>3. Walk-forward验证通过 |
| Alpha因子 | 1. 至少50个因子注册<br>2. 因子IC>0.02的因子占比>30%<br>3. 因子组合效果优于单因子 |
| 强化学习 | 1. PPO Agent能在模拟环境学习<br>2. 测试集收益>0<br>3. 与现有策略融合信号稳定 |
| 市场状态 | 1. HMM识别准确率>70%<br>2. 状态切换延迟<5天<br>3. 集成检测优于单一检测 |

### 10.2 性能验收

| 指标 | 目标值 |
|------|--------|
| 单次参数优化时间 | <5分钟 |
| 因子计算延迟 | <100ms/品种 |
| RL推理延迟 | <50ms |
| 状态检测延迟 | <200ms |

### 10.3 稳定性验收

| 指标 | 目标值 |
|------|--------|
| 系统可用性 | >99.9% |
| 内存占用增长 | <20% |
| 数据库查询延迟 | <50ms |

---

## 附录

### A. 依赖清单

**新增Python依赖:**
```
# 自适应优化
optuna>=3.0

# 强化学习
gymnasium>=0.29
torch>=2.0

# HMM
hmmlearn>=0.3

# 因子挖掘
# 无额外依赖，使用现有numpy/pandas
```

### B. 配置文件

```yaml
# config/adaptive_config.yaml
adaptive:
  bayesian:
    n_trials: 100
    timeout: 300  # 秒
  
  regime_aware:
    cache_ttl: 3600  # 1小时
    min_regime_duration: 5
  
  walk_forward:
    n_splits: 5
    train_ratio: 0.7

# config/alpha_config.yaml
alpha:
  evaluator:
    min_ic: 0.02
    min_ir: 0.5
    max_turnover: 0.3
  
  combiner:
    default_method: 'ic_weight'

# config/rl_config.yaml
rl:
  ppo:
    learning_rate: 0.0003
    gamma: 0.99
    epsilon: 0.2
    batch_size: 64
    hidden_dim: 256
    n_episodes: 1000
```

---

**文档版本:** v1.0  
**最后更新:** 2026-06-12  
**作者:** AI Assistant
