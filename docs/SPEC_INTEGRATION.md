# 增量集成规划：5个外部项目 → 交易策略中心

> 本文档定义将 `D:\完整项目\20260623` 下5个外部项目增量集成到交易策略中心的方案。

---

## 一、集成概览

| 外部项目 | 核心价值 | 集成后模块 | 优先级 |
|---------|---------|-----------|--------|
| Agent-Reach | 互联网数据获取能力 | Market Intelligence | P0 |
| NewsRader | AI新闻聚合与评分 | News Aggregator | P0 |
| UZI-Skill | 游资分析引擎 | VStock Advisor | P1 |
| Vibe-Trading | HKUDS量化研究系统 | Vibe Research | P1 |
| claude-for-financial-services-cn | A股金融研究框架 | China Finance | P2 |

---

## 二、现有系统定位

```
trading-strategy-center/
├── Market Intelligence     ← Agent-Reach 注入
├── News Aggregator         ← NewsRader 注入
├── VStock Advisor          ← UZI-Skill 注入
├── Vibe Research           ← Vibe-Trading 注入
└── China Finance           ← claude-for-financial-services-cn 注入
```

---

## 三、模块级集成方案

### 3.1 Market Intelligence（Agent-Reach）

**原项目亮点：**
- 覆盖：Twitter/X、YouTube、Reddit、小红书、B站、GitHub、雪球、V2EX、RSS、全网搜索
- MCP Server 设计，一键安装
- 自动诊断和错误恢复

**集成方案：**
```
src/intelligence/
├── platforms/              # 各平台适配器
│   ├── twitter.py          # Twitter/X 采集
│   ├── github.py           # GitHub Trending/Issues
│   ├── xueqiu.py            # 雪球舆情
│   └── rss.py              # 通用 RSS
├── mcp_server.py           # MCP 协议服务
└── aggregator.py           # 跨平台聚合引擎
```

**关键决策：**
- 复用现有 `signals/` 模块的信号格式
- MCP Server 作为独立服务运行，通过 SSE 与主系统通信
- 优先集成雪球（A股舆情）和 GitHub（代码趋势）

---

### 3.2 News Aggregator（NewsRader）

**原项目亮点：**
- 多源采集：RSS、Reddit、Hacker News、GitHub
- AI情感评分（0-10）
- 多通知渠道：邮件/飞书/钉钉/Discord/Slack

**集成方案：**
```
src/news/
├── sources/                # 新闻源适配器
│   ├── rss.py
│   ├── reddit.py
│   ├── hackernews.py
│   └── github.py
├── scorer.py               # AI情感评分
├── notifier.py             # 通知引擎
└── router.py               # 路由到各模块
```

**关键决策：**
- 评分结果存入 `news_scores` 表
- 与现有快讯模块共享通知渠道
- 情感分数作为信号输入的一部分

---

### 3.3 VStock Advisor（UZI-Skill）

**原项目亮点：**
- 66位评审团、9大流派、22维数据
- 22种机构分析方法
- DCF估值、杀猪盘排查

**集成方案：**
```
src/vstock/
├── jury.py                 # 评审团引擎
├── schools.py              # 9大流派分析
├── dimensions.py           # 22维数据
├── valuation.py            # DCF/相对估值
├── scam_detector.py        # 杀猪盘识别
└── reporter.py             # 研报复用
```

**关键决策：**
- 作为 `signals/` 模块的专业分析后端
- 输出结构化研报，供前端渲染
- 复用现有 `fundamental/` 数据源

---

### 3.4 Vibe Research（Vibe-Trading）

**原项目亮点：**
- 研究智能体 + 回测引擎 + Swarm 多智能体
- 18个数据源：AShare/Futures/Crypto/Forex
- Alpha Zoo：452个量化因子
- Shadow Account + 券商连接

**集成方案：**
```
src/vibe/
├── research_agent/         # 研究智能体
├── backtest/               # 回测引擎
├── swarm/                  # Swarm 多智能体
├── shadow_account/         # 影子账户
├── brokers/                # 券商连接（IB/富途/老虎）
└── alpha_zoo/              # 因子库
```

**关键决策：**
- 因子库作为独立模块，供所有策略调用
- 回测引擎集成到现有 `core/rl/` 流程
- 券商连接作为可插拔模块（需要用户 API Key）
- 优先集成 AShare（A股）数据源

---

### 3.5 China Finance（claude-for-financial-services-cn）

**原项目亮点：**
- 63个 Claude Skills
- 覆盖：投行、PE、财富管理、基金运营
- 数据：Wind/iFind/AkShare

**集成方案：**
```
src/china_finance/
├── skills/                 # 金融专业 Skills
│   ├── investment_banking/ # 投行相关
│   ├── pe/                 # 私募股权
│   ├── wealth/             # 财富管理
│   └── fund_ops/           # 基金运营
└── data_adapters/         # 数据适配器
    ├── wind.py
    ├── ifind.py
    └── akshare.py
```

**关键决策：**
- Skills 转换为可调用函数
- Wind/iFind 需要商业许可，优先用 AkShare
- 与 Vibe Research 共用 AShare 数据源

---

## 四、技术架构

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│  Dashboard / Signals / Backtest / Reports          │
└─────────────────────────┬───────────────────────────┘
                          │ HTTP/SSE
┌─────────────────────────▼───────────────────────────┐
│                    API Gateway                       │
│  /api/signals  /api/news  /api/vstock  /api/vibe  │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│                  Service Layer                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Signals  │ │  News     │ │ VStock   │           │
│  └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐                         │
│  │  Vibe    │ │ ChinaFi  │                         │
│  └──────────┘ └──────────┘                         │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│                   Data Layer                        │
│  PostgreSQL / Redis / SQLite / TimescaleDB         │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│               External Data Sources                   │
│  AkShare / 交易所 / 券商API / 雪球 / Twitter        │
└─────────────────────────────────────────────────────┘
```

---

## 五、实施计划

### Phase 1：基础设施（P0）
- [ ] 创建模块目录结构
- [ ] 统一数据模型（Signal, News, Report）
- [ ] 基础 API 路由框架
- [ ] 日志和错误追踪

### Phase 2：核心模块（P0）
- [ ] NewsRader → News Aggregator
- [ ] Agent-Reach → Market Intelligence
- [ ] 与现有 signals 模块打通

### Phase 3：专业模块（P1）
- [ ] UZI-Skill → VStock Advisor
- [ ] Vibe-Trading → Vibe Research（优先 AShare）
- [ ] 因子库集成到回测引擎

### Phase 4：高级模块（P2）
- [ ] claude-for-financial-services-cn → China Finance
- [ ] Swarm 多智能体框架
- [ ] Shadow Account 模拟交易

### Phase 5：前端完善（P1-P2 并行）
- [ ] 各模块前端页面
- [ ] Dashboard 集成
- [ ] 通知渠道配置 UI

---

## 六、数据流设计

```
外部项目数据 → 标准化处理 → 统一存储 → API 输出 → 前端展示
     ↓
[Agent-Reach] → 平台数据 → signals 表
[NewsRader]   → 新闻评分 → news 表
[UZI-Skill]   → 研报     → reports 表
[Vibe-Trading]→ 因子/回测 → factors/backtest 表
[ChinaFinance] → 金融数据 → fundamentals 表
```

---

## 七、风险与依赖

| 风险 | 缓解措施 |
|-----|---------|
| 数据源不稳定 | 降级策略 + 缓存层 |
| API 限流 | 请求队列 + 重试机制 |
| 商业数据许可 | AkShare 作为主要免费源 |
| 模块复杂度 | 分阶段交付，每阶段可独立运行 |

---

## 八、文件位置

所有新增模块位于：
```
D:\完整项目\trading-strategy-center\
├── api/routes/news_routes.py              # News Aggregator
├── api/routes/market_intelligence_routes.py # Market Intelligence
├── api/routes/vstock_routes.py             # VStock Advisor
├── api/routes/vibe_routes.py               # Vibe Research
├── api/routes/china_finance_routes.py      # China Finance
└── frontend/src/pages/
    ├── NewsAggregator.tsx                  # 新闻聚合页
    ├── VStockAdvisor.tsx                    # 游资分析页
    ├── VibeResearch.tsx                     # 量化研究页
    └── ChinaFinance.tsx                     # 金融研究页
```

外部项目源码存档于：
```
D:\完整项目\20260623\     # 参考，不修改原项目
```

---

## 九、集成现状 (2026-06-25)

### ✅ 已完成

| 模块 | 后端文件 | 前端文件 | 状态 |
|------|---------|---------|------|
| News Aggregator | api/routes/news_routes.py | frontend/src/pages/NewsAggregator.tsx | ✅ 框架完成 |
| Market Intelligence | api/routes/market_intelligence_routes.py | (集成到 NewsAggregator) | ✅ 框架完成 |
| VStock Advisor | api/routes/vstock_routes.py | frontend/src/pages/VStockAdvisor.tsx | ✅ 框架完成 |
| Vibe Research | api/routes/vibe_routes.py | frontend/src/pages/VibeResearch.tsx | ✅ 框架完成 |
| China Finance | api/routes/china_finance_routes.py | frontend/src/pages/ChinaFinance.tsx | ✅ 框架完成 |

### ⚠️ 待完善

| 模块 | 问题 | 优先级 | 建议 |
|------|-----|--------|------|
| NewsRader | AI情感评分是模拟，需接 LLM API | P0 | 复用现有 llm_routes.py |
| NewsRader | 缺 Reddit/Hacker News 采集 | P1 | 复用 news_routes 架构 |
| NewsRader | 缺飞书/钉钉/Webhook 通知 | P1 | 参考 NewsRader 源码 |
| Agent-Reach | 雪球需登录态 | P1 | Cookie 方案 |
| Agent-Reach | 缺 YouTube/B站/小红书 | P2 | 参考 Agent-Reach 源码 |
| Vibe-Trading | Alpha Zoo 仅50个因子(目标452) | P1 | 接入 core/alpha/alpha101 的 292 因子 |
| Vibe-Trading | 回测需接真实行情数据 | P0 | 与现有 backtest_routes 整合 |
| UZI-Skill | DCF/杀猪盘用模拟数据 | P1 | 接入 fundamental_routes |
| claude-for-financial | 63个Skills仅实现12个 | P1 | 按需扩展 |

### 🔗 关键连接点

```python
# NewsRader AI评分 → 复用 LLM
from api.routes.llm_routes import router as llm_router

# Vibe-Trading Alpha Zoo → 接入已有因子库
from core.alpha.alpha101 import FactorRegistry, FactorPipeline

# Vibe-Trading 回测 → 复用 backtest_routes
from api.routes.backtest_routes import router as backtest_router

# UZI-Skill 财务数据 → 接入 fundamental_routes
from api.routes.fundamental_routes import router as fundamental_router
```

### 📋 建议行动计划

1. **P0 紧急**：
   - Vibe-Trading 回测接入真实行情 (与 backtest_routes 整合)
   - NewsRader AI评分接入 LLM (与 llm_routes 整合)

2. **P1 重要**：
   - Vibe-Trading Alpha Zoo 接入 core/alpha/alpha101 的 292 因子
   - UZI-Skill DCF 接入 fundamental_routes 财务数据
   - NewsRader 添加 Reddit/Hacker News 源

3. **P2 可选**：
   - Agent-Reach 添加 YouTube/B站/小红书
   - NewsRader 添加飞书/钉钉通知
   - claude-for-financial 扩展更多 Skills
