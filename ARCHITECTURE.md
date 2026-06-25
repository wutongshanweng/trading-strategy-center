# 交易策略中心 — 架构设计文档

> 版本: v2.0  
> 项目路径: `D:\完整项目\trading-strategy-center\`  
> 目标部署: VPS Ubuntu (22.04+)  
> 开发环境: Windows 10/11

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [模块规范](#3-模块规范)
4. [数据流](#4-数据流)
5. [API 设计](#5-api-设计)
6. [数据库设计](#6-数据库设计)
7. [前端设计](#7-前端设计)
8. [部署方案](#8-部署方案)
9. [错误处理与重试策略](#9-错误处理与重试策略)
10. [安全设计](#10-安全设计)
11. [监控与可观测性](#11-监控与可观测性)
12. [CI/CD 流水线](#12-cicd-流水线)
13. [测试策略](#13-测试策略)
14. [实现路线图](#14-实现路线图)
15. [关键整合决策](#15-关键整合决策)
16. [原始代码 Bug 注册表](#16-原始代码-bug-注册表)
17. [升级迁移路径](#17-升级迁移路径)

---

## 1. 项目概述

### 1.1 项目目标

构建一个 **交易策略中心**（Trading Strategy Center），将三个独立 Agent 系统（观山/楚风/听海）生成的策略资产 **全量整合** 到统一平台中，覆盖：

- **数据获取**：market_data_fetcher 覆盖 16 类数据源，统一 `MarketDataManager` 入口
- **策略共振**：三套独立共振系统各自计算 Score → 统一加权 → 最终信号
- **模拟交易**：纯模拟环境，以楚风 sim_trader_v3 为骨架，ATR 止损/金字塔加仓/多级路由
- **回测验证**：向量化回测（观山主力）+ 阈值优化回测（听海备用）
- **投资组合**：马科维茨/HRP/CVaR 优化
- **ML 增强**：重训 XGBoost/HMM/LSTM + Stacking 集成 + PPO RL
- **策略锦标赛**：Duel/Tournament/Exploration 三模式进化淘汰（听海）
- **市场微观结构**：KLS Lambda + Ising 羊群效应 + Hawkes 自激过程（听海）
- **缠论分析**：3 层笔-线段-中枢框架（听海+观山）
- **14 经典量化模型**：GBM/HMM/马科维茨/协整套利/GARCH/泊松跳跃等（楚风）
- **自动进化**：PerformanceTracker + ABTest + EvolutionScheduler
- **可视化**：React + Ant Design + lightweight-charts

### 1.2 约束

- **不接入 CTP 实盘交易** — 仅模拟
- **仅支持国内期货**（未来可扩展至股票/加密货币）
- **部署在 VPS Ubuntu 22.04**，开发环境为 Windows
- **异步任务**：长耗时操作（回测/模型训练）走 Celery + Redis，不走 HTTP 同步
- **所有代码资产全量合并**：不选最优，全量整合

### 1.3 三大 Agent 资产总表

| Agent | 代码库 | 源文件数 | 代码行数(估) | 核心贡献 |
|-------|--------|---------|-------------|---------|
| 观山 | `agent\guanshan\modules\` | ~80 | ~15,000 | 插件框架/进化引擎/组合优化/高级分析/AI 信号 |
| 楚风 | `agent\chufeng\core\` + `config\` + `strategies\` | ~89 | ~35,000 | sim_trader_v3/三层共振/Regime/14 量化模型/技术指标库 |
| 听海 | `agent\tinghai\quant_system\` + `bin\` | ~68 | ~80,000 | 33 策略/ML 管线/缠论/微观结构/锦标赛/规则引擎 |

### 1.4 可复用基础设施

从 `qzh-trading-main` 可直接复用：

| 模块 | 源文件 | 行数 | 复用方式 |
|------|--------|------|----------|
| DataSourceManager | `services/data_source_manager.py` | 386 | 封装为 MarketDataManager 核心 |
| WebSocketManager | `services/websocket_manager.py` | 125 | 直接复用，增强广播 |
| HistoryStore | `services/history_store.py` | ~300 | 直接复用，增加数据质量检查 |
| MarketDataService | `services/market_data.py` | ~200 | 增强为 Tick→K 线实时聚合 |
| Config (pydantic) | `core/config.py` | ~80 | 改造为 ConfigManager |
| CONTRACT_META | `main.py` | ~100 | 移入 `config/contracts.yaml` |
| useWebSocket hook | `hooks/useWebSocket.ts` | 130 | 直接复用 |
| 前端组件 | `components/` | ~3000 | 重构为新页面结构 |

### 1.5 原始代码 Bug 注册表

完整 Bug 清单（24 个，含修复方案和优先级）见 [第 16 章](#16-原始代码-bug-注册表)。

---

## 2. 系统架构

### 2.1 七层架构（含异步任务层）

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Layer 7: Frontend (React + Ant Design + lightweight-charts)             │
│  Dashboard / Strategy / Trading / Backtest / Portfolio / ML / Settings   │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 6: API Gateway (FastAPI + WebSocket + Auth + RateLimit)           │
│  REST routes / WS push / JWT / RBAC / OpenAPI / rate limiting            │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 5: Core Engine (同步)                                              │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐ ┌────────────┐           │
│  │ Simulation │ │ Risk Mgr   │ │ Portfolio    │ │ Evolution  │           │
│  │ sim_engine │ │ + breaker  │ │ optimizer    │ │ engine     │           │
│  └────────────┘ └────────────┘ └──────────────┘ └────────────┘           │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │  Strategy Engine ———— Resonance Engine ———— Rule Engine             │    │
│  │  33+13+7 策略 → Voter/Matrix/Scanner 共振 → 加权合并 → 规则过滤      │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │  市场微观结构 / 缠论 / 策略锦标赛 / 新闻情绪 / 基本面                  │    │
│  └───────────────────────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 4: Async Task Layer (Celery + Redis)                               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────────┐           │
│  │ Backtest Worker  │ │ Training Worker │ │ Report Worker     │           │
│  │ (向量化回测)      │ │ (XGBoost/HMM/   │ │ (日报/导出/报告)  │           │
│  │                  │ │  LSTM/Ensemble) │ │                   │           │
│  └─────────────────┘ └─────────────────┘ └───────────────────┘           │
│  Task State: PENDING → STARTED → PROGRESS → SUCCESS/FAILURE               │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 3: Analysis & ML                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐        │
│  │ XGBoost  │ │ HMM      │ │ LSTM     │ │ Stacking │ │ PPO/SAC/TD3│        │
│  │ 方向预测  │ │ 状态识别  │ │ 短期预测  │ │ 集成学习  │ │ PyTorch+GPU │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └─────────┘        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ 14 量化  │ │ GARCH    │ │ ARIMA    │ │ Alpha101 │                    │
│  │ 经典模型  │ │ 波动率    │ │ 价格预测  │ │ 因子      │                    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                    │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 2: Market State + Cross-Symbol                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐                  │
│  │ Regime: HMM  │ │ Entropy      │ │ State Machine   │                  │
│  │ + 多因子     │ │ (观山补充)    │ │ (TREND_UP/DOWN/  │                  │
│  │ (楚风主力)    │ │              │ │  RANGE/HIGH_VOL) │                  │
│  └──────────────┘ └──────────────┘ └──────────────────┘                  │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │  Cross-Symbol: 板块轮动 / 资金流向 / 跨品种共振 / 相关性分析          │    │
│  └───────────────────────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────────────────┤
│  Layer 1: Data (market_data_fetcher → MarketDataManager)                  │
│  AKShare / yfinance / TDX / FRED / EIA / CFTC / AlphaVantage / Tiingo    │
│  FMP / ChinaOptions / USOptions / 生意社 / 东方财富 / 新浪               │
│  16 类数据源 → 统一 MarketDataManager → 2 级缓存 (LRU + Redis)           │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.1b 异步任务层设计

```
core/tasks/
├── celery_app.py              # Celery 实例，broker=redis://redis:6379/1
├── config.py                  # 路由/队列/重试策略/rate limit
├── base.py                    # BaseTask: 进度上报/心跳/失败处理
├── backtest_tasks.py          # 向量化回测任务（1800s 超时）
├── training_tasks.py          # 模型重训任务（XGBoost/HMM/LSTM/Ensemble）
├── report_tasks.py            # 日报/报告导出
├── signals_tasks.py           # 批量信号计算
└── scheduled_tasks.py         # APScheduler 定时任务（日收盘/周优化）
```

**任务队列映射：**
| 队列 | 用途 | 并发 | 超时 | Rate Limit |
|------|------|------|------|------------|
| `backtest` | 回测任务 | 2 worker | 1800s | 2/m |
| `training` | 模型训练 | 1 worker | 3600s | 1/m |
| `reports` | 报告导出 | 1 worker | 300s | 5/m |

**n8n 替代方案（可选）：**
对于不想引入 Celery 的场景，可以用 n8n 编排异步工作流：
- n8n Webhook → 触发回测 → 轮询结果 → 推送到前端
- 优点：可视化编排，免代码维护
- 缺点：额外的 Docker 服务，调试不便

### 2.2 目录结构

```
D:\完整项目\trading-strategy-center\
│
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── data_routes.py          # 数据查询
│   │   │   ├── strategy_routes.py      # 策略配置/信号
│   │   │   ├── trading_routes.py       # 模拟交易/持仓
│   │   │   ├── backtest_routes.py      # 回测触发/结果
│   │   │   ├── portfolio_routes.py     # 组合优化
│   │   │   ├── analysis_routes.py      # 高级分析
│   │   │   ├── ml_routes.py            # ML 模型管理
│   │   │   ├── tournament_routes.py    # 策略锦标赛
│   │   │   └── health_routes.py        # 健康检查
│   │   ├── ws/
│   │   │   └── handlers.py             # WebSocket
│   │   └── middleware/
│   │       ├── auth.py                 # JWT 认证
│   │       ├── error_handler.py        # 全局异常处理
│   │       ├── rate_limit.py           # 限流
│   │       └── logging.py              # 请求日志
│   │
│   ├── core/
│   │   ├── data/
│   │   │   ├── market_data_manager.py  # 统一数据入口
│   │   │   ├── history_store.py        # 历史数据存储
│   │   │   ├── cache_manager.py        # 二级缓存 (LRU+Redis)
│   │   │   ├── data_quality.py         # 数据质量护栏
│   │   │   ├── data_adapters.py        # CSV/JSON/HTTP/WS 适配器
│   │   │   ├── contract_resolver.py    # 合约解析器
│   │   │   └── data_freshness.py       # 数据新鲜度检查
│   │   │
│   │   ├── knowledge/
│   │   │   ├── futures_knowledge.py    # 品种百科全书
│   │   │   └── contract_meta.py        # 合约元数据
│   │   │
│   │   ├── signals/
│   │   │   ├── base.py                 # BaseStrategy ABC + Signal
│   │   │   ├── registry.py             # @register 装饰器 + 自动发现
│   │   │   ├── indicators.py           # 统一技术指标库
│   │   │   ├── price_action.py         # K线形态识别
│   │   │   ├── strategies/
│   │   │   │   ├── trend/              # EMA, ADX, SuperTrend, DMI, Turtle...
│   │   │   │   ├── oscillation/        # RSI, Bollinger, MACD Div, KDJ, CCI...
│   │   │   │   ├── momentum/           # Momentum, OBV, Volume, TS_Corr...
│   │   │   │   ├── classic/            # Turtle, MeanRev, Fibonacci, Grid...
│   │   │   │   ├── ml/                 # MLFactor, XGBoost, LSTM...
│   │   │   │   ├── pairs/              # PairsTrading
│   │   │   │   ├── alpha101/           # 101 Alpha 因子
│   │   │   │   └── chan/               # 缠论策略
│   │   │   ├── engine.py               # 策略引擎入口
│   │   │   ├── quick_scan.py           # TT7×Voter×Macro 快速扫描
│   │   │   ├── enhanced_signals.py     # 盘中信号整合
│   │   │   ├── layering/
│   │   │   │   ├── layer1_trend.py     # 趋势过滤层
│   │   │   │   ├── layer2_revert.py    # 均值回复过滤层
│   │   │   │   └── layer3_event.py     # 事件驱动过滤层
│   │   │   ├── intraday/
│   │   │   │   ├── tt7_scanner.py      # 观山 TT7 扫描
│   │   │   │   └── intraday_engine.py  # 日内策略引擎
│   │   │   └── signal_types.py         # Signal dataclass 定义
│   │   │
│   │   ├── cross_symbol/
│   │   │   ├── cross_symbol_engine.py  # 多品种联合分析
│   │   │   ├── correlation_analyzer.py # 相关性分析
│   │   │   └── sector_rotation.py      # 板块轮动检测
│   │   │
│   │   ├── resonance/
│   │   │   ├── engine.py               # 统一共振引擎入口
│   │   │   ├── voter.py                # 观山加权投票
│   │   │   ├── matrix.py               # 楚风相关矩阵
│   │   │   ├── scanner.py              # 听海阈值扫描
│   │   │   └── weight_learner.py       # 动态权重学习
│   │   │
│   │   ├── market_state/
│   │   │   ├── regime_detector.py      # HMM+多因子（主力）
│   │   │   ├── entropy_analyzer.py     # 信息熵（辅助）
│   │   │   ├── state_machine.py        # 4 状态机
│   │   │   └── market_regime.py        # 状态枚举
│   │   │
│   │   ├── simulation/
│   │   │   ├── sim_engine.py           # 模拟交易引擎
│   │   │   ├── position_manager.py     # 持仓管理
│   │   │   ├── position_state.py       # 网格/配对/套利状态机
│   │   │   ├── order_book.py           # 订单簿
│   │   │   ├── pnl_calculator.py       # PnL 计算
│   │   │   ├── signal_adapter.py       # 信号适配
│   │   │   ├── scoring.py              # 信号评分
│   │   │   └── rule_engine.py          # 信号→交易规则引擎
│   │   │
│   │   ├── risk/
│   │   │   ├── atr_stop.py             # ATR 动态止损
│   │   │   ├── cvar_garch.py           # CVaR+GARCH
│   │   │   ├── circuit_breaker.py      # 断路器
│   │   │   ├── position_sizing.py      # 仓位计算
│   │   │   └── risk_config.py          # 风险参数
│   │   │
│   │   ├── portfolio/
│   │   │   ├── markowitz.py            # 马科维茨
│   │   │   ├── hrp.py                  # 层次风险平价
│   │   │   ├── cvar_optimizer.py       # CVaR 优化
│   │   │   └── efficient_frontier.py   # 有效前沿
│   │   │
│   │   ├── timeframe/
│   │   │   ├── timeframe_manager.py    # 多周期聚合
│   │   │   └── multitimeframe.py       # 多周期共振
│   │   │
│   │   ├── backtest/
│   │   │   ├── vectorized_engine.py    # 向量化回测（主力）
│   │   │   ├── threshold_optimizer.py  # 阈值优化（备用）
│   │   │   ├── walkforward.py          # Walk-forward 验证
│   │   │   ├── metrics.py              # 回测指标
│   │   │   └── backtest_final.py       # 最终对比回测
│   │   │
│   │   ├── ml/
│   │   │   ├── trainer.py              # ML 训练器
│   │   │   ├── ensemble.py             # Stacking 集成
│   │   │   ├── ml_quant_lgb.py         # LightGBM
│   │   │   ├── ml_quant_ensemble.py    # LGBM+LR+SVM
│   │   │   ├── alpha_layer.py          # ARIMA/GARCH
│   │   │   ├── ppo_agent.py            # PPO RL (PyTorch + NumPy 双后端)
│   │   │   ├── hmm_state.py            # HMM 状态识别
│   │   │   ├── lstm_predictor.py       # LSTM 预测
│   │   │   ├── meta_model.py           # 元模型 Stacking
│   │   │   ├── garch_predictor.py      # GARCH 预测
│   │   │   ├── retrain_pipeline.py     # 重训管道
│   │   │   └── model_registry.py       # 模型版本管理
│   │   │
│   │   ├── evolution/
│   │   │   ├── tracker.py              # PerformanceTracker
│   │   │   ├── ab_tester.py            # ABTest (t-test)
│   │   │   └── scheduler.py            # EvolutionScheduler
│   │   │
│   │   ├── tournament/
│   │   │   ├── agent_tournament.py     # 策略锦标赛系统
│   │   │   ├── duel_manager.py         # 决斗系统
│   │   │   └── strategy_evaluator.py   # 策略评估器
│   │   │
│   │   ├── microstructure/
│   │   │   ├── kls_lambda.py           # 价格冲击系数
│   │   │   ├── ising_herd.py           # 伊辛羊群模型
│   │   │   ├── hawkes_process.py       # Hawkes 自激过程
│   │   │   └── analyzer.py             # 综合分析器
│   │   │
│   │   ├── quant_models/
│   │   │   ├── gbm_model.py            # 几何布朗运动
│   │   │   ├── hmm_model.py            # HMM 模型
│   │   │   ├── markowitz_optimizer.py  # 马科维茨
│   │   │   ├── cointegration_arb.py    # 协整套利
│   │   │   ├── garch_model.py          # GARCH
│   │   │   ├── poisson_model.py        # 泊松跳跃
│   │   │   ├── liquidity_density.py    # 流动性密度
│   │   │   ├── sqrt_impact.py          # 平方根冲击
│   │   │   ├── kls_lambda.py           # KLS Lambda
│   │   │   ├── algem_chriss.py         # Almgren-Chriss
│   │   │   ├── hawkes_process.py       # Hawkes
│   │   │   ├── ising_herd.py           # Ising
│   │   │   └── chan_theory.py          # 缠论
│   │   │
│   │   ├── analysis/
│   │   │   ├── chan_theory.py          # 缠论（笔/线段/中枢）
│   │   │   ├── chan_integration.py     # 缠论 DB 桥接
│   │   │   ├── fourier_analyzer.py     # 傅里叶周期
│   │   │   ├── bayesian_inference.py   # 贝叶斯推断
│   │   │   ├── factor_eval.py          # 因子评价
│   │   │   ├── oifactors.py            # OI 因子
│   │   │   ├── monte_carlo.py          # 蒙特卡洛
│   │   │   ├── seasonality.py          # 季节效应
│   │   │   ├── divergence_detector.py  # 背离检测
│   │   │   └── market_microstructure.py # 微观结构分析
│   │   │
│   │   ├── notification/
│   │   │   ├── sentinel.py             # 哨兵告警引擎
│   │   │   ├── sentinel_v2.py          # 增强版
│   │   │   ├── feishu_push.py          # 飞书推送
│   │   │   ├── alert_rules.py          # 告警规则
│   │   │   ├── unified_alert.py        # 统一告警
│   │   │   └── alert_manager.py        # 多渠道管理
│   │   │
│   │   ├── news/
│   │   │   ├── news_sentiment.py       # 新闻情绪 v3
│   │   │   └── news_sentiment_v2.py    # 新闻情绪 v2
│   │   │
│   │   ├── fundamental/
│   │   │   └── fundamental_engine.py   # 基本面引擎
│   │   │
│   │   ├── db/
│   │   │   ├── db_manager.py           # 统一 DB 管理器
│   │   │   └── models.py               # SQLAlchemy 模型
│   │   │
│   │   ├── config/
│   │   │   ├── manager.py              # 配置管理器（热重载）
│   │   │   └── model_manager.py        # 模型 fallback 链
│   │   │
│   │   ├── monitoring/
│   │   │   ├── prometheus.py           # Prometheus 指标
│   │   │   ├── performance.py          # 性能监控
│   │   │   └── health_check.py         # 系统健康检查
│   │   │
│   │   ├── tasks/                      # Celery 异步任务
│   │   └── utils/
│   │       ├── hte_utils.py            # 通用工具
│   │       └── decorators.py           # 通用装饰器
│   │
│   ├── config/
│   │   ├── settings.py                 # 全局配置 (pydantic-settings)
│   │   ├── strategy_params.yaml        # 策略参数模板
│   │   ├── contracts.yaml              # 品种配置表
│   │   └── model_config.yaml           # LLM/model 配置
│   │
│   ├── db/
│   │   ├── models.py                   # ORM 模型
│   │   ├── session.py                  # 会话管理
│   │   └── migrations/                 # Alembic
│   │
│   └── main.py                         # FastAPI 入口
│
├── models/                             # ML 模型目录
│   ├── xgboost/
│   ├── hmm/
│   ├── lstm/
│   └── ensemble/
│
├── scripts/
│   ├── setup_ubuntu.sh                 # VPS 初始化
│   ├── backup_db.sh
│   ├── restore_db.sh
│   ├── migrate.sh
│   ├── health_check.sh
│   └── daily_close.py                  # 收盘后处理
│
├── data/
│   ├── futures.db                      # SQLite（开发）
│   ├── backtest_results/
│   ├── cache/
│   └── logs/
│
├── frontend/
│   ├── src/
│   │   ├── api/                        # API 调用封装
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   ├── Dashboard/
│   │   │   ├── DataCenter/
│   │   │   ├── Strategy/
│   │   │   ├── Trading/
│   │   │   ├── Backtest/
│   │   │   ├── Portfolio/
│   │   │   ├── ML/
│   │   │   └── Common/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── stores/                      # Zustand
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
│
├── deploy/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── docker-compose.yml
│   ├── nginx.conf
│   └── setup.sh
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── pyproject.toml
├── requirements.txt
├── Makefile
├── .env.example
└── ARCHITECTURE.md
```

---

## 3. 模块规范

### 3.1 数据层 (`core/data/`)

#### `MarketDataManager` — 统一数据入口

封装 `market_data_fetcher` 的 `data_source_manager.py`，增加两级缓存（内存 LRU + Redis）、熔断降级、请求去重。

```
MarketDataManager
├── get_daily(symbol, start, end)               # 日线
├── get_minute(symbol, period)                  # 分钟线
├── get_realtime_quotes(symbols)                # 实时行情
├── get_main_contracts()                        # 主力合约
├── get_index_constituents(index)               # 指数成分
├── get_macro_data(type)                        # 宏观数据
├── get_fundamentals(symbol)                    # 基本面
├── get_options_chain(symbol)                   # 期权链
├── get_cot_report(symbol)                      # COT 持仓报告
├── get_inventories(type)                       # 库存数据
├── list_sources()                              # 可用数据源状态
└── get_source_info(name)                       # 数据源详情
```

**覆盖的 16 类数据源：**

| # | 数据源 | 类名 | 覆盖范围 | API Key |
|---|--------|------|----------|---------|
| 1 | AKShare (新浪/东财) | AKShareFetcher | 国内期货日/分钟线、A股、ETF、现货 | 无 |
| 2 | yfinance | YFinanceFetcher | 国际期货 (CL=F, GC=F, ES=F)、美股、外汇 | 无 |
| 3 | 通达信 MAC | TDXFetcher | A股实时行情、K线、资金流向、板块、港股/美股/期货 | 无 |
| 4 | FRED | FREDFetcher | GDP、CPI、失业率、利率、国债收益率 | 需要 |
| 5 | EIA | EIAFetcher | 原油/汽油/天然气库存 | 需要 |
| 6 | CFTC | CFTCFetcher | COT 持仓报告 | 无 |
| 7 | Alpha Vantage | AlphaVantageFetcher | 全球股票、外汇、技术指标 | 需要 |
| 8 | FMP | FMPFetcher | 公司基本面、财报、比率 | 需要 |
| 9 | Tiingo | TiingoFetcher | 美股调整后数据、外汇、加密货币 | 需要 |
| 10 | 国内期权 | ChinaOptionsFetcher | ETF/股指/商品期权、QVIX | 无 |
| 11 | 美股期权 | USOptionsFetcher | 美股期权链、Greeks、PCR | 无 |
| 12 | 统一入口 | OptionsFetcher | 国内+美股期权合并 | 无 |
| 13 | 统一路由 | UnifiedFetcher | AKShare↔yfinance 自动路由 | 无 |
| 14 | 生意社 | AKShare (spot_price) | 商品现货价格 | 无 |
| 15 | 东方财富 | AKShare (futures_daily_em) | 具体合约日线 | 无 |
| 16 | CTP (stub) | CTPFetcher | Tick→K线聚合工具（无实盘连接） | 需要 |

**缓存策略：**
```python
class CacheManager:
    """两级缓存：LRU (内存) + Redis (分布式)"""
    
    def __init__(self, redis_url: str = None):
        self.memory_cache = LRUCache(maxsize=1000, ttl=300)  # 5 分钟
        self.redis = Redis.from_url(redis_url) if redis_url else None
    
    async def get(self, key: str) -> pd.DataFrame:
        # 1. 查内存
        if (df := self.memory_cache.get(key)) is not None:
            return df
        # 2. 查 Redis
        if self.redis and (data := await self.redis.get(key)):
            df = pd.read_json(data)
            self.memory_cache.set(key, df)
            return df
        return None
    
    async def set(self, key: str, df: pd.DataFrame, ttl: int = 3600):
        self.memory_cache.set(key, df)
        if self.redis:
            await self.redis.setex(key, ttl, df.to_json())
```

#### `DataQualityGuard` — 数据质量护栏

每条数据入库前必经 6 道检查，质量分 < 0.5 的数据自动标记不可用。

| 检查项 | 方法 | 自动修复 |
|--------|------|----------|
| Schema 验证 | validate_schema | 拒绝入库 |
| 价格范围 | check_price_range | 取前后均值 |
| 连续性 | check_no_gaps | 线性插值（<3天）/ 备用源补拉 |
| 去重 | check_no_duplicates | 保留最新 |
| 异常值 | detect_outliers_iqr | IQR 替换 |
| 成交量 | check_volume_reasonable | 查备用源 |

#### `HistoryStore` — 历史数据存储

复用 qzh-trading-main，增强数据质量集成：
- Save → 质量检查 → upsert → 记录质量评分
- Query → 按质量分过滤（`final_score > 0.5`）
- Auto-repair: 缺失检测 → 自动补拉 → 插值修复 → 去重

### 3.2 策略层 (`core/signals/`)

#### 统一策略注册框架 (观山 `@register` 装饰器)

```python
# registry.py
_strategies: Dict[str, Type[BaseStrategy]] = {}

def register(name: str = None):
    def decorator(cls):
        key = name or cls.__name__
        _strategies[key] = cls
        cls.registered_name = key
        return cls
    return decorator

def discover(package: str = "core.signals.strategies"):
    """自动发现所有带 @register 装饰器的策略"""
    for importer, modname, ispkg in pkgutil.walk_packages(
            importlib.import_module(package).__path__, 
            prefix=f"{package}."):
        importlib.import_module(modname)
    return dict(_strategies)

def get_strategy(name: str) -> Type[BaseStrategy]:
    if name not in _strategies:
        raise KeyError(f"策略 {name} 未注册")
    return _strategies[name]
```

#### `BaseStrategy` ABC

```python
class BaseStrategy(ABC):
    strategy_name: str
    params: Dict
    symbol: str
    
    @abstractmethod
    def compute(self, data: pd.DataFrame, symbol: str) -> Signal:
        """计算信号，返回统一 Signal"""
        pass
    
    @abstractmethod
    def get_params(self) -> Dict:
        pass
    
    def set_params(self, **params):
        self.params.update(params)
```

#### 统一 Signal dataclass

```python
@dataclass
class Signal:
    strategy_name: str           # 策略名
    symbol: str                  # 品种
    direction: Literal["BUY", "SELL", "HOLD"]
    confidence: float            # 0.0 ~ 1.0
    score: float                 # -10 ~ +10（共振加权用）
    price: float
    timestamp: datetime
    reason: str
    source_system: str           # "guanshan" / "chufeng" / "tinghai"
    resonance_layer: str = ""    # 共振层信息
    metadata: dict = None        # 扩展字段
```

#### 完整策略清单

整合三个 Agent 的所有策略，去重后约 **46 个独立策略**：

**趋势类 (12)**：
`EMA_Cross`, `Breakout_20`, `SuperTrend`, `DMI`, `ADX_Trend`, `Turtle`, `Swing`, `TRIX`, `DualThrust`, `MultiMA_Resonance`, `MACD_ADX`, `Price_Action`

**反转/震荡类 (9)**：
`RSI_Signals`, `RSI_Divergence`, `Bollinger_Bounce`, `MeanReversion`, `Fibonacci`, `CCI`, `CandlestickPattern`, `Williams_R`, `KDJ`

**突破类 (3)**：
`VolatilityBreakout`, `MACD_Div`, `Scalping`

**动量类 (8)**：
`Momentum_Rank`, `OBV`, `CurveMomentum`, `Volume_Confirm`, `TS_Corr`, `TS_Rank`, `TS_ArgMax`, `TS_ArgMin`, `PriceAccel`

**过滤类 (2)**：
`Entropy`, `FourierCycle`

**ML 类 (4)**：
`MLFactor`, `XGBoost_Pred`, `LSTM_Pred`, `HMM_State`

**缠论类 (under `chan/`)** (6):
`Chan_Type1_Buy/Sell`, `Chan_Type2_Buy/Sell`, `Chan_Type3_Buy/Sell`, `Chan_Bullish/Bearish_Div`

**网格/套利/配对 (3)**：
`Grid`, `PairsTrading`, `Arbitrage`

**观山特有 (3)**：
`TT7_Scanner`, `OI_Factor`, `Enhanced_MultiFactor`

**Alpha 101 (101)**：因子库，组合使用

### 3.3 共振引擎 (`core/resonance/`)

```
                    ┌──────────────────┐
                    │  Market State    │
                    │  (regime/entropy) │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  ResonanceEngine │
                    │  (统一入口)       │
                    └────────┬─────────┘
                             │
   ┌─────────────────┬───────┴───────┬─────────────────┐
   │                 │               │                 │
   ▼                 ▼               ▼                 ▼
 ┌──────┐       ┌────────┐      ┌─────────┐      ┌──────────┐
 │Voter │       │ Matrix │      │ Scanner │      │Weight    │
 │(观山) │       │(楚风)  │      │(听海)   │      │Learner   │
 │加权  │       │相关矩阵│      │阈值扫描 │      │动态权重  │
 │投票+ │       │+分层   │      │+灵敏度  │      │(回测反馈)│
 │ADX   │       │过滤    │      │调优    │      │          │
 └──┬───┘       └───┬────┘      └────┬────┘      └────┬─────┘
    │               │               │                 │
    │          Score_G          Score_C          Score_T │
    │               │               │                 │
    └───────────────┴───────────────┴─────────────────┘
                    │
                    ▼
          ┌──────────────────┐
          │ 加权求和         │
          │ Score_final =    │
          │ w_G×S_G + w_C×S_C│
          │ + w_T×S_T        │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ 最终信号判定     │
          │ + 规则引擎过滤   │
          │ + 置信度/方向    │
          └──────────────────┘
```

**初始权重**: `w_G = w_C = w_T = 1/3`
**动态调整**: 每周根据回测胜率更新（WeightLearner）
**状态感知**: 不同市场状态下权重可不同（如趋势市增加观山权重）

### 3.4 市场状态 (`core/market_state/`)

```python
class MarketRegime(Enum):
    TREND_UP = "trend_up"        # 上升趋势
    TREND_DOWN = "trend_down"    # 下降趋势
    RANGE_BOUND = "range_bound"  # 区间震荡
    HIGH_VOL = "high_volatility" # 高波动
```

| 子模块 | 来源 | 类型 | 角色 |
|--------|------|------|------|
| `regime_detector.py` | 楚风 v2 | HMM + 多因子 + 波动率聚类 | **主力**：4 状态 HMM，软切换，持续时间惩罚 |
| `entropy_analyzer.py` | 观山 | 信息熵分析 | **辅助验证** |
| `state_machine.py` | 楚风 | 4 状态机 + 滞后阈值 | 防频繁切换 |

### 3.5 模拟交易 (`core/simulation/`)

以楚风 `sim_trader_v3.py` 为核心骨架，融合听海 PositionState：

```
SimEngine
├── process_signal(signal) → OrderResult
│   ├── 规则引擎过滤 (rule_engine.py)
│   ├── 信号有效性评分 (scoring.py)
│   ├── 风险评估 (ATR止损/最大回撤/断路器)
│   ├── 仓位计算 (凯利/百分比/CVaR)
│   └── 路由决策 (ALERT/执行/拒绝)
├── update_positions(market_data)     # 持仓状态更新
├── close_position(id, reason)
├── get_positions() → List[Position]
├── get_pnl() → PnLSummary
└── get_history() → List[TradeRecord]
```

Position 结构：
```
Position: id / symbol / direction(LONG/SHORT) / entry_price / quantity
          stop_loss / take_profit / unrealized_pnl / realized_pnl
          strategy / status(open/closed) / entry_time / exit_time / exit_reason
```

**规则引擎** (听海 `rule_engine.py` 31KB — 零 LLM 依赖)：
```
RuleEngine
├── filter_signals(signals) → filtered     # 规则过滤
├── check_entry_conditions(signal) → bool  # 入场条件
├── check_exit_conditions(position) → bool # 出场条件
└── Config: 品种级阈值配置
```

### 3.6 风险管理 (`core/risk/`)

```
RiskManager
├── check_position(symbol, signal, position) → RiskVerdict
│   ├── ATR 止损检查（动态倍数）
│   ├── 总敞口检查（多品种汇总）
│   ├── 最大回撤检查
│   ├── 相关性检查（避免同向集中）
│   └── VaR/CVaR 检查（听海 var_risk.py）
├── calculate_position_size(symbol, price, confidence) → float
│   ├── 凯利公式
│   ├── 百分比资金模型
│   └── CVaR 约束
├── get_stop_levels(symbol, entry_price, direction) → (SL, TP)
│   └── ATR 倍数计算（按品种参数调整）
└── get_risk_summary() → RiskSummary
```

**VaR/CVaR (听海 var_risk.py 21KB)**：
```
VaRController
├── historical_var(data, alpha=0.05) → float
├── parametric_var(returns, alpha=0.05) → float
├── historical_cvar(data, alpha=0.05) → float
└── risk_level: SAFE / CAUTION / DANGER / CRITICAL
```

### 3.7 投资组合 (`core/portfolio/`)

```
PortfolioOptimizer
├── markowitz_optimize(returns, cov) → weights
├── hrp_optimize(returns) → weights
├── cvar_optimize(returns, alpha=0.05) → weights
├── efficient_frontier(returns, num_points=100) → frontier
└── sharpe_ratio(returns, weights) → float
```

### 3.8 回测 (`core/backtest/`)

| 引擎 | 来源 | 角色 | 特点 |
|------|------|------|------|
| `vectorized_engine.py` | 观山 | **主力** | 向量化信号计算、持仓序列模拟、多参数扫描 |
| `threshold_optimizer.py` | 听海 | **备用** | 阈值调优、v2/v3 对比、walkforward |
| `walkforward.py` | 观山 | **验证** | Walk-forward 跨期验证 |
| `metrics.py` | 统一 | **指标** | 胜率/盈亏比/最大回撤/夏普/卡玛 |

```python
@dataclass
class BacktestResult:
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_loss_ratio: float
    total_trades: int
    equity_curve: List[float]
    trade_records: List[TradeRecord]
```

### 3.9 ML 管线 (`core/ml/`)

| 模块 | 来源 | 功能 |
|------|------|------|
| `trainer.py` | 楚风 | 30+ 特征 LightGBM 训练器 + 超参调优 |
| `ensemble.py` | 楚风 | Stacking: XGBoost+LightGBM+RF → 元学习器 |
| `ml_quant_lgb.py` | 楚风 | 10 因子 5 日方向预测 |
| `ml_quant_ensemble.py` | 楚风 | LGBM+LR+SVM 三模型加权投票 |
| `alpha_layer.py` | 楚风 | ARIMA/SARIMAX + GARCH/EGARCH/TGARCH |
| `ppo_agent.py` | 楚风 | PPO (PyTorch 自动微分 + GPU / NumPy 纯CPU) |
| `hmm_state.py` | 听海 | 4 状态 HMM (QUIET/BULL/BEAR/STRESS) |
| `lstm_predictor.py` | 听海 | BiLSTM 4 视野期 (15m/45m/90m/180m) |
| `meta_model.py` | 听海 | LSTM+XGBoost+Factor 加权融合 |
| `garch_predictor.py` | 听海 | GARCH(1,1) 条件波动率 + 年化波动率 |
| `retrain_pipeline.py` | 统一 | 周期性重训 → AB 测试 → 模型升级 |
| `model_registry.py` | 统一 | 模型版本管理 |

**5 层 ML 管线：**
```
Layer 1: HMM (市场状态识别) → 状态感知权重
Layer 2: LSTM (短期方向预测, 4 视野)
Layer 3: XGBoost (36 特征策略信号 + 量价特征)
Layer 4: GARCH (条件波动率 + 残差检验)
Layer 5: VaR/CVaR (SAFE/CAUTION/DANGER/CRITICAL)
         ↓
Meta-Ensemble: 加权融合 → 最终信号
```

### 3.10 进化引擎 (`core/evolution/`)

```
EvolutionEngine
├── PerformanceTracker: 记录每个策略/组合的实时表现
├── ABTester: t 检验比较新旧策略（p < 0.05 显著差异）
└── EvolutionScheduler: 周期性触发淘汰/迭代
```

### 3.11 策略锦标赛系统 (`core/tournament/`)

来自听海 `agent_tournament.py` (39KB)：

```
三种运行模式：
├── DUEL: A/B 微仓对决（信号不确定时分别开仓评测）
├── TOURNAMENT: N 策略 PnL/Sharpe 排名
│   ├── 底部 20% 淘汰
│   └── 顶部 20% 增强
└── EXPLORATION: 随机参数采样探索新策略

StrategyEvaluator: 回测评分器
├── win_rate, profit_factor, sharpe, correlation
├── greedy low-correlation selection
└── evolution_prune(策略池, 保留率=0.8)
```

### 3.12 市场微观结构 (`core/microstructure/`)

来自听海 `market_microstructure.py` (23KB) + 楚风 `quant_models/`：

```
MarketMicrostructureAnalyzer
├── KLSLambda: 价格冲击系数（流动性压力检测）
│   ├── lambda = Δprice / volume
│   └── 阈值: NORMAL / ELEVATED / STRESSED
├── IsingHerding: 伊辛羊群模型
│   ├── magnetization（磁化强度 → 羊群强度）
│   └── susceptibility（磁化率 → 相变预警）
├── HawkesProcess: 自激过程
│   ├── baseline + 自激核
│   └── branching ratio → 级联风险
└── analyze_cross_contract(symbols) → systemic_risk
```

### 3.13 缠论分析 (`core/analysis/chan_theory.py`)

来自听海 `chan_theory.py` (24.7KB) + 观山 `chan_theory.py`：

```
ChanTheory
├── find_pivots(df, level)              # 顶底分型识别
├── find_strokes(pivots)                # 笔生成
├── find_zhong_shu(strokes)             # 中枢识别
├── detect_divergence(zhong_shu, price) # 背驰检测
├── classify_trade_points(df)           # 三类买卖点
│   ├── Type1: 趋势背驰点（±2.5）
│   ├── Type2: 第二类买卖点（±2.0）
│   └── Type3: 第三类买卖点（±2.2）
└── multi_level_analysis(levels)        # 多级别共振
    ├── level: D1 / H1 / M5
    └── 多级别同向 → 强信号（±3.0）
```

### 3.14 14 经典量化模型 (`core/quant_models/`)

来自楚风 `quant_models/*.py` (80KB)，统一入口：

| 模型 | 文件 | 用途 |
|------|------|------|
| GBM | `gbm_model.py` | 几何布朗运动价格模拟 |
| HMM | `hmm_model.py` | 隐马尔可夫状态识别 |
| Markowitz | `markowitz_optimizer.py` | 马科维茨组合优化 |
| Cointegration | `cointegration_arb.py` | 协整套利 |
| GARCH | `garch_model.py` | 波动率建模 |
| Poisson | `poisson_model.py` | 泊松跳跃过程 |
| Liquidity Density | `liquidity_density.py` | 流动性密度估计 |
| Square-Root Impact | `sqrt_impact.py` | 平方根价格冲击 |
| KLS Lambda | `kls_lambda.py` | Kyle's Lambda |
| Almgren-Chriss | `algem_chriss.py` | 最优执行模型 |
| Hawkes | `hawkes_process.py` | 自激过程 |
| Ising | `ising_herd.py` | 伊辛模型 |
| Chan Theory | `chan_theory.py` | 缠论 |
| DataLayer | `data_layer.py` | 通用数据获取器 |

### 3.15 规则引擎 (`core/simulation/rule_engine.py`)

来自听海 `rule_engine.py` (31.4KB)，零 LLM 依赖的信号→交易决策系统：

```
RuleEngine
├── filter_signals(signals) → filtered
│   ├── 共振强度阈值（>60 通过）
│   ├── 策略方向一致性检查
│   ├── 最小置信度过滤
│   └── 品种黑/白名单
├── check_entry_conditions(signal) → bool
│   ├── 已有仓位方向冲突？
│   ├── 品种相关敞口已满？
│   ├── 距前次开仓时间达标？
│   └── VaR 敞口允许？
├── check_exit_conditions(position) → bool
│   ├── 信号反转？
│   ├── SL/TP 触发？
│   └── 定时平仓？
└── Config (per-variety)
    ├── threshold: 共振通过分数
    ├── min_confidence: 最小置信度
    ├── max_positions_per_symbol
    └── cooldown_minutes
```

### 3.16 新闻情绪 (`core/news/`)

来自楚风 `news_sentiment.py` + `news_sentiment_v2.py`：

```
NewsSentimentEngine
├── search_news(symbol, keywords)        # Tavily API 搜索
├── score_sentiment(texts) → float       # -1 ~ +1 情感评分
├── keyword_sentiment(symbol) → Signal   # 关键词映射评分
├── COOLDOWN: 同一品种 30 分钟冷却
└── CONFIDENCE: 多源一致性检查
```

### 3.17 基本面分析 (`core/fundamental/`)

来自楚风 `fundamental_engine.py`：

```
FundamentalEngine
├── analyze_industry_supply(sector)       # 行业供应分析
├── analyze_demand_drivers(symbol)        # 需求驱动因素
├── get_policy_impact(symbol)             # 政策影响评估
└── score_fundamentals(symbol) → Signal   # 综合信号
```

### 3.18 品种知识库 (`core/knowledge/`)

来自楚风 `futures_knowledge.py` (1081 行) + 观山品种映射：

```
FuturesKnowledge
├── get_product_info(symbol) → ProductInfo
│   ├── name, exchange, category
│   ├── multiplier, min_tick, margin_rate
│   ├── volatility_profile (HIGH/MED/LOW)
│   ├── associated_products
│   ├── delivery_months
│   └── trading_warnings
├── get_products_by_category(cat) → List[ProductInfo]
├── get_delivery_months(symbol) → List[int]
└── get_margin_rate(symbol) → float
```

覆盖 78 个品种（听海 `contracts_config.py` 提供完整列表）。

### 3.19 数据质量护栏 (`core/data/data_quality.py`)

```
CHECKS = [
    ("schema", validate_schema),           # 列名/类型/非空
    ("range", check_price_range),          # 价格合理性（>0, <历史极值*10）
    ("continuity", check_no_gaps),         # 交易日连续性
    ("duplicate", check_no_duplicates),    # 主键去重
    ("outlier", detect_outliers_iqr),      # IQR 异常值检测
    ("volume", check_volume_reasonable),   # 成交量 0 或暴增 100 倍
]
```

### 3.20 通知系统 (`core/notification/`)

```
AlertManager
├── channels: feishu / email / slack / telegram
├── send_alert(alert):
│   ├── INFO → feishu
│   ├── WARNING → feishu + email
│   ├── CRITICAL → all channels
│   └── EMERGENCY → all channels + phone

SentinelSystem (楚风)
├── 7 alert types: SIGNAL_CHANGE / RESONANCE / RISK / PRICE / VOLUME / POSITION / SYSTEM
├── v2: dedup / cooling / confidence filter
└── check_alerts(signals, positions) → List[Alert]
```

### 3.21 多周期管理 (`core/timeframe/`)

来自楚风 `timeframe_manager.py` (361 行)：

```
TimeframeManager
├── get_raw_data(symbol, base='5m') → DataFrame
├── resample(df, target) → DataFrame        # K线聚合
├── get_multi_timeframe(symbol) → Dict      # 所有周期
└── align_signals(signals_by_tf) → DataFrame # 信号对齐

TIMEFRAME_HIERARCHY: ['5m', '15m', '30m', '1h', '4h', '1d']
```

### 3.22 配置管理 (`core/config/`)

```
ConfigManager
├── get(key, default=None)                  # 点表示法: 'strategy.params.atr_period'
├── loaders: yaml / json / env / vault...
├── hot_reload: 每 5 秒检查文件 mtime
├── register_listener(callback, keys)       # 配置变更监听
└── merge: 文件 > 环境变量 > 默认值
```

### 3.23 数据库管理 (`core/db/`)

来自楚风 `db_manager.py` (272 行)：

```
DatabaseManager
├── db_path → str                           # 自动选择 shared / local
├── query_daily(symbol, start, end) → DataFrame
├── query_minute(symbol, period, start, end) → DataFrame
├── save_daily(symbol, df) → int            # 去重 upsert
├── save_minute(symbol, period, df) → int
├── get_latest_date(symbol) → str
├── get_contracts() → List[Dict]
└── validate_data(symbol, period) → Dict
```

### 3.24 跨模块接口契约（多模型并行开发专用）

以下接口定义是 **不同模型并行开发时的契约**。实现方和消费方各做各的，以契约为界。

#### `MarketDataManager` (3.1) → `StrategyEngine` 契约

```python
# 数据层输出 → 策略层输入
class DataFeed:
    """策略引擎依赖的唯一数据接口"""
    symbol: str
    timeframe: str                 # '1d' | '1h' | '4h' | '30m' | '15m' | '5m'
    df: pd.DataFrame               # 列: ['open','high','low','close','volume','open_interest']
    start_date: str                # YYYY-MM-DD
    end_date: str
    quality_score: float           # 0-1

# MarketDataManager 必须实现
def get_data_feed(symbol: str, timeframe: str,
                  start: str = None, end: str = None) -> DataFeed: ...

def list_available_symbols() -> List[str]: ...
def list_timeframes() -> List[str]: ...
```

#### `BaseStrategy.compute()` (3.2) → `StrategyEngine` 契约

```python
# 每个策略的输出格式
class StrategyOutput:
    signal: Signal                 # 见 3.2 Signal dataclass
    debug_info: Dict               # 策略内部指标值，用于调试

# StrategyEngine 接收 List[StrategyOutput]
# → 汇总后送入 ResonanceEngine
```

#### `ResonanceEngine` (3.3) → `RuleEngine` 契约

```python
# 共振引擎输出
class ResonanceOutput:
    symbol: str
    score_G: float                 # -10 ~ +10, 观山系统 score
    score_C: float                 # -10 ~ +10, 楚风系统 score
    score_T: float                 # -10 ~ +10, 听海系统 score
    final_score: float             # w_G*S_G + w_C*S_C + w_T*S_T
    direction: Literal["BUY", "SELL", "HOLD"]
    confidence: float              # 0-1
    regime: MarketRegime           # 当前市场状态
    weight_G: float                # 当前使用权重
    weight_C: float
    weight_T: float

# ResonanceEngine 接口
async def calculate(symbol: str,
                    signals: List[StrategyOutput],
                    regime: MarketRegime) -> ResonanceOutput: ...
```

#### `RiskManager` (3.6) → `SimEngine` (3.5) 契约

```python
@dataclass
class RiskVerdict:
    allowed: bool                  # 是否允许开仓
    reason: str                    # 拒绝原因
    max_size: int                  # 建议最大手数
    suggested_sl: float            # ATR 止损价
    suggested_tp: float            # 止盈价

# RiskManager 接口
def check_signal(symbol: str, direction: str,
                 signal: Signal, positions: List[Position]) -> RiskVerdict: ...

# SimEngine 接口  
async def execute_signal(signal: Signal,
                         risk: RiskVerdict) -> Optional[Position]: ...
```

**并行开发原则**：
- 各模型按照本契约的输入/输出类型定义开发各自模块
- 实现阶段用 `Protocol` / `ABC` 做静态类型检查
- 集成阶段只需确认契约字段对齐，无需深入对方代码

---

## 4. 数据流

### 4.1 主数据流（日频）

```
market_data_fetcher (16 类数据源)
    │
    ▼
MarketDataManager ─── Cache (LRU + Redis) ─── HistoryStore
    │                                                   │
    ▼                                                   │
StrategyEngine                                          │
    │  并行计算所有活跃策略（46 个）                       │
    ▼                                                   │
Signal[] (每个策略一个 Signal)                            │
    │                                                   │
    ▼                                                   │
3-Layer Filter (趋势→均值回复→事件驱动)                   │
    │                                                   │
    ▼                                                   │
ResonanceEngine:
    Voter(观山)→Score_G                                  │
    Matrix(楚风)→Score_C                                 │
    Scanner(听海)→Score_T                                │
    WeightLearner→w_G, w_C, w_T                          │
    │                                                   │
    ▼                                                   │
Score_final = w_G×S_G + w_C×S_C + w_T×S_T               │
    │                                                   │
    ▼                                                   │
RuleEngine (方向一致 / 置信度 / 品种白名单)                │
    │                                                   │
    ▼                                                   │
RiskManager (VaR/敞口/回撤/相关性)                        │
    │                                                   │
    ▼                                                   │
SimEngine (评分→仓位→订单执行→持仓更新)                    │
    │                                                   │
    ▼                                                   │
API → WebSocket → Frontend                              │
    │                                                   │
    ▼                                                   │
Daily loop:
    ├── PnL 结算 → PerformanceTracker → 策略得分更新
    ├── 模型重训检查 → retrain_pipeline (若到期)
    └── 锦标赛调度 → tournament_step (若到期)
```

### 4.2 WebSocket 实时推送

```
连接建立 → 发送当前状态（持仓/信号/风险）
    │
    ▼
盘中事件触发推送:
├── 新信号 → {"type": "signal", "data": Signal}
├── 持仓变更 → {"type": "position_update", "data": Position}
├── PnL 更新 → {"type": "pnl_update", "data": PnLSummary}
├── 风险预警 → {"type": "risk_alert", "data": RiskAlert}
├── 回测完成 → {"type": "backtest_done", "data": BacktestResult}
└── 心跳 → {"type": "heartbeat", "timestamp"}
```

---

## 5. API 设计

### 5.1 REST API

#### 数据
| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/data/daily/{symbol}` | 日线 |
| GET | `/api/v1/data/minutes/{symbol}` | 分钟线 |
| GET | `/api/v1/data/realtime/{symbols}` | 实时行情 |
| GET | `/api/v1/data/contracts` | 主力合约 |
| GET | `/api/v1/data/sources` | 数据源状态 |
| GET | `/api/v1/data/macro` | 宏观数据 |
| GET | `/api/v1/data/cot` | CFTC 持仓 |
| GET | `/api/v1/data/inventories` | EIA 库存 |
| GET | `/api/v1/data/options/{symbol}` | 期权链 |
| GET | `/api/v1/data/volatility-index` | 波动率指数 |
| PUT | `/api/v1/data/cache/clear` | 清空缓存 |

#### 历史数据
| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/history/stats` | 统计概览 |
| GET | `/api/v1/history/{symbol}` | 获取 K 线 |
| POST | `/api/v1/history/query` | 时间范围查询 |
| POST | `/api/v1/history/save` | 保存至历史 |
| POST | `/api/v1/history/pull` | 拉取并保存 |
| POST | `/api/v1/history/validate` | 校验重复/缺失 |
| POST | `/api/v1/history/repair` | 修复缺失 |
| POST | `/api/v1/history/export` | 导出 CSV |

#### 策略
| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/strategies` | 策略列表 |
| GET | `/api/v1/strategies/{name}` | 策略详情 |
| PUT | `/api/v1/strategies/{name}/params` | 参数更新 |
| PUT | `/api/v1/strategies/{name}/toggle` | 启用/禁用 |
| POST | `/api/v1/strategies/compute/{symbol}` | 手动触发计算 |
| GET | `/api/v1/signals/current` | 当前所有信号 |
| GET | `/api/v1/signals/history` | 信号历史 |
| GET | `/api/v1/resonance/current` | 当前共振状态 |
| GET | `/api/v1/resonance/weights` | 共振权重 |

#### 交易
| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/trading/positions` | 当前持仓 |
| GET | `/api/v1/trading/history` | 交易历史 |
| GET | `/api/v1/trading/pnl` | PnL 汇总 |
| POST | `/api/v1/trading/order` | 手动下单 |
| DELETE | `/api/v1/trading/position/{id}` | 平仓 |
| POST | `/api/v1/trading/reset` | 重置模拟账户 |

#### 回测
| Method | Path | 描述 |
|--------|------|------|
| POST | `/api/v1/backtest/run` | 启动回测 |
| GET | `/api/v1/backtest/status/{id}` | 回测状态 |
| GET | `/api/v1/backtest/result/{id}` | 回测结果 |
| POST | `/api/v1/backtest/compare` | 对比回测 |

#### 市场状态
| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/market/regime` | 当前市场状态 |
| GET | `/api/v1/market/state` | 状态机详情 |
| GET | `/api/v1/cross-symbol/analysis` | 跨品种分析 |
| GET | `/api/v1/cross-symbol/rotation` | 板块轮动 |

#### 组合优化
| Method | Path | 描述 |
|--------|------|------|
| POST | `/api/v1/portfolio/markowitz` | 马科维茨 |
| POST | `/api/v1/portfolio/hrp` | HRP |
| POST | `/api/v1/portfolio/cvar` | CVaR |
| GET | `/api/v1/portfolio/efficient-frontier` | 有效前沿 |

#### ML
| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/ml/models` | 模型列表 |
| POST | `/api/v1/ml/retrain` | 触发重训 |
| GET | `/api/v1/ml/status/{model}` | 训练状态 |

#### 锦标赛
| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/tournament/status` | 锦标赛状态 |
| POST | `/api/v1/tournament/step` | 手动触发一轮 |
| GET | `/api/v1/tournament/leaderboard` | 排名榜 |

#### 系统
| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| GET | `/api/v1/version` | 版本 |
| GET | `/api/v1/config` | 当前配置 |

### 5.2 WebSocket API

**连接**: `ws://host:port/api/v1/ws`

**Client → Server**:
```json
{"action": "subscribe", "symbols": ["RB", "CU", "AU"]}
{"action": "unsubscribe", "symbols": ["RB"]}
{"action": "ping"}
```

**Server → Client**:
```json
{"type": "tick", "symbol": "RB", "data": {"last_price": 3850, ...}}
{"type": "signal", "data": {"strategy": "ema_cross", "direction": "BUY", ...}}
{"type": "position_update", "data": {"symbol": "RB", "unrealized_pnl": 1200}}
{"type": "pnl_update", "data": {"total_equity": 105000}}
{"type": "risk_alert", "data": {"level": "WARNING", "type": "DRAWDOWN"}}
{"type": "resonance", "data": {"score_G": 3.2, "score_C": 5.1, "score_T": -2.0, "final": 2.1}}
{"type": "backtest_done", "data": {...}}
{"type": "pong", "timestamp": 1718100000}
```

---

## 6. 数据库设计

### 6.1 数据模型

```python
class Contract(Base):
    """品种合约表"""
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False)
    name = Column(String(100))              # 螺纹钢, 沪铜
    exchange = Column(String(20))           # SHFE, DCE, CZCE, CFFEX, INE, GFEX
    category = Column(String(20))           # metal, energy, chemical, agri
    multiplier = Column(Integer)            # 合约乘数
    min_tick = Column(Float)
    margin_rate = Column(Float)
    commission = Column(Float)
    is_active = Column(Boolean, default=True)

class DailyData(Base):
    """日线数据"""
    __tablename__ = "daily_data"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    open / high / low / close = Column(Float)
    volume = Column(BigInteger)
    open_interest = Column(BigInteger)
    amount = Column(BigInteger)
    __table_args__ = (UniqueConstraint("symbol", "trade_date"),)

class MinuteData(Base):
    """分钟线数据"""
    __tablename__ = "minute_data"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    period = Column(String(10), nullable=False)  # 5m, 15m, 30m, 1h...
    datetime = Column(DateTime, nullable=False)
    open / high / low / close = Column(Float)
    volume = Column(BigInteger)
    __table_args__ = (UniqueConstraint("symbol", "period", "datetime"),)

class SignalRecord(Base):
    """信号记录"""
    __tablename__ = "signal_records"
    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(100), index=True)
    symbol = Column(String(20), index=True)
    direction = Column(String(10))
    score = Column(Float)
    confidence = Column(Float)
    price = Column(Float)
    signal_time = Column(DateTime, index=True)
    market_state = Column(String(20))
    details = Column(Text)                  # JSON

class TradeRecord(Base):
    """交易记录"""
    __tablename__ = "trade_records"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), index=True)
    direction = Column(String(10))
    entry_price / exit_price = Column(Float, nullable=True)
    entry_time / exit_time = Column(DateTime)
    quantity = Column(Integer)
    pnl / pnl_pct = Column(Float)
    stop_loss / take_profit = Column(Float)
    strategy = Column(String(100))
    status = Column(String(20), default="open")
    reason = Column(String(500))

class BacktestResult(Base):
    __tablename__ = "backtest_results"
    # ... 标准回测指标字段

class ModelVersion(Base):
    """ML 模型版本"""
    __tablename__ = "model_versions"
    model_name / version / description / metrics / file_path / is_active / trained_at

class PerformanceSnapshot(Base):
    """每日表现快照"""
    __tablename__ = "performance_snapshots"
    date / total_equity / cash / positions_value / daily_pnl / total_pnl / drawdown / metrics

class TournamentRecord(Base):
    """锦标赛记录"""
    __tablename__ = "tournament_records"
    strategy_name / score / sharpe / win_rate / trades / rank / round
```

### 6.2 数据库选择

| 环境 | 数据库 | 连接池 | 迁移工具 |
|------|--------|--------|----------|
| 开发 | SQLite (`data/futures.db`) | 无（threading.local） | Alembic |
| 生产 | PostgreSQL 16 (Docker) | SQLAlchemy pool (5-20) | Alembic |

---

## 7. 前端设计

### 7.1 技术栈

- **框架**: React 18 + TypeScript + Vite
- **UI 库**: Ant Design 5.x (zhCN)
- **图表**: lightweight-charts 4.x (TradingView)
- **状态管理**: Zustand 4 (persist middleware)
- **网络**: axios (REST) + 原生 WebSocket (useWebSocket hook)
- **路由**: react-router-dom v6

### 7.2 页面布局

```
┌──────────────────────────────────────────────────────────┐
│ Header: Logo / 系统状态 / 当前权益 / 信号计数器 / 主题   │
├──────────┬───────────────────────────────────────────────┤
│ Sidebar  │  Content Area                                 │
│          │  ┌─────────────────────────────────────────┐  │
│ Dashboard│  │                                         │  │
│ Data     │  │  根据路由显示对应页面                     │  │
│ Strategy │  │                                         │  │
│ Trading  │  │  Dashboard: 权益曲线/信号面板/市场状态    │  │
│ Backtest │  │  Strategy: 策略列表/共振可视化/信号流     │  │
│ Portfolio│  │  Trading: 持仓表/PnL曲线/下单面板        │  │
│ ML       │  │  Tournament: 锦标赛状态/排名榜            │  │
│ Settings │  │  ...                                     │  │
│          │  └─────────────────────────────────────────┘  │
├──────────┴───────────────────────────────────────────────┤
│ Footer: 版本 / 延迟 / 最后同步时间                       │
└──────────────────────────────────────────────────────────┘
```

### 7.3 核心页面

| 页面 | 组件 | 核心内容 |
|------|------|----------|
| **Dashboard** | `pages/Dashboard.tsx` | 权益曲线、信号汇总、市场状态、风险指标、活跃策略 |
| **Data Center** | `pages/DataCenter.tsx` | 数据源状态（绿/红灯）、查询工具、预览表、历史管理 |
| **Strategy** | `pages/Strategy.tsx` | 策略列表、详情、共振可视化（三系统 Score 柱状图）、实时信号流 |
| **Trading** | `pages/Trading.tsx` | 持仓表、下单面板、PnL 曲线、交易历史、风险监控 |
| **Backtest** | `pages/Backtest.tsx` | 参数表单、进度/状态、结果卡片、权益曲线、对比视图 |
| **Portfolio** | `pages/Portfolio.tsx` | 优化配置、有效前沿图、权重分配、结果对比 |
| **ML** | `pages/ML.tsx` | 模型列表、训练控制台、特征重要性、版本管理 |
| **Tournament** | `pages/Tournament.tsx` | 排名榜、策略 PnL 对比、淘汰/晋级可视化 |
| **Settings** | `pages/Settings.tsx` | 主题、语言、数据源、刷新间隔、账户参数 |

### 7.4 状态管理 (Zustand)

```
┌──────────────────────────────────────────────────────┐
│ stores/                                              │
│ ├── marketStore.ts     — K线缓存（symbol+period）     │
│ ├── tradingStore.ts    — 账户/持仓/订单/交易历史      │
│ ├── strategyStore.ts   — 策略/回测结果/模板           │
│ ├── tournamentStore.ts — 锦标赛状态/排名              │
│ ├── watchlistStore.ts  — ⭐自选列表 (persist)         │
│ └── themeStore.ts      — 明/暗主题 (persist)         │
└──────────────────────────────────────────────────────┘
```

### 7.5 WebSocket Hook

复用 `qzh-trading-main` 的 `useWebSocket.ts` (130 行)：
- 自动重连（3 秒间隔）
- 消息按 type 分发到对应 store
- subscribe/unsubscribe 方法
- 连接状态 `connected` state

---

## 8. 部署方案

### 8.1 开发环境（Windows）

```bash
# 后端
cd backend
python -m venv venv
pip install -r requirements.txt
uvicorn main:app --reload --port 8765

# 前端
cd frontend
npm install
npm run dev
```

### 8.2 生产环境（VPS Ubuntu 22.04）

**Docker Compose (精简版，不含 Celery)：**
```yaml
version: '3.8'
services:
  backend:
    build: 
      context: ./backend
      dockerfile: ../deploy/Dockerfile.backend
    ports:
      - "8765:8765"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./logs:/app/logs
    environment:
      - DATABASE_URL=postgresql://tsc:${DB_PASSWORD}@db:5432/tsc
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=info
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

  frontend:
    build:
      context: ./frontend
      dockerfile: ../deploy/Dockerfile.frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  celery-worker:
    build:
      context: ./backend
      dockerfile: ../deploy/Dockerfile.backend
    command: celery -A core.tasks.celery_app worker -Q backtest,training,reports -c 2
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    environment:
      - DATABASE_URL=postgresql://tsc:${DB_PASSWORD}@db:5432/tsc
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - db

  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=tsc
      - POSTGRES_USER=tsc
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tsc"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/nginx.conf
      - ./deploy/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
```

**nginx 反向代理 (关键配置)：**
```nginx
# 后端 API 代理 — 长超时支持回测
location /api/ {
    proxy_pass http://backend:8765;
    proxy_read_timeout 300s;    # 回测任务可能 > 60s
    proxy_send_timeout 60s;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";  # WebSocket 支持
}

# WebSocket
location /ws/ {
    proxy_pass http://backend:8765;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;   # WS 长连接
}

# 前端静态资源
location / {
    proxy_pass http://frontend:3000;
}
```

### 8.3 Ubuntu 初始化脚本

```bash
# scripts/setup_ubuntu.sh
#!/bin/bash
set -e

# 1. 系统更新
apt update && apt upgrade -y
apt install -y docker.io docker-compose python3-pip nodejs npm ufw fail2ban

# 2. 防火墙 — 只开放 80/443
ufw default deny incoming
ufw default allow outgoing
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 3. Fail2ban SSH 保护
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
EOF
systemctl restart fail2ban

# 4. 克隆项目
git clone <repo> /opt/trading-strategy-center
cd /opt/trading-strategy-center

# 5. 创建 .env（手动编辑 DB_PASSWORD, SECRET_KEY 等）
cp .env.example .env
# vi .env ← 手动编辑敏感信息

# 6. 启动
docker-compose up -d

# 7. 初始化数据库
docker-compose exec -T backend alembic upgrade head

# 8. 定时任务（收盘后处理）
crontab -l | { cat; echo "0 15 * * 1-5 cd /opt/trading-strategy-center && docker-compose exec -T backend python -m scripts.daily_close"; } | crontab -

# 9. 日志轮转
cat > /etc/logrotate.d/tsc << EOF
/opt/trading-strategy-center/data/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF

echo "✅ 部署完成！"
```

### 8.4 安全加固

| 措施 | 配置 |
|------|------|
| 防火墙 | 仅开放 80/443，关闭 22(改用 VPN) |
| DB 密码 | Docker Secret 或 .env，不提交 Git |
| JWT 密钥 | `SECRET_KEY` 环境变量，128 位随机 |
| nginx 限流 | `limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s` |
| CORS | 仅允许前端域名 |
| HTTPS | Let's Encrypt + certbot 自动续期 |
| Docker 非 root | 使用 `USER appuser` 非 root 运行 |
| 依赖扫描 | `pip-audit` + `npm audit` CI 阶段检查 |

---

## 9. 错误处理与重试策略

### 9.1 全局异常处理

```python
# api/middleware/error_handler.py
@ app.exception_handler(AppException)
async def app_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
            "request_id": request.state.request_id,
        }
    )

# 自定义异常层次
class AppException(Exception):
    """基类，所有已知异常继承此类"""
    code: int
    message: str
    status_code: int = 400

class DataException(AppException): ...
class StrategyException(AppException): ...
class TradingException(AppException): ...
class BacktestException(AppException): ...
class ConfigException(AppException): ...
```

#### 9.1b 错误码定义

| 错误码 | 异常类 | HTTP | 描述 |
|--------|--------|------|------|
| 40000 | `AppException` | 400 | 通用请求错误 |
| 40001 | `DataException` | 502 | 数据获取失败（数据源超时/不可用） |
| 40002 | `DataException` | 400 | 数据质量不合格（评分 < 0.5） |
| 40003 | `DataException` | 404 | 数据源不可用（未配置 API Key） |
| 40004 | `DataException` | 400 | 请求参数无效（symbol/日期格式错误） |
| 41000 | `StrategyException` | 500 | 策略执行内部错误 |
| 41001 | `StrategyException` | 400 | 策略参数无效（ATR period ≤ 0 等） |
| 41002 | `StrategyException` | 404 | 策略未注册（未加 `@register`） |
| 41003 | `StrategyException` | 400 | 品种不在策略支持列表 |
| 42000 | `TradingException` | 400 | 交易执行错误 |
| 42001 | `TradingException` | 400 | 资金不足 |
| 42002 | `TradingException` | 400 | 超过风控限制（最大持仓/敞口/回撤） |
| 42003 | `TradingException` | 400 | 方向已存在持仓 |
| 43000 | `BacktestException` | 500 | 回测执行错误 |
| 43001 | `BacktestException` | 400 | 回测参数冲突（开始日期 > 结束日期） |
| 43002 | `BacktestException` | 400 | 回测数据不足 |
| 44000 | `ConfigException` | 500 | 配置加载失败 |
| 44001 | `ConfigException` | 500 | 配置文件格式错误 |
| 50000 | `AppException` | 500 | 内部服务器错误（未捕获异常） |

**使用约定**：所有 API 响应中 `code` 字段使用此表。不同模型开发不同模块时，统一使用这些错误码。

### 9.2 重试策略

| 场景 | 策略 | 参数 |
|------|------|------|
| 数据源 API 超时 | 指数退避 | 3 次, base=1s, max=10s |
| DB 连接失败 | 指数退避 + 熔断 | 5 次, base=2s, 熔断 60s |
| Celery 任务失败 | 线性重试 | 3 次, 间隔 10s |
| 模型加载失败 | 一次重试 + fallback | 降级到旧版本 |
| 外部 HTTP 请求 | 指数退避 | 3 次, base=0.5s |

```python
# core/utils/decorators.py
def retry(max_retries=3, base_delay=1.0, backoff=2.0, exceptions=(Exception,)):
    """指数退避重试装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (backoff ** attempt)
                        time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator
```

### 9.3 服务降级

| 降级级别 | 行为 |
|----------|------|
| **正常** | 所有功能可用 |
| **降级** | 数据源不可用 → 使用缓存数据；ML 模型不可用 → 纯技术分析 |
| **最小** | 仅基础行情和手动交易可用 |

---

## 10. 安全设计

### 10.1 认证与授权
- JWT 令牌（access_token 30m + refresh_token 7d）
- RBAC 角色：admin / analyst / viewer
- API 限流：30 req/s per IP，回测任务限 2/min

### 10.2 密钥管理
- `.env` 文件（开发）/ Docker secrets（生产）
- 禁止硬编码：原始代码中的 CTP 账号密码、API Key 全部移到配置

### 10.3 网络安全
| 措施 | 说明 |
|------|------|
| TLS 1.3 | Let's Encrypt + certbot |
| CORS | 白名单前端域名 |
| CSP Header | `script-src 'self'` 防止 XSS |
| Rate Limiting | nginx `limit_req` + FastAPI middleware |

### 10.4 审计日志
- 所有写操作（配置修改/下单/触发回测）记录审计日志
- 格式：`{timestamp, user, action, resource, result, ip}`

---

## 11. 监控与可观测性

### 11.1 Prometheus 指标

| 指标 | 类型 | 标签 | 说明 |
|------|------|------|------|
| `api_requests_total` | Counter | method, path, status | API 调用量 |
| `api_duration_seconds` | Histogram | method, path | API 延迟 |
| `tasks_total` | Counter | task_name, status | 任务总数 |
| `task_duration_seconds` | Histogram | task_name | 任务耗时 |
| `signals_generated_total` | Counter | strategy, symbol | 信号生成数 |
| `trades_total` | Counter | symbol, direction | 交易数 |
| `positions_open` | Gauge | symbol | 持仓数 |
| `data_quality_score` | Gauge | symbol, period | 数据质量分 |
| `cache_hit_rate` | Gauge | cache_name | 缓存命中率 |
| `db_connections` | Gauge | pool_name | 连接池使用率 |
| `ws_connections` | Gauge | — | WS 连接数 |

### 11.2 结构化日志

```python
# 统一日志格式
{"timestamp": "...", "level": "INFO", "module": "...", 
 "request_id": "uuid", "message": "...", 
 "extra": {...}}
```

### 11.3 告警规则

| 条件 | 级别 | 通知 |
|------|------|------|
| API 错误率 > 5% | WARNING | 飞书 |
| 任务失败率 > 10% | CRITICAL | 飞书 + 邮件 |
| 缓存命中率 < 50% | WARNING | 飞书 |
| DB 连接池 > 80% | CRITICAL | 飞书 |
| 数据质量分 < 0.5 | WARNING | 飞书 |
| 回撤 > 10% | EMERGENCY | 全渠道 |

---

## 12. CI/CD 流水线

```yaml
# .github/workflows/ci.yml
name: CI/CD
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Lint
        run: ruff check .
      - name: Type check
        run: mypy backend/
      - name: Unit tests
        run: pytest tests/unit/ -v
      - name: Dependency audit
        run: pip-audit

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker images
        run: docker-compose build
      - name: Push to registry
        run: |
          docker tag tsc-backend ${{ secrets.REGISTRY }}/tsc-backend:${{ github.sha }}
          docker push ${{ secrets.REGISTRY }}/tsc-backend:${{ github.sha }}

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_KEY }}
          script: |
            cd /opt/trading-strategy-center
            docker-compose pull
            docker-compose up -d --force-recreate
            docker image prune -f
```

---

## 13. 测试策略

### 13.1 测试分类

| 类型 | 范围 | 工具 | 目标覆盖率 |
|------|------|------|-----------|
| 单元测试 | 核心信号/共振/风险逻辑 | pytest | > 90% |
| API 集成 | 所有 REST + WS 端点 | pytest + httpx | > 80% |
| 回测可重复 | 确保结果一致 | pytest | 关键路径 |
| 数据源模拟 | market_data_fetcher | pytest + mock | 100% 公共方法 |

### 13.2 测试数据
- 预设 CSV 数据（`tests/fixtures/`）：包含 5 个品种的 2 年日线 + 1 个月分钟线
- 所有回测必须使用固定随机种子，确保结果可重复

### 13.3 测试命令

```bash
# 全部
pytest tests/ -v --cov=backend --cov-report=term-missing

# 单元
pytest tests/unit/ -v

# 集成
pytest tests/integration/ -v

# 回测可重复性（关键！确保后续开发不改坏历史结果）
pytest tests/integration/test_backtest_reproducibility.py -v
```

---

## 14. 实现路线图

### Phase 1: 基础设施 (3-5 天)
> **并行分配**: 模型A(基础设置+数据层) | 模型B(API骨架+DB) | 模型C(前端骨架+异常处理)
1. 创建项目目录结构
2. 实现 `pyproject.toml` / `requirements.txt` / `settings.py`
3. 实现 `market_data_manager.py`（封装 data_source_manager）
4. 实现 `db/models.py` + 初始化迁移
5. 实现 `main.py`（FastAPI 骨架）
6. 实现 `api/routes/health_routes.py`
7. 创建前端项目骨架（Vite + React + Ant Design + router）
8. 实现 `core/data/data_quality.py`
9. 实现全局异常处理（`api/middleware/error_handler.py`）
10. 实现 `core/utils/decorators.py`（retry 装饰器）

### Phase 2: 策略核心 (5-7 天)
> **并行分配**: 模型A(框架+趋势/反转策略) | 模型B(突破/动量/过滤策略) | 模型C(ML/缠论/Alpha101)
1. 实现 `signals/base.py`（BaseStrategy + Signal）
2. 实现 `signals/registry.py`（装饰器 + 自动发现）
3. 实现 `signals/indicators.py`（合并去重指标库）
4. 实现 `signals/engine.py`
5. 实现全部 46 个策略（趋势/反转/突破/动量/过滤）
6. 实现 `signals/price_action.py`
7. 实现 `signals/layering/` 三层过滤
8. 实现 `alpha101/alpha_factors.py`

### Phase 3: 共振 + 市场状态 (3-4 天)
> **并行分配**: 模型A(市场状态) | 模型B(共振 Voter+Matrix) | 模型C(共振 Scanner+WeightLearner)
1. 实现 `market_state/regime_detector.py`
2. 实现 `market_state/entropy_analyzer.py`
3. 实现 `market_state/state_machine.py`
4. 实现 `resonance/voter.py`（观山）
5. 实现 `resonance/matrix.py`（楚风）
6. 实现 `resonance/scanner.py`（听海）
7. 实现 `resonance/engine.py` + `WeightLearner`

### Phase 4: 模拟交易 + 风控 (3-4 天)
> **并行分配**: 模型A(模拟交易引擎) | 模型B(风控全部) | 模型C(规则引擎+信号适配)
1. 实现 `simulation/sim_engine.py`
2. 实现 `simulation/position_manager.py`
3. 实现 `simulation/pnl_calculator.py`
4. 实现 `simulation/scoring.py`
5. 实现 `simulation/rule_engine.py`
6. 实现 `risk/` 全部模块
7. 实现 `signal_adapter.py`

### Phase 5: 回测 + 组合 + 经典模型 (3-4 天)
> **并行分配**: 模型A(回测全部) | 模型B(组合优化) | 模型C(14 量化模型)
1. 实现 `backtest/vectorized_engine.py`
2. 实现 `backtest/threshold_optimizer.py`
3. 实现 `backtest/walkforward.py`
4. 实现 `backtest/metrics.py`
5. 实现 `portfolio/` 全部模块
6. 实现 `quant_models/` 全部 14 个模型

### Phase 6: 高级分析 + Cross-Symbol + 微观结构 (3-4 天)
> **并行分配**: 模型A(Cross-Symbol+分析工具) | 模型B(缠论+微观结构) | 模型C(新闻+基本面+背离)
1. 实现 `cross_symbol/` 全部
2. 实现 `analysis/chan_theory.py` + `chan_integration.py`
3. 实现 `analysis/fourier_analyzer.py`
4. 实现 `analysis/bayesian_inference.py`
5. 实现 `analysis/factor_eval.py`
6. 实现 `analysis/oifactors.py`
7. 实现 `analysis/monte_carlo.py`
8. 实现 `analysis/seasonality.py`
9. 实现 `analysis/divergence_detector.py`
10. 实现 `microstructure/` 全部
11. 实现 `news/` 全部
12. 实现 `fundamental/`

### Phase 7: ML + 锦标赛 + 进化 (4-5 天)
> **并行分配**: 模型A(ML 训练管线+模型) | 模型B(锦标赛+进化) | 模型C(LSTM/GARCH/PPO)
1. 实现 `ml/` 全部模块
2. 实现 `tournament/` 全部
3. 实现 `evolution/` 全部
4. 实现 `notebooks/` 模型探索

### Phase 8: 前端 (5-7 天)
> **并行分配**: 模型A(Dashboard+Data+Strategy 页) | 模型B(Trading+Backtest+Portfolio 页) | 模型C(ML+Tournament+Settings 页+共振可视化)
1. 布局 + 路由 + WebSocket hook
2. 所有 9 个页面
3. 共振可视化（三系统 Score 对比图）
4. Tournament 排名 / 策略对比图

### Phase 9: API 对接 + 异步任务 + 测试 (4-5 天)
> **并行分配**: 模型A(REST API 路由) | 模型B(WS+异步任务+Celery) | 模型C(测试全量+联调)
1. 全部 REST API 路由
2. WebSocket 推送
3. Celery 配置 + 任务实现
4. 前后端联调
5. 单元测试 + 集成测试 + 回测可重复性测试

### Phase 10: 部署 (2-3 天)
> **并行分配**: 模型A(Docker+nginx) | 模型B(CI/CD+脚本) | 模型C(文档+验证)
1. Dockerfile + docker-compose
2. nginx 配置（含 WS 代理）
3. VPS 初始化脚本
4. CI/CD 配置
5. 定时任务设置

---

## 15. 关键整合决策

### 15.1 信号类型统一

| Agent | 类型 | 字段 |
|-------|------|------|
| 观山 | `Signal` dataclass | direction/confidence/price/reason |
| 楚风 | `StrategySignal`, `ResonanceSignal` | symbol/direction/strength/layer |
| 听海 | Signal enum | BUY/SELL/HOLD + score |

**决策**：使用观山 `Signal` dataclass 为模板，扩展 `source_system` / `resonance_layer` 字段，统一全系统信号类型。

### 15.2 策略注册机制

| Agent | 机制 |
|-------|------|
| 观山 | `@register` 装饰器 + `BaseStrategy` ABC + 自动发现 |
| 楚风 | `StrategyLibrary` 注册表 |
| 听海 | `Strategy` 基类 + 手动注册 |

**决策**：使用观山 `@register` 装饰器 + `BaseStrategy` ABC 作为统一框架。

### 15.3 Market Regime 合并

**决策**：以楚风 `regime_detector.py` v2（HMM + 多因子）为主力，观山熵分析作为补充验证通道。

### 15.4 共振引擎

**决策**：三系统独立计算 Score → 统一加权合并。不合并算法逻辑，合并决策面。

### 15.5 模拟引擎

**决策**：以楚风 `sim_trader_v3.py` 为核心骨架，融合听海 PositionState 的状态管理能力。信号→交易经过听海 RuleEngine 过滤。

### 15.6 数据访问

**决策**：全部通过 `MarketDataManager` 统一获取，不直接调用数据源 API。原有 akshare 调用全部替换。

### 15.7 ML 模型

| 资产 | 用途 |
|------|------|
| 听海预训练模型 | 参考结构，当前数据上重训 |
| 楚风训练逻辑 | 重训管道基础 |
| 楚风 meta_ensemble | 集成层 |
| 听海 5 层 ML 管线 | 架构参考，整合到 ML 目录 |

### 15.8 技术指标库统一

**决策**：以楚风 `TechnicalIndicators` 类为主体，观山增强指标作为扩展方法。所有策略统一从此类导入。

### 15.9 合约解析统一

**决策**：以楚风 `contract_resolver.py` 为主体（3 种主力合约识别方案），融合观山品种映射表。

### 15.10 数据库管理

**决策**：复用楚风 `db_manager.py`（自动选择共享/本地库、表名列名别名、线程安全），配合 Alembic schema 迁移。

### 15.11 通知系统

**决策**：以楚风 sentinel 为告警引擎核心，观山 feishu_push 为推送通道，听海日报逻辑为报告模块。

### 15.12 日志

- 运行日志：`data/logs/` 按日期轮转（保留 30 天）
- 策略日志：每次策略执行输入/输出（保留 7 天）
- 交易日志：每笔交易详情（永久保留）
- 审计日志：配置修改/下单操作（永久保留）

---

## 16. 原始代码 Bug 注册表

以下 Bug 已在源文件中确认，**新项目迁移时必须修复**：

### 16.1 CRITICAL（运行时崩溃）

| # | 文件 | 行 | 问题 | 修复方案 |
|---|------|----|------|----------|
| 1 | 楚风 `technical_indicators.py` | 49-56 | `_true_range()` 静态方法无限递归：当 `prev_close is None` 时调用自身不传参 | 静态方法委托给实例方法 `true_range()` |
| 2 | 听海 `signal_generator.py` | 1070 | `STRATEGY_MAP` 键名 `"Volume_Conform"` 少字母 `f`（应为 `Volume_Confirm`） | 修正拼写 |
| 3 | 听海 `correlation_analyzer.py` | 309,312,315 | `random.choice()` 不支持 `weights` 参数（这是 numpy 的 API） | 改为 `numpy.random.choice()` |
| 4 | `market_data_fetcher/tdx_fetcher.py` | 54-61 | 重复 `except ImportError`，第二个永远不可达；默认静默失败不报错 | 删除第二个 except，第一个改为打印警告 |
| 5 | 楚风 `strategy_engine.py` | 16 | `from regime_detector import MarketRegimeDetector` 裸导入，包上下文失效 | 改为相对导入 `.regime_detector` 或绝对导入 `core.regime_detector` |

### 16.2 HIGH（功能异常）

| # | 文件 | 行 | 问题 | 修复方案 |
|---|------|----|------|----------|
| 6 | 楚风 `strategies/layered_strategy_system.py` | 全局 | 硬编码 `sys.path.insert(0, '/root/.hermes/hte/')`，Windows 不可用 | 全部改为相对路径/配置驱动 |
| 7 | 楚风 `config/model_manager.py` | 25 | `CONFIG_PATH = '/root/.hermes/hte/config/model_config.yaml'` | 通过 `settings.py` 注入路径 |
| 8 | 楚风 `scripts/system_health_check.py` | 全局 | 硬编码 `/root/` 路径 | 配置化 |
| 9 | 听海 所有根模块 | 全局 | `DB_PATH = "/root/.openclaw/workspace/quant_system/futures.db"` | 集中到 `settings.py` |
| 10 | 听海 `bin/` 模块 | 全局 | `DB_PATH = "/data/quant_system/data/futures.db"`（与根模块不同路径） | 统一到 `settings.py` |
| 11 | 听海 `scanner.py` | 15 | `from strategy_engine import ResonanceEngine` — 但 `strategy_engine` 已无该类 | 改为从 `resonance_engine.py` 导入 |
| 12 | 听海 `backtest_final.py` | 9-10 | 导入不存在的模块属性 `STRATEGY_REGISTRY`、`CONTRACT_LIST` | 修正导入路径 |
| 13 | 听海 `data_adapter.py` | 174 | `FeishuNotifier.send()` 对字符串调用 `.get('code')`，永远返回 None | 先 `json.loads()` 解析响应 |
| 14 | 听海 `signal_generator.py` | 1344 | UPSERT `ON CONFLICT(contract,period)` 但 signals 表无对应唯一约束 | 添加唯一约束或改用 INSERT OR REPLACE |
| 15 | qzh-trading-main `ctp_feed.py` | 21-23 | CTP 账号密码硬编码（broker=9999, user=13718488065, password=Cn03103221!） | 移到 `.env` 文件 |
| 16 | qzh-trading-main `data_center.py` | 236-241 | `/api/data/unified/kline` 端点忽略 `get_kline()`，直接调 `get_akshare_futures_daily()` | 改为调用 `data_source_manager.get_kline()` |
| 17 | 楚风 `real_market_api.py` | 19 | `from core.real_time_data_fetcher import ...` 绝对路径在非根目录运行失败 | 改为相对导入 |

### 16.3 MEDIUM（代码质量/设计）

| # | 文件 | 行 | 问题 | 修复方案 |
|---|------|----|------|----------|
| 18 | 观山 `strategy_layered_scan.py` | 末尾 | 包含 `PYEOF` 死代码（文件结束标记后的无用内容） | 删除 |
| 19 | 观山 `walkforward.py` | 全局 | `__import__('pandas')` 动态导入反模式 | 改为 `import pandas as pd` |
| 20 | `market_data_fetcher/core/base.py` | 9-11 | `BaseFetcher` 是空类（`pass`），无抽象接口 | 添加 ABC + 抽象方法 |
| 21 | `market_data_fetcher/eia_cftc_fetcher.py` | 182-183 | 类间孤立重复导入 `BaseFetcher`、`cached` | 删除 |
| 22 | `market_data_fetcher/options_fetcher.py` | 769-770 | 同上 | 删除 |
| 23 | `market_data_fetcher/tdx_fetcher.py` | 685-686 | 同上 | 删除 |
| 24 | 听海 `signal_generator.py` | 1186 | `final_score` 先计算后被覆盖，死代码 | 删除冗余计算 |

### 16.4 修复优先级

迁移时按以下优先级修复：

1. **P0 (必须修复)**: Bug #1-5 (CRITICAL 级别) — 在实现对应模块时直接修复
2. **P1 (重要)**: Bug #6-17 (HIGH 级别) — 在 Phase 1-4 中逐个修复
3. **P2 (建议)**: Bug #18-24 (MEDIUM 级别) — 在代码 review 中统一处理

---

## 17. 升级迁移路径

### 17.1 从原始代码到新系统的迁移步骤

1. **数据迁移**：原始 DB 文件（SQLite）→ 新 PostgreSQL/SQLite
   - 使用 `db_manager.py` 的别名映射同步 schema
   - 数据验证后再导入（经过 DataQualityGuard）

2. **配置迁移**：原始 YAML/JSON 配置 → 新 ConfigManager 格式
   - 楚风 `strategy_params.yaml`（40+ 品种配置）保持格式兼容
   - 硬编码路径全部替换为 `${DATA_DIR}` / `${PROJECT_ROOT}` 变量

3. **策略迁移**：三套策略代码 → 统一 `@register` 框架
   - 每个策略封装为一个文件，继承 `BaseStrategy`
   - 复用现有计算逻辑，仅包装接口
   - 观山 `strategy_base.py` → `signals/base.py`
   - 楚风 `base_strategies.py` → `signals/strategies/trend/oscillation/`
   - 听海 `signal_generator.py` 33 策略 → 对应目录

4. **模型迁移**：听海预训练模型 → `models/` 目录
   - 参考模型结构，重训
   - 新模型版本注册到 `ModelVersion` 表

### 17.2 增量上线策略

```
Phase 1: 数据层上线（已有 data_source_manager 直接可用）
Phase 2: 策略引擎上线（原有策略逐渐接入）
Phase 3: 共振/交易上线（模拟盘运行）
Phase 4: 前端上线（可视化监控）
Phase 5: ML/锦标赛上线（进阶功能）
```

---

## 附录

### A. 依赖清单

**Python** (`requirements.txt`):
```
# Web
fastapi>=0.110
uvicorn[standard]
pydantic>=2.0
pydantic-settings>=2.0

# DB
sqlalchemy>=2.0
alembic
aiosqlite
asyncpg                          # PostgreSQL async driver
redis[hiredis]>=5.0

# 任务队列
celery>=5.3

# 数据处理
pandas>=2.0
numpy
scipy

# ML
scikit-learn
lightgbm>=4.0
xgboost>=2.0
hmmlearn
statsmodels
arch                              # GARCH

# 深度学习（可选）
torch>=2.0                        # LSTM

# 数据源
akshare>=1.14
yfinance>=0.2
easy-tdx                          # 通达信行情

# 通知
requests

# 工具
python-dotenv
websockets
httpx
pyyaml
loguru
apscheduler                       # 定时任务

# 测试
pytest
pytest-cov
pytest-asyncio
httpx
ruff
mypy
pip-audit
```

**Node.js** (`frontend/package.json`):
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "antd": "^5.12.0",
    "lightweight-charts": "^4.1.0",
    "axios": "^1.6.0",
    "dayjs": "^1.11.0",
    "zustand": "^4.4.0",
    "@ant-design/icons": "^5.2.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@types/react": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0"
  }
}
```

### B. 环境变量 (.env)

```bash
# 应用
APP_NAME=trading-strategy-center
APP_VERSION=1.0.0
LOG_LEVEL=info
SECRET_KEY=<random-256-bit>

# 数据库
DATABASE_URL=sqlite:///../data/futures.db
# DATABASE_URL=postgresql://tsc:password@db:5432/tsc
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0

# 数据源
DATA_CACHE_DIR=../data/cache
DATA_CACHE_TTL=3600

# API Keys (可选)
FRED_API_KEY=
EIA_API_KEY=
ALPHA_VANTAGE_API_KEY=
FMP_API_KEY=
TIINGO_API_KEY=
TAVILY_API_KEY=                   # 新闻情绪

# 模拟账户
SIM_INITIAL_CAPITAL=100000
SIM_COMMISSION_RATE=0.0005
SIM_SLIPPAGE=0.0001

# ML
MODEL_DIR=../models
RETRAIN_INTERVAL_DAYS=7

# 飞书（可选）
FEISHU_APP_ID=
FEISHU_APP_SECRET=
FEISHU_OPEN_ID=
```

### C. Git 忽略

```gitignore
__pycache__/
*.pyc
*.pyo
venv/
.env
*.egg-info/

data/*.db
data/cache/
data/backtest_results/
data/logs/

models/*.pkl
models/*.json
models/*.pt

node_modules/
frontend/dist/

.vscode/
.idea/
*.swp
*.swo

Thumbs.db
.DS_Store
```

### D. Makefile (常用命令)

```makefile
.PHONY: dev test lint db-migrate db-upgrade docker-up deploy

# 开发
dev:
	uvicorn backend.main:app --reload --port 8765

dev-frontend:
	cd frontend && npm run dev

# 测试
test:
	pytest tests/ -v --cov=backend

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# Lint
lint:
	ruff check backend/
	mypy backend/

# 数据库
db-migrate:
	alembic revision --autogenerate -m "$(msg)"

db-upgrade:
	alembic upgrade head

# Docker
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

# 部署
deploy:
	ssh ubuntu@$(HOST) "cd /opt/trading-strategy-center && docker-compose pull && docker-compose up -d"
