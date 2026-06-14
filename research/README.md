# Jupyter研究环境

量化交易研究笔记本和工具集

## 目录结构

```
research/
├── notebooks/              # Jupyter笔记本
│   ├── 01_data_exploration.ipynb
│   ├── 02_factor_analysis.ipynb
│   ├── 03_strategy_development.ipynb
│   ├── 04_backtest_analysis.ipynb
│   └── 05_model_training.ipynb
├── factor_lab/            # 因子研究工具
│   ├── factor_analyzer.py
│   ├── factor_combiner.py
│   └── ic_calculator.py
├── templates/             # 研究模板
│   ├── alpha_research_template.ipynb
│   └── strategy_research_template.ipynb
└── utils/                 # 工具函数
    ├── data_loader.py
    └── visualization.py
```

## 快速开始

### 安装Jupyter

```bash
pip install jupyter jupyterlab ipywidgets matplotlib seaborn
```

### 启动Jupyter Lab

```bash
cd research
jupyter lab
```

### 或使用Jupyter Notebook

```bash
cd research/notebooks
jupyter notebook
```

## 研究笔记本

### 1. 数据探索 (01_data_exploration.ipynb)

- 数据源连接测试
- 数据质量检查
- 基础统计分析
- 可视化探索

### 2. 因子分析 (02_factor_analysis.ipynb)

- Alpha因子计算
- IC/IR分析
- 因子分层回测
- 因子组合优化

### 3. 策略开发 (03_strategy_development.ipynb)

- 策略逻辑实现
- 参数优化
- 信号回测
- 绩效评估

### 4. 回测分析 (04_backtest_analysis.ipynb)

- 完整回测流程
- 多策略对比
- Walk-forward验证
- 风险分析

### 5. 模型训练 (05_model_training.ipynb)

- 机器学习模型训练
- 时序模型（TFT/N-BEATS）
- 强化学习训练
- 模型评估

## 因子研究工具

### FactorAnalyzer - 因子分析器

```python
from research.factor_lab.factor_analyzer import FactorAnalyzer

analyzer = FactorAnalyzer()

# IC分析
ic_results = analyzer.calculate_ic(
    factor_values=factor_df,
    returns=future_returns,
    periods=[1, 5, 10]
)

# 分层回测
layered_results = analyzer.layered_backtest(
    factor='alpha001',
    n_quantiles=5
)

# 因子衰减分析
decay = analyzer.ic_decay(factor='alpha001', max_periods=20)
```

### FactorCombiner - 因子组合器

```python
from research.factor_lab.factor_combiner import FactorCombiner

combiner = FactorCombiner()

# IC加权组合
combined = combiner.ic_weighted_combine(
    factors=['alpha001', 'alpha002', 'alpha003'],
    ic_values=[0.05, 0.08, 0.06]
)

# 等权组合
combined = combiner.equal_weighted_combine(factors)

# 优化组合
combined = combiner.optimize_combine(
    factors=factors,
    method='max_sharpe'
)
```

## 使用示例

### 示例1: 快速因子测试

```python
import sys
sys.path.append('..')

from core.data.market_data_manager import MarketDataManager
from core.alpha.alpha101.factor_registry import FactorRegistry
from research.factor_lab.factor_analyzer import FactorAnalyzer

# 1. 获取数据
manager = MarketDataManager()
df = await manager.get_daily('RB', start='2020-01-01', end='2024-12-31')

# 2. 计算因子
registry = FactorRegistry()
alpha001 = registry.get('alpha001')
factor_values = alpha001.compute(df, 'RB')

# 3. 因子分析
analyzer = FactorAnalyzer()
ic = analyzer.calculate_ic(factor_values, df['close'].pct_change().shift(-1))

print(f"IC: {ic}")
```

### 示例2: 策略回测

```python
from signals.registry import get_strategy
from backtest.vectorized_engine import VectorizedBacktest

# 1. 获取策略
strategy = get_strategy('trend_ma_cross')

# 2. 配置回测
backtest = VectorizedBacktest(
    strategy=strategy,
    initial_capital=1_000_000,
    commission=0.0003
)

# 3. 运行回测
result = backtest.run(
    symbol='RB',
    start_date='2023-01-01',
    end_date='2024-12-31'
)

# 4. 查看结果
print(f"年化收益: {result.annual_return:.2%}")
print(f"夏普比率: {result.sharpe_ratio:.2f}")
print(f"最大回撤: {result.max_drawdown:.2%}")
```

### 示例3: 时序模型训练

```python
from ml.models.tft_model import train_tft_for_symbol
from ml.models.nbeats_model import train_nbeats_for_symbol

# TFT模型
tft_model = train_tft_for_symbol(
    data=df,
    symbol='RB',
    sequence_length=20,
    prediction_horizon=5
)

# N-BEATS模型
nbeats_model = train_nbeats_for_symbol(
    data=df['close'],
    symbol='RB',
    lookback=30,
    forecast_horizon=5
)

# 预测
predictions_tft = tft_model.predict(X_test)
predictions_nbeats = nbeats_model.predict(X_test_nbeats)
```

## 可视化工具

研究环境预装可视化工具：

- **matplotlib**: 基础图表
- **seaborn**: 统计可视化
- **plotly**: 交互式图表
- **lightweight-charts**: TradingView风格K线图

## 最佳实践

### 1. 因子研究流程

1. 因子计算和验证
2. IC分析（相关性）
3. 分层回测（单调性）
4. 因子组合优化
5. 实盘前验证

### 2. 策略研究流程

1. 策略逻辑设计
2. 历史数据回测
3. 参数敏感性分析
4. Walk-forward验证
5. 风险评估

### 3. 模型研究流程

1. 特征工程
2. 模型训练
3. 样本外验证
4. 过拟合检测
5. 模型解释性分析

## 注意事项

1. **数据泄漏**: 确保特征不包含未来信息
2. **过拟合**: 使用交叉验证和样本外测试
3. **幸存者偏差**: 考虑已退市品种
4. **前视偏差**: 使用当时可获得的数据
5. **交易成本**: 包含滑点和手续费

## 资源链接

- [Alpha101因子文档](../docs/alpha101.md)
- [策略开发指南](../docs/strategy_development.md)
- [回测最佳实践](../docs/backtest_best_practices.md)
- [API文档](http://localhost:8000/docs)

---

**开始探索，祝研究顺利！** 🔬📊
