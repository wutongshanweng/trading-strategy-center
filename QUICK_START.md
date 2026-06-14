# 交易策略中心 - 快速入门指南

> 版本: v0.1.0
> 更新: 2026-06-14

## 目录
1. [系统概述](#系统概述)
2. [快速启动](#快速启动)
3. [核心功能使用](#核心功能使用)
4. [策略开发](#策略开发)
5. [API参考](#api参考)
6. [常见问题](#常见问题)

---

## 系统概述

交易策略中心是一个**企业级量化交易平台**，整合了三个独立系统（观山/楚风/听海）的核心能力：

### 核心特性
- ✅ **101个Alpha因子** + 遗传编程因子挖掘
- ✅ **多策略融合** 趋势/均值回复/动量/突破/套利
- ✅ **智能共振** 三系统信号加权融合
- ✅ **强化学习** DQN/SAC/TD3/MADDPG
- ✅ **期权交易** 完整定价引擎 + Greeks管理
- ✅ **风险管理** 实时VaR/CVaR + 多级止损
- ✅ **向量化回测** 秒级回测 + Walk-forward验证

### 系统架构
```
Frontend (React)
    ↓
API Gateway (FastAPI + WebSocket)
    ↓
Core Engine (策略/共振/风险/组合)
    ↓
Data Layer (16类数据源 + 二级缓存)
```

---

## 快速启动

### 前置要求
- Python 3.10+
- Node.js 18+ (前端)
- PostgreSQL 16 或 SQLite (开发)
- Redis 7+ (可选，用于缓存)

### 方式1: 本地开发

```bash
# 1. 克隆项目
cd D:\完整项目\trading-strategy-center

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -e .
pip install -e ".[ml]"  # 安装ML可选依赖

# 4. 配置环境变量
copy .env.example .env
# 编辑 .env 文件，配置数据库等

# 5. 初始化数据库
alembic upgrade head

# 6. 启动后端
python main.py
# 访问 http://localhost:8000

# 7. 启动前端 (新终端)
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

### 方式2: Docker Compose (推荐)

```bash
# 1. 配置环境变量
cp .env.example .env

# 2. 启动所有服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f backend

# 4. 停止服务
docker-compose down
```

### 验证安装

```bash
# 测试API
curl http://localhost:8000/api/v1/health

# 运行测试
pytest tests/ -v

# 预期结果: 981 passed
```

---

## 核心功能使用

### 1. 获取市场数据

```python
from core.data.market_data_manager import MarketDataManager

# 初始化
manager = MarketDataManager()

# 获取日线数据
df = await manager.get_daily(
    symbol="RB",  # 螺纹钢
    start="2024-01-01",
    end="2024-12-31"
)

# 获取分钟线数据
df_5m = await manager.get_minute(
    symbol="CU",  # 沪铜
    period="5m"
)

# 获取实时行情
quotes = await manager.get_realtime(["RB", "CU", "AU"])
```

### 2. 计算Alpha因子

```python
from core.alpha.alpha101.factor_registry import FactorRegistry
from core.alpha.alpha101.factor_pipeline import FactorPipeline

# 列出所有因子
registry = FactorRegistry()
all_factors = registry.list_all()

# 计算单个因子
alpha001 = registry.get("alpha001")
result = alpha001.compute(df, symbol="RB")

# 并行计算多个因子
pipeline = FactorPipeline(max_workers=8)
factor_names = ["alpha001", "alpha002", "alpha003"]
results = pipeline.compute_factors(df, factor_names, symbol="RB")
```

### 3. 运行策略信号

```python
from signals.registry import get_strategy

# 获取策略
strategy = get_strategy("trend_ma_cross")

# 配置参数
strategy.set_params(
    fast_period=5,
    slow_period=20
)

# 计算信号
signal = strategy.compute(df, symbol="RB")

print(f"方向: {signal.direction}")
print(f"置信度: {signal.confidence}")
print(f"评分: {signal.score}")
```

### 4. 三系统共振

```python
from core.resonance.engine import ResonanceEngine

# 初始化共振引擎
resonance = ResonanceEngine()

# 计算共振信号
result = await resonance.calculate(
    symbol="RB",
    signals=all_signals,  # 来自多个策略
    regime=current_regime  # 当前市场状态
)

print(f"观山评分: {result.score_G}")
print(f"楚风评分: {result.score_C}")
print(f"听海评分: {result.score_T}")
print(f"最终评分: {result.final_score}")
print(f"方向: {result.direction}")
```

### 5. 模拟交易

```python
from simulation.sim_engine import SimEngine

# 初始化模拟引擎
sim = SimEngine(initial_capital=1_000_000)

# 处理信号
result = await sim.process_signal(signal)

# 查看持仓
positions = sim.get_positions()

# 查看PnL
pnl = sim.get_pnl()
print(f"总权益: {pnl.total_equity}")
print(f"未实现盈亏: {pnl.unrealized_pnl}")
print(f"已实现盈亏: {pnl.realized_pnl}")
```

### 6. 回测

```python
from backtest.vectorized_engine import VectorizedBacktest

# 配置回测
backtest = VectorizedBacktest(
    strategy=strategy,
    initial_capital=1_000_000,
    commission=0.0003
)

# 运行回测
result = backtest.run(
    symbol="RB",
    start_date="2023-01-01",
    end_date="2024-12-31"
)

# 查看结果
print(f"总收益率: {result.total_return:.2%}")
print(f"年化收益率: {result.annual_return:.2%}")
print(f"夏普比率: {result.sharpe_ratio:.2f}")
print(f"最大回撤: {result.max_drawdown:.2%}")
print(f"胜率: {result.win_rate:.2%}")
```

### 7. 期权定价

```python
from options.pricing.black_scholes import BlackScholes

# 计算期权价格
bs = BlackScholes()
call_price = bs.price(
    S=3800,      # 标的价格
    K=3900,      # 行权价
    T=0.25,      # 到期时间（年）
    r=0.03,      # 无风险利率
    sigma=0.20,  # 波动率
    option_type="call"
)

# 计算Greeks
greeks = bs.greeks(S=3800, K=3900, T=0.25, r=0.03, sigma=0.20)
print(f"Delta: {greeks['delta']:.4f}")
print(f"Gamma: {greeks['gamma']:.4f}")
print(f"Vega: {greeks['vega']:.4f}")
print(f"Theta: {greeks['theta']:.4f}")
```

---

## 策略开发

### 创建自定义策略

```python
# signals/strategies/custom/my_strategy.py

from signals.base import BaseStrategy, Signal
from signals.registry import register
import pandas as pd

@register("my_custom_strategy")
class MyCustomStrategy(BaseStrategy):
    """我的自定义策略"""
    
    def __init__(self):
        super().__init__()
        self.params = {
            'period': 20,
            'threshold': 2.0
        }
    
    def compute(self, data: pd.DataFrame, symbol: str) -> Signal:
        """计算策略信号"""
        # 1. 计算指标
        ma = data['close'].rolling(self.params['period']).mean()
        std = data['close'].rolling(self.params['period']).std()
        
        # 2. 计算Z-score
        zscore = (data['close'] - ma) / std
        
        # 3. 生成信号
        if zscore.iloc[-1] < -self.params['threshold']:
            direction = "BUY"
            confidence = min(abs(zscore.iloc[-1]) / 3.0, 1.0)
        elif zscore.iloc[-1] > self.params['threshold']:
            direction = "SELL"
            confidence = min(abs(zscore.iloc[-1]) / 3.0, 1.0)
        else:
            direction = "HOLD"
            confidence = 0.0
        
        return Signal(
            strategy_name="my_custom_strategy",
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            score=zscore.iloc[-1],
            price=data['close'].iloc[-1],
            timestamp=data.index[-1],
            reason=f"Z-score={zscore.iloc[-1]:.2f}",
            source_system="custom"
        )
    
    def get_params(self) -> dict:
        return self.params
```

### 使用自定义策略

```python
from signals.registry import discover, get_strategy

# 自动发现所有策略
discover()

# 使用策略
my_strategy = get_strategy("my_custom_strategy")
signal = my_strategy.compute(df, symbol="RB")
```

---

## API参考

### REST API

#### 健康检查
```http
GET /api/v1/health
```

#### 获取日线数据
```http
GET /api/v1/data/daily/RB?start=2024-01-01&end=2024-12-31
```

#### 获取所有策略
```http
GET /api/v1/strategies
```

#### 运行回测
```http
POST /api/v1/backtest/run
Content-Type: application/json

{
  "strategy": "trend_ma_cross",
  "symbol": "RB",
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 1000000
}
```

#### 获取当前持仓
```http
GET /api/v1/trading/positions
```

### WebSocket API

```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

// 订阅品种
ws.send(JSON.stringify({
  action: 'subscribe',
  symbols: ['RB', 'CU', 'AU']
}));

// 接收消息
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('类型:', data.type);
  console.log('数据:', data.data);
};
```

---

## 常见问题

### Q1: 如何配置数据源？

**A**: 编辑 `.env` 文件，添加API密钥：

```bash
# AKShare 免费，无需配置

# Alpha Vantage
ALPHA_VANTAGE_API_KEY=your_key_here

# EIA (能源数据)
EIA_API_KEY=your_key_here

# FRED (宏观数据)
FRED_API_KEY=your_key_here
```

### Q2: 为什么测试失败？

**A**: 确保：
1. Python版本 >= 3.10
2. 所有依赖已安装：`pip install -e ".[ml]"`
3. 数据库已初始化：`alembic upgrade head`

### Q3: 如何添加新品种？

**A**: 修改 `core/data/market_data_manager.py` 中的 `_VARIETY_EXCHANGE` 字典。

### Q4: 回测速度慢怎么办？

**A**: 
1. 使用向量化回测引擎（已默认）
2. 减少策略数量
3. 使用因子缓存
4. 并行回测多个品种

### Q5: 如何部署到生产环境？

**A**: 使用Docker Compose：

```bash
# 1. 编辑生产配置
cp .env.example .env
# 设置 ENV=production

# 2. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 3. 配置nginx反向代理（见deploy/nginx.conf）
```

### Q6: 支持哪些交易所？

**A**: 
- 中国期货：SHFE, DCE, CZCE, CFFEX, INE, GFEX ✅
- 国际期货：通过yfinance（有限支持）
- 股票：A股（AKShare）、美股（yfinance）
- 期权：中国期权（50ETF, 300ETF等）

### Q7: 如何查看日志？

**A**:
```bash
# 开发环境
tail -f data/logs/app.log

# Docker环境
docker-compose logs -f backend
```

### Q8: 数据质量问题怎么处理？

**A**: 系统内置6道质量检查，自动修复常见问题：
- 缺失值：前向填充
- 重复行：保留最新
- 异常值：IQR替换
- 零成交量：使用前值

查看质量报告：
```python
from core.data.data_quality import DataQualityGuard

guard = DataQualityGuard()
report = guard.check(df, symbol="RB", period="1d")
print(report.to_dict())
```

---

## 进阶主题

### 1. 因子研究

```python
from core.alpha.management.factor_analyzer import FactorAnalyzer

analyzer = FactorAnalyzer()

# IC分析
ic_results = analyzer.calculate_ic(
    factors_df=factor_values,
    returns_df=future_returns
)

# 分层回测
layered = analyzer.layered_backtest(
    factor="alpha001",
    n_quantiles=5
)
```

### 2. 策略锦标赛

```python
from tournament.tournament_manager import TournamentManager

tournament = TournamentManager()

# 启动锦标赛
results = tournament.run_tournament(
    strategies=all_strategies,
    mode="TOURNAMENT",  # DUEL / TOURNAMENT / EXPLORATION
    num_rounds=10
)

# 查看排名
leaderboard = tournament.get_leaderboard()
```

### 3. 强化学习训练

```python
from core.rl.deep.sac_trainer import SACTrainer

trainer = SACTrainer()

# 训练
trainer.train(
    env=trading_env,
    total_timesteps=1_000_000
)

# 评估
rewards = trainer.evaluate(n_episodes=100)
```

---

## 资源链接

- **架构文档**: `ARCHITECTURE.md`
- **升级状态**: `UPGRADE_STATUS.md`
- **完成报告**: `SYSTEM_COMPLETION_REPORT.md`
- **API文档**: http://localhost:8000/docs (启动后访问)
- **测试覆盖**: `pytest tests/ --cov`

---

## 支持与反馈

- 问题反馈：创建 GitHub Issue
- 功能建议：Pull Request
- 技术支持：查看文档或联系团队

---

**祝交易愉快！** 🚀📈
