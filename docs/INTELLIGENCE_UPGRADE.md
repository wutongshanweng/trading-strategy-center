# Intelligence Upgrade Documentation

## Overview

The Intelligence Upgrade module enhances the trading strategy center with three major components:

1. **Adaptive Optimization** - Bayesian optimization, regime-aware tuning, and parameter management
2. **Alpha Factor Library** - Modular factor computation, evaluation, and combination
3. **Reinforcement Learning** - PPO-based trading agent with custom environments

---

## Module Architecture

```
trading-strategy-center/
├── core/
│   ├── adaptive/          # Adaptive optimization modules
│   │   ├── bayesian_optimizer.py
│   │   ├── regime_aware_optimizer.py
│   │   ├── walk_forward_validator.py
│   │   ├── parameter_store.py
│   │   └── scheduler.py
│   ├── alpha/             # Alpha factor modules
│   │   ├── factor_library.py
│   │   ├── factor_evaluator.py
│   │   ├── factor_combiner.py
│   │   └── alpha101/      # Built-in alpha factors
│   └── rl/                # Reinforcement learning modules
│       ├── environments.py
│       ├── agents.py
│       └── config.py
└── market_state/          # Market regime detection
    ├── regime_detector_v2.py  # HMM-based detector
    └── state_machine_v2.py
```

---

## 1. Alpha Factor Library

### Quick Start

```python
from core.alpha import FactorLibrary, FactorEvaluator, FactorCombiner
from core.alpha.alpha101 import Alpha001, Alpha002, Alpha003
import pandas as pd

# Create factor library
library = FactorLibrary()

# Register built-in factors
library.register("alpha001", lambda d, **kw: Alpha001().compute(d), category="momentum")
library.register("alpha002", lambda d, **kw: Alpha002().compute(d), category="volume")

# Compute factors
factors_df = library.compute_all(price_data)
```

### FactorLibrary API

| Method | Description |
|--------|-------------|
| `register(name, compute_fn, category, description, params)` | Register a new factor |
| `get_factor(name)` | Get factor metadata |
| `list_factors(category=None)` | List all factors or filter by category |
| `compute_all(data, factors=None)` | Compute all or selected factors |
| `remove_factor(name)` | Remove a factor from library |
| `get_categories()` | Get all unique categories |

### FactorEvaluator API

```python
evaluator = FactorEvaluator(forward_returns=returns, periods=1)

# Information Coefficient
ic_series = evaluator.calculate_ic(factor_values, method="pearson")

# Information Ratio
ir = evaluator.calculate_ir(factor_values)

# Turnover
turnover = evaluator.calculate_turnover(factor_values, quantile=0.2)

# Full report
report = evaluator.generate_report("my_factor", factor_values)
```

### FactorCombiner API

```python
combiner = FactorCombiner(factors_df)

# Equal weight combination
combined = combiner.equal_weight()

# IC-weighted combination
combined = combiner.ic_weight(ic_values={"factor_a": 0.5, "factor_b": 0.3})

# Regime-aware combination
combined = combiner.regime_weight(regimes=regimes, regime_weights=regime_weights)

# Normalization
normalized = combiner.normalize_factors(method="zscore")  # or "minmax", "rank"
```

### Built-in Alpha Factors (Alpha101)

| Factor | Category | Description |
|--------|----------|-------------|
| Alpha001 | momentum | Price momentum - close/open ratio |
| Alpha002 | volume | Volume-based factor |
| Alpha003 | volatility | Volatility-based factor |

---

## 2. Adaptive Optimization

### Bayesian Optimization

```python
from core.adaptive import BayesianOptimizer
from core.adaptive.bayesian_optimizer import ParameterSpace

# Define parameter space
param_space = [
    ParameterSpace("learning_rate", 1e-5, 1e-1, log_scale=True),
    ParameterSpace("n_estimators", 10, 500),
    ParameterSpace("max_depth", 3, 20),
]

# Define objective function
def objective(params):
    # Train model with params, return validation score
    return score

# Create optimizer
optimizer = BayesianOptimizer(
    param_space=param_space,
    objective=objective,
    n_initial=5,
    random_state=42,
)

# Run optimization
best_params, best_score = optimizer.optimize(n_iterations=20)
```

### Regime-Aware Optimization

```python
from core.adaptive import RegimeAwareOptimizer

def objective(params, regime):
    """Objective that varies by market regime."""
    base_score = train_and_evaluate(params)
    if regime == "trending":
        return base_score * 1.1  # Boost in trending markets
    return base_score

optimizer = RegimeAwareOptimizer(
    param_space=param_space,
    objective=objective,
    regime_detector=detect_regime,
)

result = optimizer.optimize(market_data, n_iterations=20)
print(result["regime"], result["best_params"], result["best_score"])
```

### Parameter Store

```python
from core.adaptive import ParameterStore

store = ParameterStore("./parameter_store")

# Save parameters
store.save("strategy_A", {"lr": 0.01, "depth": 5}, score=0.85)
store.save("strategy_A", {"lr": 0.02, "depth": 3}, score=0.92)

# Load latest
latest = store.load_latest("strategy_A")

# Get best version
best = store.get_best("strategy_A", higher_is_better=True)

# List all versions
versions = store.list_versions("strategy_A")

# Export strategy history
export = store.export_strategy("strategy_A")
```

### Walk-Forward Validation

```python
from core.adaptive import WalkForwardValidator

validator = WalkForwardValidator(
    train_ratio=0.7,
    n_splits=5,
    expanding=True,
    min_train_size=500,
)

# Get train/test splits
splits = validator.split(n_observations=2000)

# Run validation
report = validator.validate(
    data=price_data,
    objective=objective_fn,
    optimizer_class=BayesianOptimizer,
    param_space=param_space,
    n_optimization_iter=20,
)

# Check robustness
is_robust = validator.check_robustness(report)
is_overfit = validator.detect_overfitting(report)
```

---

## 3. Reinforcement Learning

### Trading Environment

```python
from core.rl import TradingEnvironment
import pandas as pd

# Create environment with OHLCV data
env = TradingEnvironment(
    data=ohlcv_df,
    initial_balance=100000.0,
    commission_rate=0.001,
    slippage=0.0001,
    max_position=1.0,
    reward_scaling=1.0,
    lookback_window=60,
)

# Reset and step
obs = env.reset(seed=42)
obs, reward, done, info = env.step(action)  # action: 0=hold, 1=buy, 2=sell
```

### PPO Agent

```python
from core.rl import PPOAgent

agent = PPOAgent(
    state_dim=env.observation_space_size,
    action_dim=env.action_space_size,
    hidden_dim=256,
    learning_rate=3e-4,
    gamma=0.99,
    gae_lambda=0.95,
    clip_epsilon=0.2,
)

# Select action
action, log_prob, value = agent.select_action(obs, training=True)

# Store experience
agent.store_experience(obs, action, reward, next_obs, done, log_prob, value)

# Update agent
metrics = agent.update(num_epochs=10, batch_size=64)

# Save/Load
agent.save("./models/rl_agent")
agent.load("./models/rl_agent")
```

### RL Configuration

Default configuration in `core/rl/config.py`:

```python
RL_CONFIG = {
    "environment": {
        "initial_balance": 100000.0,
        "commission_rate": 0.001,
        "slippage": 0.0001,
        "max_position": 1.0,
        "reward_scaling": 1.0,
        "transaction_cost_penalty": 0.001,
    },
    "agent": {
        "learning_rate": 3e-4,
        "gamma": 0.99,
        "gae_lambda": 0.95,
        "clip_epsilon": 0.2,
        "entropy_coef": 0.01,
        "value_loss_coef": 0.5,
        "max_grad_norm": 0.5,
        "hidden_dim": 256,
    },
    "training": {
        "num_episodes": 1000,
        "max_steps_per_episode": 500,
        "update_interval": 2048,
        "num_epochs": 10,
        "batch_size": 64,
        "eval_interval": 10,
        "save_interval": 50,
    },
    "data": {
        "lookback_window": 60,
        "feature_columns": ["open", "high", "low", "close", "volume", ...],
    },
}
```

---

## 4. Market Regime Detection

### HMM-Based Detector

```python
from market_state.regime_detector_v2 import HMMDetector, RegimeV2

detector = HMMDetector(n_regimes=4, covariance_type="full", n_iter=100)
detector.fit(returns_series)

# Predict regimes
regimes = detector.predict(returns_series)  # List[str]: QUIET, TRENDING, VOLATILE, CRISIS

# Get probabilities
proba_df = detector.predict_proba(returns_series)

# Detect change points
change_points = detector.detect_change_point(returns_series, threshold=0.3)
```

### Regime Values

| Regime | Description |
|--------|-------------|
| `QUIET` | Low volatility, mean-reverting |
| `TRENDING` | Strong directional moves |
| `VOLATILE` | High volatility, no clear direction |
| `CRISIS` | Extreme volatility, market stress |

---

## 5. End-to-End Pipeline Example

```python
from core.alpha import FactorLibrary, FactorEvaluator, FactorCombiner
from core.alpha.alpha101 import Alpha001, Alpha002, Alpha003
from core.rl import TradingEnvironment, PPOAgent
from core.adaptive import BayesianOptimizer, ParameterStore
from core.adaptive.bayesian_optimizer import ParameterSpace
from market_state.regime_detector_v2 import HMMDetector
import pandas as pd
import numpy as np

# 1. Load data
data = pd.read_csv("market_data.csv", index_col=0, parse_dates=True)

# 2. Compute alpha factors
library = FactorLibrary()
library.register("momentum", lambda d, **kw: Alpha001().compute(d))
library.register("volume", lambda d, **kw: Alpha002().compute(d))
factors_df = library.compute_all(data)

# 3. Detect market regime
returns = data["close"].pct_change().dropna()
detector = HMMDetector(n_regimes=4, n_iter=100)
detector.fit(returns)
regimes = detector.predict(returns)

# 4. Combine factors with regime-aware weighting
combiner = FactorCombiner(factors_df)
combined_signal = combiner.equal_weight()

# 5. Add signal to data for RL
data["signal"] = combined_signal

# 6. Train RL agent
env = TradingEnvironment(data.dropna(), lookback_window=60)
agent = PPOAgent(
    state_dim=env.observation_space_size,
    action_dim=env.action_space_size,
)

for episode in range(100):
    obs = env.reset()
    done = False
    while not done:
        action, log_prob, value = agent.select_action(obs)
        next_obs, reward, done, info = env.step(action)
        agent.store_experience(obs, action, reward, next_obs, done, log_prob, value)
        obs = next_obs
    agent.update()

# 7. Optimize parameters
def objective(params):
    # Backtest with given parameters
    return sharpe_ratio

optimizer = BayesianOptimizer(
    param_space=[ParameterSpace("lookback", 20, 120)],
    objective=objective,
)
best_params, best_score = optimizer.optimize(n_iterations=20)

# 8. Store optimal parameters
store = ParameterStore("./params")
store.save("rl_strategy", best_params, best_score)
```

---

## Test Commands

```bash
# Run all integration tests
pytest tests/integration/test_intelligence_upgrade.py -v

# Run specific test classes
pytest tests/integration/test_intelligence_upgrade.py::TestAlphaFactorPipeline -v
pytest tests/integration/test_intelligence_upgrade.py::TestRLPipeline -v
pytest tests/integration/test_intelligence_upgrade.py::TestAdaptivePipeline -v
pytest tests/integration/test_intelligence_upgrade.py::TestMarketStatePipeline -v
pytest tests/integration/test_intelligence_upgrade.py::TestFullIntelligencePipeline -v

# Run unit tests
pytest tests/unit/test_alpha.py -v
pytest tests/unit/test_rl.py -v
pytest tests/unit/test_adaptive.py -v

# Run all tests
pytest tests/ -v
```

---

## Configuration Reference

### Bayesian Optimizer Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_initial` | int | 5 | Number of initial random trials |
| `random_state` | int | None | Random seed for reproducibility |
| `clip_epsilon` | float | 0.2 | PPO clipping parameter |

### RL Environment Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `initial_balance` | float | 100000.0 | Starting capital |
| `commission_rate` | float | 0.001 | Trading commission (0.1%) |
| `slippage` | float | 0.0001 | Price slippage (0.01%) |
| `max_position` | float | 1.0 | Maximum position size |
| `reward_scaling` | float | 1.0 | Reward multiplier |
| `lookback_window` | int | 60 | Observation window size |

### Walk-Forward Validator Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `train_ratio` | float | 0.7 | Train/test split ratio |
| `n_splits` | int | 5 | Number of validation windows |
| `expanding` | bool | True | Expanding vs sliding window |
| `min_train_size` | int | 0 | Minimum training set size |
