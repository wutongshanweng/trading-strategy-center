# 用户需求分析与实施方案

> 基于用户访谈的完整需求分析  
> 日期: 2026-06-14

---

## 📋 核心需求总结

### 用户角色定位
- **量化交易员** - 每天登录查看信号
- **策略研究者** - 需要数据和回测工具
- **系统运维者** - 需要稳定的信号和监控

### 核心痛点
1. **实时性不足** - 需要分钟/小时级别实时数据
2. **操作复杂** - 希望自动化，减少手动操作
3. **信号延迟** - 需要实时信号推送和告警
4. **策略固定** - 希望策略能自动进化和优化
5. **监控分散** - 希望在Dashboard统一查看所有信号

---

## 🎯 需求清单（按优先级）

### P0 - 核心功能（立即需要）

#### 1. 数据中心增强 ⭐⭐⭐⭐⭐
**需求**: 
- 自定义下载历史数据（多维度）
- 实时同步按钮（快速填充缺失数据）
- 支持分钟/小时级实时数据
- 根据策略周期调整数据频率

**实施方案**:
```typescript
// 数据中心新增功能
interface DataDownloadConfig {
  symbols: string[];           // 品种列表
  dataType: 'daily' | 'minute' | 'hour' | 'tick';
  startDate: string;
  endDate: string;
  fields: string[];           // 选择字段：open/high/low/close/volume等
}

// 实时同步功能
interface RealTimeSyncConfig {
  enabled: boolean;
  interval: 'minute' | 'hour';
  autoFill: boolean;          // 自动填充缺失数据
}
```

**UI设计**:
```
数据中心页面
┌──────────────────────────────────────────┐
│ 📊 历史数据下载                           │
│                                          │
│ 品种选择: [RB] [CU] [AU] ... (多选)      │
│ 数据类型: ○日线 ○小时 ●分钟 ○Tick        │
│ 时间范围: [2024-01-01] 至 [2024-12-31]  │
│ 数据字段: ☑OHLCV ☑持仓量 ☑成交额         │
│                                          │
│ [下载数据] [批量下载]                     │
│                                          │
│ 📡 实时同步设置                           │
│                                          │
│ ☑ 启用实时同步                            │
│ 同步频率: [1分钟 ▼]                      │
│ ☑ 自动填充缺失数据                        │
│                                          │
│ [启动实时同步] 状态: 🟢运行中             │
└──────────────────────────────────────────┘
```

---

#### 2. Dashboard实时信号告警 ⭐⭐⭐⭐⭐
**需求**:
- 实盘信号实时展示
- 包含：品种、合约、价格、买卖信号、原因、置信度
- 消息告警推送

**实施方案**:
```typescript
interface RealTimeSignal {
  id: string;
  timestamp: Date;
  symbol: string;              // 品种：RB
  contract: string;            // 合约：RB2501
  price: number;               // 当前价格：3850
  signal: 'BUY' | 'SELL' | 'HOLD';
  strategy: string;            // 策略名称
  reason: string;              // 信号原因
  confidence: number;          // 置信度：0.85
  priority: 'high' | 'medium' | 'low';
}
```

**UI设计**:
```
Dashboard页面
┌──────────────────────────────────────────┐
│ 🔔 实盘信号告警 (实时)                    │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ 🔴 高优先级信号 (3个)               │  │
│ │                                    │  │
│ │ RB2501  买入  3850  置信度:92%    │  │
│ │ 策略: 双均线趋势                    │  │
│ │ 原因: 5日线上穿20日线，MACD金叉    │  │
│ │ 时间: 14:23:15  [查看详情] [忽略]  │  │
│ │                                    │  │
│ │ CU2501  卖出  67800  置信度:88%   │  │
│ │ 策略: RSI超买                      │  │
│ │ 原因: RSI(14)=78，进入超买区       │  │
│ │ 时间: 14:20:32  [查看详情] [忽略]  │  │
│ └────────────────────────────────────┘  │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ 🟡 中优先级信号 (5个)               │  │
│ │ [展开查看...]                       │  │
│ └────────────────────────────────────┘  │
│                                          │
│ 设置: [推送通知] [声音提醒] [过滤规则]   │
└──────────────────────────────────────────┘
```

---

#### 3. 策略自动进化（机器学习） ⭐⭐⭐⭐⭐
**需求**:
- 自动调整策略参数
- 自动策略组合
- 策略共振优化
- 高胜率策略自动进入实盘监控

**实施方案**:
```python
# 策略自动进化引擎
class StrategyEvolutionEngine:
    """
    策略自动进化引擎
    使用遗传算法、贝叶斯优化等方法自动优化策略
    """
    
    def __init__(self):
        self.optimizer = BayesianOptimizer()
        self.evaluator = StrategyEvaluator()
    
    def evolve_parameters(self, strategy: Strategy, data: pd.DataFrame):
        """自动优化策略参数"""
        # 定义参数搜索空间
        param_space = strategy.get_param_space()
        
        # 贝叶斯优化
        best_params = self.optimizer.optimize(
            objective=lambda p: self._evaluate_strategy(strategy, p, data),
            space=param_space,
            n_iterations=100
        )
        
        return best_params
    
    def combine_strategies(self, strategies: List[Strategy]):
        """自动策略组合"""
        # 计算策略相关性
        correlation_matrix = self._calculate_correlation(strategies)
        
        # 优化组合权重（最大化夏普比率）
        weights = self._optimize_weights(strategies, correlation_matrix)
        
        return StrategyEnsemble(strategies, weights)
    
    def resonance_optimization(self, strategies: List[Strategy]):
        """策略共振优化"""
        # 分析策略信号共振
        resonance_score = self._analyze_resonance(strategies)
        
        # 当多个策略同时发出信号时，提高置信度
        return resonance_score
    
    def auto_deploy(self, strategy: Strategy, backtest_result: BacktestResult):
        """高胜率策略自动部署到实盘"""
        if self._is_deployment_worthy(backtest_result):
            # 自动加入实盘监控
            self.deploy_to_live(strategy)
            # 发送通知
            self.notify_user(f"策略 {strategy.name} 已自动部署到实盘监控")
```

**UI设计**:
```
策略页面 - 自动进化
┌──────────────────────────────────────────┐
│ 🤖 策略自动进化                           │
│                                          │
│ 当前进化任务:                             │
│ ├─ 双均线趋势: 参数优化中... 进度 67%    │
│ ├─ RSI策略: 组合优化完成 ✓               │
│ └─ 动量策略: 排队中...                   │
│                                          │
│ 进化历史:                                 │
│ ┌────────────────────────────────────┐  │
│ │ 双均线趋势 v2.3                     │  │
│ │ 优化前: 夏普1.8 胜率62%             │  │
│ │ 优化后: 夏普2.3 胜率68% ⬆          │  │
│ │ [查看详情] [应用到实盘]             │  │
│ └────────────────────────────────────┘  │
│                                          │
│ 自动部署规则:                             │
│ - 夏普比率 > 2.0                         │
│ - 胜率 > 65%                             │
│ - 最大回撤 < 15%                         │
│ - 样本外测试通过                         │
│                                          │
│ [配置规则] [查看已部署策略]              │
└──────────────────────────────────────────┘
```

---

#### 4. 锦标赛和赛马机制 ⭐⭐⭐⭐
**需求**:
- 策略实时竞赛
- 自动晋级机制
- 优胜策略推荐

**实施方案**:
```python
class StrategyTournament:
    """策略锦标赛系统"""
    
    def __init__(self):
        self.participants = []
        self.rankings = []
    
    def run_tournament(self, strategies: List[Strategy], duration_days: int = 30):
        """运行策略锦标赛"""
        for day in range(duration_days):
            # 每个策略生成信号
            signals = [s.compute(today_data) for s in strategies]
            
            # 模拟交易
            results = self.simulate_trading(signals)
            
            # 更新排名
            self.update_rankings(results)
        
        # 自动晋级前10%策略到实盘
        winners = self.get_top_strategies(percent=0.1)
        self.auto_deploy_winners(winners)
    
    def horse_race(self, strategies: List[Strategy]):
        """赛马机制 - 动态资金分配"""
        # 根据历史表现分配资金
        for strategy in strategies:
            performance = self.get_recent_performance(strategy)
            allocation = self.calculate_allocation(performance)
            strategy.set_capital(allocation)
```

**UI设计**:
```
锦标赛页面
┌──────────────────────────────────────────┐
│ 🏆 策略锦标赛 - 第3周                     │
│                                          │
│ 排行榜 (67个策略参赛)                     │
│                                          │
│ 排名 策略名称      收益率  夏普  胜率    │
│ 🥇1  SuperTrend   +18.5%  2.8   72%    │
│ 🥈2  双均线v2.3   +16.2%  2.5   68%    │
│ 🥉3  KAMA自适应   +14.8%  2.3   65%    │
│  4  一目均衡      +12.3%  2.1   63%    │
│  5  动量突破      +11.7%  1.9   61%    │
│  ... 查看全部                            │
│                                          │
│ 🎯 自动晋级规则:                          │
│ - 前10名自动进入实盘监控                  │
│ - 后20名淘汰，触发重新优化                │
│                                          │
│ 赛马资金分配:                             │
│ - 第1名: 20%资金                         │
│ - 第2-5名: 各10%                        │
│ - 第6-10名: 各5%                        │
│                                          │
│ [查看详细战绩] [开始新赛季]              │
└──────────────────────────────────────────┘
```

---

### P1 - 重要功能

#### 5. 前端策略/因子创建 ⭐⭐⭐⭐
**需求**:
- 在Web界面直接添加策略
- 在Web界面直接添加因子
- 支持即时回测

**实施方案**:
```typescript
// 策略创建器
interface StrategyBuilder {
  name: string;
  type: 'trend' | 'mean_reversion' | 'arbitrage' | 'momentum';
  signals: SignalConfig[];
  params: Record<string, number>;
  riskManagement: RiskConfig;
}

// 因子创建器
interface FactorBuilder {
  name: string;
  formula: string;              // 支持类Python语法
  inputs: string[];             // 需要的输入数据
  lookback: number;
}
```

**UI设计**:
```
策略创建页面
┌──────────────────────────────────────────┐
│ ➕ 创建新策略                             │
│                                          │
│ 策略名称: [我的趋势策略__________]        │
│ 策略类型: [趋势跟踪 ▼]                   │
│                                          │
│ 信号配置:                                 │
│ ┌────────────────────────────────────┐  │
│ │ 入场信号:                           │  │
│ │ - MA(5) 上穿 MA(20)                │  │
│ │ - RSI(14) > 50                     │  │
│ │ [添加条件]                         │  │
│ │                                    │  │
│ │ 出场信号:                           │  │
│ │ - MA(5) 下穿 MA(20)                │  │
│ │ - 持仓时间 > 5天                    │  │
│ │ [添加条件]                         │  │
│ └────────────────────────────────────┘  │
│                                          │
│ 参数设置:                                 │
│ - 快速MA周期: [5_____] (范围: 2-10)    │
│ - 慢速MA周期: [20____] (范围: 10-50)   │
│                                          │
│ 风险管理:                                 │
│ - 止损: [2%] - 止盈: [10%]              │
│ - 最大仓位: [30%]                        │
│                                          │
│ [保存策略] [立即回测]                     │
└──────────────────────────────────────────┘
```

---

#### 6. Agent API接口 ⭐⭐⭐⭐
**需求**:
- 提供API供外部Agent使用
- Agent可以获取数据、策略、因子
- Agent可以进行模拟交易

**实施方案**:
```python
# Agent API设计
from fastapi import APIRouter, Header

agent_router = APIRouter(prefix="/api/v1/agent", tags=["agent"])

@agent_router.post("/auth")
async def agent_authenticate(api_key: str) -> dict:
    """Agent认证"""
    return {"token": "...", "expires_in": 3600}

@agent_router.get("/data/{symbol}")
async def get_market_data(
    symbol: str,
    start: str,
    end: str,
    interval: str = "1m",
    token: str = Header(...)
):
    """获取市场数据"""
    return {"data": [...]}

@agent_router.get("/strategies")
async def list_strategies(token: str = Header(...)):
    """获取策略列表"""
    return {"strategies": [...]}

@agent_router.post("/signals/compute")
async def compute_signals(
    symbol: str,
    strategy_names: List[str],
    token: str = Header(...)
):
    """计算策略信号"""
    return {"signals": [...]}

@agent_router.post("/trading/simulate")
async def simulate_trade(
    order: OrderRequest,
    token: str = Header(...)
):
    """模拟交易"""
    return {"order_id": "...", "status": "filled"}

@agent_router.get("/factors/{factor_id}")
async def get_factor_values(
    factor_id: str,
    symbol: str,
    start: str,
    end: str,
    token: str = Header(...)
):
    """获取因子值"""
    return {"factor_values": [...]}
```

**使用示例**:
```python
# 外部Agent使用系统API
import requests

class TradingAgent:
    def __init__(self, api_key: str):
        self.base_url = "http://localhost:8000/api/v1/agent"
        self.token = self._authenticate(api_key)
    
    def _authenticate(self, api_key: str):
        response = requests.post(
            f"{self.base_url}/auth",
            json={"api_key": api_key}
        )
        return response.json()["token"]
    
    def get_realtime_signals(self, symbol: str):
        """获取实时信号"""
        response = requests.post(
            f"{self.base_url}/signals/compute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "symbol": symbol,
                "strategy_names": ["trend_ma_cross", "rsi_reversal"]
            }
        )
        return response.json()["signals"]
    
    def execute_trade(self, signal):
        """基于信号执行交易"""
        # Agent可以在系统外部执行真实交易
        # 或使用系统的模拟交易功能
        pass
```

---

### P2 - 增强功能

#### 7. 消息推送系统 ⭐⭐⭐
**实施方案**:
```python
# 多渠道消息推送
class NotificationService:
    def send_signal_alert(self, signal: Signal):
        """发送信号告警"""
        message = self._format_signal_message(signal)
        
        # 多渠道推送
        self.send_email(message)
        self.send_wechat(message)
        self.send_websocket(message)  # 网页实时推送
        self.send_telegram(message)    # Telegram机器人
    
    def _format_signal_message(self, signal: Signal) -> str:
        return f"""
        🔔 交易信号告警
        
        品种: {signal.symbol}
        合约: {signal.contract}
        方向: {signal.direction}
        价格: {signal.price}
        置信度: {signal.confidence:.0%}
        
        策略: {signal.strategy}
        原因: {signal.reason}
        
        时间: {signal.timestamp}
        """
```

---

## 🏗️ 实施路线图

### 第1周：核心功能（P0）
- ✅ Day 1-2: Dashboard实时信号告警
- ✅ Day 3-4: 数据中心实时同步
- ✅ Day 5-7: 策略自动进化基础框架

### 第2周：重要功能（P1）
- Day 1-3: 前端策略/因子创建器
- Day 4-5: Agent API接口
- Day 6-7: 锦标赛系统

### 第3周：增强和优化
- Day 1-2: 消息推送系统
- Day 3-4: 性能优化
- Day 5-7: 测试和文档

---

## 🎯 预期效果

### 用户体验提升
- **每日登录时间**: 从30分钟 → **5分钟**
- **信号延迟**: 从分钟级 → **秒级**
- **策略优化**: 从手动 → **自动**
- **监控效率**: 从多页面 → **Dashboard统一**

### 系统能力提升
- 实时数据更新
- 自动策略优化
- 智能信号推送
- Agent生态支持

---

## 💡 技术亮点

1. **实时性** - WebSocket + Redis实现秒级推送
2. **智能化** - 机器学习自动优化策略
3. **自动化** - 高胜率策略自动部署
4. **开放性** - Agent API支持外部集成
5. **可靠性** - 系统内稳定，外部灵活

---

## ✅ 立即可开始的工作

我可以立即帮您实现：

1. **Dashboard实时信号组件** - 最快30分钟
2. **数据中心实时同步UI** - 1小时
3. **Agent API框架** - 2小时
4. **策略进化引擎基础** - 4小时

**需要我现在开始实施哪个功能？**
