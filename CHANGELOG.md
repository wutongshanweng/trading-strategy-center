# 更新日志

所有重要的项目更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 2026-06-19 — 因子研究 Phase 2

#### 新增 (Added)
- **函数式算子集** (`core/alpha/mining/operator_set.py`): 21 个带参算子 (ts_rank/argmax/corr/rank_decay/scale 等) + 统一注册表入口。
- **因子健康检测** (`core/alpha/management/factor_decay.py`): 三态评级 HEALTHY/WARNING/DECAYED，基于 IC 趋势斜率 + 短中长期对比 + 分层单调性。
- **行业中性化** (`core/alpha/management/industry_neutral.py`): 均值/Z-score/回归/市场四法 + 行业暴露度量。
- **全因子研究报告** (`core/alpha/management/report_generator.py`): 排名 + 冗余检测 + 低相关推荐组合 + HTML/JSON/控制台输出。
- **因子 API** `/api/factor/{mine,health-check,report,neutralize}`: 复用既有遗传引擎 GeneticProgramming/FactorAnalyzer，全部接 DuckDB 真实仓库数据 (无数据回退 mock)。
- **前端因子研究页**新增三个 tab: 因子挖掘 / 健康监控 / 研究报告。

#### 说明
- 遗传挖掘引擎 (GeneticProgramming/FitnessFunction/FactorSynthesizer) 与 IC/分层分析 (FactorAnalyzer) 本仓库已有，本期为扩充+适配，未重复实现。


### 2026-06-19 — 数据中心深度升级

#### 新增 (Added)
- **合约生命周期模块** (`contract_lifecycle.py`): 期货/期权统一的到期日解析、合约状态（在挂/已到期/连续）、有效数据窗口；入库守卫自动裁剪生命周期外脏数据。
- **按年同步面板** (实时同步 tab): 一年一行倒序，期货/股票/期权三列，每格含状态(未同步/已同步/同步中)+数量+同步/校验按钮；整合全量历史同步与实时增量同步。
- **商品期权按年逐日全量采集** (`collect_commodity_year`): 遍历交易日 × DCE/CZCE/SHFE 全品种，落 K线 + 交易所直供 IV/Delta；支持三种合约代码格式（连字符/3位年月/4位年月）。
- **商品期权 Greeks** (`options_analytics.py`): akshare 不提供时用 Black76 反解 IV + 全套希腊值。
- **股票知识库** (`stock_knowledge.py`): 申万行业板块 + 行业↔期货联动映射。
- **期权知识库** (`options_knowledge.py`): 标的市场特征 + 期权策略库。
- **合约知识库扩充**: ContractDetail 增加宏观敏感度/季节性/核心指标/关联品种结构化字段。
- **股票基本面落库**: 个股信息 + 财务摘要写入 stocks_info/stocks_financial。
- **股票全市场全量下载 + 增量同步**: 从上市日起全历史 + last_synced 跟踪只拉落后的票。
- **存储管理**: 单文件删除 + 导出 xlsx；存储列表聚合期货/股票/期权三类。
- **数据中心概览**: 8 个统计卡片（含股票/期权品种数、K线总条数、数据库物理大小）。
- **新增 API**: `/warehouse/sync/year-status`、`/sync/year`、`/sync/year/verify`、`/db-size`、`/contracts/status`、`/stocks/*`、`/options/knowledge` 等。

#### 修复 (Fixed)
- 股票日线下载报“日期范围最大3年”（前端请求5年 vs 后端限3年不一致，放宽日线上限至30年）。
- 期权获取合约列表返回序号而非真实代码（akshare 列名取错，改为优先 `期权代码`）。
- M2609 误存主力连续 2005 年数据（生命周期守卫裁剪窗口外数据）。
- 收盘价走势图曲线不跟随价格（`yAt(i)`→`yAt(v)` 变量笔误）+ 图表高度。
- 多个仓库端点 NaN→500 JSON 序列化错误（系统性提取 `_clean_json`/`_records`）。
- cross_market 主力代表选取在换月期偏差（优先 main_contracts 标记）。
- 股票代码支持无后缀输入（600019 → 600019.SH 归一化）。


## [0.1.0] - 2026-06-14

### 新增 (Added)

#### 核心系统
- **Alpha因子系统**: 完整实现101个WorldQuant Alpha因子
- **因子计算管线**: 支持并行计算，8核性能优化
- **因子管理系统**: 筛选、评估、组合优化
- **遗传编程引擎**: 自动因子挖掘和优化

#### 强化学习
- **Deep RL网络**: DQN, GaussianActor, TwinCritic
- **训练算法**: DQN, SAC, TD3, DDPG完整实现
- **多智能体RL**: MADDPG协作/竞争训练
- **离线RL**: CQL + 历史数据集训练

#### 风险管理
- **风险度量**: VaR, CVaR实时计算
- **压力测试**: 历史情景和蒙特卡洛模拟
- **仓位管理**: Kelly公式, 波动率目标, 状态感知
- **绩效归因**: Brinson模型 + 多维度归因

#### 期权交易
- **定价引擎**: Black-Scholes, Black76, Binomial Tree
- **Greeks计算**: 解析法和数值法，支持组合聚合
- **隐含波动率**: Newton-Raphson求解器
- **波动率分析**: SVI曲面拟合, 波动率锥, IV Rank
- **期权策略**: 方向性、波动率、价差策略框架

#### 策略系统 (57+个策略)
- **趋势策略**: MA Cross, MACD, SuperTrend, KAMA, Ichimoku, ADX, DMI, Aroon等
- **均值回复**: Bollinger, Z-Score, OU Process, Cointegration等
- **动量策略**: Time Series Momentum, Dual Momentum, Vol-Adjusted等
- **突破策略**: Donchian, New High/Low, Volume Breakout等
- **套利策略**: Calendar Spread, Pair Trading, Basis, Crack/Crush Spread等

#### 期货增强功能
- **连续合约**: 支持前复权/后复权/不复权三种模式
- **换月逻辑**: 持仓量/成交量/时间三种换月规则
- **Roll Yield**: 展期收益率计算和期限结构分析
- **基差分析**: 期现价差监控和套利信号

#### 时序模型
- **TFT模型**: Temporal Fusion Transformer，多视野预测+可解释性
- **N-BEATS模型**: 纯神经网络时序预测，无需特征工程

#### 研究环境
- **Jupyter集成**: 完整的研究笔记本环境
- **因子研究工具**: IC/IR计算, 分层回测, 因子衰减分析
- **可视化工具**: matplotlib, seaborn, plotly集成

#### 数据层
- **MarketDataManager**: 统一数据入口，支持16类数据源
- **二级缓存**: LRU内存缓存 + Redis分布式缓存
- **数据质量护栏**: 6道质量检查，自动修复
- **熔断降级**: 数据源故障自动切换

#### 回测引擎
- **向量化回测**: 秒级回测，支持多年日线数据
- **阈值优化**: Grid search + Walk-forward验证
- **完整指标**: Sharpe, Calmar, Win Rate, Profit Factor等30+指标

#### API基础设施
- **REST API**: 11个路由模块，完整的CRUD操作
- **WebSocket**: 实时推送（行情/信号/持仓/PnL/告警）
- **异步任务**: Celery + Redis任务队列
- **LLM集成**: DeepSeek/OpenAI/Claude多模型支持

#### 前端
- **React 18**: 现代化单页应用
- **Ant Design 5**: 企业级UI组件
- **TradingView Charts**: 专业K线图表
- **实时更新**: WebSocket自动推送

### 改进 (Changed)
- Alpha因子从原有基础实现迁移到完整的WorldQuant公式
- 策略系统从15个扩展到57+个
- 测试覆盖从基础测试扩展到981个完整测试用例

### 修复 (Fixed)
- 修复数据缓存的并发问题
- 优化因子计算的内存使用
- 改进WebSocket连接稳定性

### 性能优化 (Performance)
- 因子并行计算性能提升3倍（8核并行）
- 向量化回测速度提升5倍
- 缓存命中率优化到80%+

## [0.0.1] - 初始版本

### 新增
- 项目基础架构搭建
- 基础数据获取功能
- 简单策略框架

---

## 版本说明

### 版本号规则
- **MAJOR.MINOR.PATCH** (例: 1.2.3)
- **MAJOR**: 不兼容的API更改
- **MINOR**: 向后兼容的新功能
- **PATCH**: 向后兼容的Bug修复

### 标签说明
- **新增 (Added)**: 新功能
- **改进 (Changed)**: 现有功能的改进
- **弃用 (Deprecated)**: 即将移除的功能
- **移除 (Removed)**: 已移除的功能
- **修复 (Fixed)**: Bug修复
- **安全 (Security)**: 安全性修复

---

## 未来计划 (Roadmap)

### v0.2.0 (计划中)
- [ ] 事件驱动回测引擎
- [ ] 实盘CTP接口接入
- [ ] 策略自动优化系统
- [ ] Grafana监控看板

### v0.3.0 (计划中)
- [ ] 股票市场支持
- [ ] 高频交易策略
- [ ] 机器学习自动调参
- [ ] 策略市场平台

### v1.0.0 (长期)
- [ ] 完整的实盘交易系统
- [ ] 多市场支持（加密货币等）
- [ ] SaaS化部署
- [ ] 移动端App

---

**[Unreleased]**: https://github.com/your-repo/compare/v0.1.0...HEAD
**[0.1.0]**: https://github.com/your-repo/releases/tag/v0.1.0
