# 交易策略中心 — 系统说明文档

> 版本: 0.1.0 | 更新: 2026-06-21
> 一个数据驱动、自我迭代的量化交易研究与决策平台。

---

## 一、系统是什么

交易策略中心是一个**全栈量化交易平台**,核心目标是形成一个正反馈飞轮:

```
统一数据中心(期货/股票/期权/宏观/新闻)
        │
        ▼
策略库(55) + Alpha101 因子 + ML 模型 + 缠论买卖点
        │
        ▼
多 agent 委员会综合决策 ──→ 交易信号(可模拟开仓, 后续可实盘)
        │
        ▼
策略锦标赛赛马 ──→ walk-forward 晋升闸门 ──→ 触发式重训
        │
        └──(更强的策略/参数回流)──┐
                                    ▼
                          弹药库越来越丰富, 信号越来越准
```

**设计哲学**:数据准 → agent 综合更可信 → 赛马迭代让策略库变强 → agent 又更强。每一环都有"防过拟合 + 人工安全闸门",不盲目自动化。

---

## 二、技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.10+, FastAPI, asyncio |
| 数据仓库 | DuckDB (行情/宏观, 列式), SQLite/PostgreSQL (交易侧表) |
| ML/量化 | scikit-learn, scipy, numpy, pandas, statsmodels, empyrical |
| 前端 | React 18 + TypeScript 5, Ant Design 5, Vite 5, Zustand |
| 图表 | lightweight-charts (TradingView) |
| LLM | 多 provider (DeepSeek/OpenAI/Claude/通义/智谱/Groq/Ollama 等 15 个), 无 key 自动降级 |
| 数据源 | akshare / baostock / 通达信(easy_tdx) (免费) + tushare/tqsdk (需 key) |

---

## 三、核心模块

### 1. 统一数据中心 (`data_center/`)
- **DuckDB 统一仓库**: 存真实合约 (RB2510, 非连续 RB0), 两层 products→symbols, 单一 kline 表按 (datetime, symbol_id, timeframe) 主键。
- **多周期**: D1 全年 + M5 近月直采 + 聚合 M15/M30/H1/H4 + W1/M1。
- **多源容错**: 单一数据源被限流/拉黑时自动切换 (如股票 baostock→akshare/sina)。
- **按年全量同步**: 期货/股票/期权各自独立开关, 生命周期守卫枚举真实合约, 断点续传。
- **实时增量同步**: 服务端常驻调度器, 关注品种持久化, 重启自恢复, 关网页不影响。

### 2. 信号与策略 (`signals/`, `core/alpha/`, `analysis/`)
- **55 个规则策略**: 趋势/动量/突破/均值回归/套利/反转/过滤 + 缠论买卖点 (chan_bsp)。
- **Alpha101 因子库**: 完整 WorldQuant 101 个公式化因子。
- **共振引擎** (`core/resonance/`): 多策略信号按 观山G/楚风C/听海T 分组加权投票。
- **专业缠论** (`analysis/chan_pro.py`): 移植自 chan.py (MIT), 一/二/三买卖点 + 盘整背驰 + 中枢。

### 3. 多 agent 交易委员会 (`signals/agents.py`)
五个 agent 各看一个维度, 主席加权裁决:

| Agent | 维度 | 数据来源 |
|-------|------|---------|
| 技术面 | 55策略+共振 | StrategyEngine + ResonanceEngineV2 |
| 因子面 | Alpha 因子 | FactorAdvisor |
| 机器学习 | 技术特征预测 | FeaturePipeline + MLSignalAdapter |
| 缠论 | 专业买卖点 | chan_pro 引擎 |
| 宏观消息 | 品种宏观倾向+新闻情绪 | RegimeAdapter + 新闻管道 |
| **主席** | 加权裁决+一致性评星 | 可选 LLM 自然语言点评 |

输出: 方向 (BUY/SELL/WATCH) + 综合净分 + 置信度 + 评星 + 每个 agent 的意见明细。

### 4. ML 自我迭代闭环 (`tournament/`, `core/adaptive/`)
四阶段, 每阶段都有防过拟合/人工闸门:
- **阶段1 锦标赛**: 对策略目录跑真实回测 → 反馈闭环回填表现 → 排名。
- **阶段2 晋升闸门**: walk-forward 样本外验证 + 过拟合检测, 按市态分组冠军。
- **阶段3 触发式重训**: 漂移触发的三层重训 (参数贝叶斯 / 因子衰减 / 模型 AutoML)。
- **阶段4 Champion/Challenger**: 新策略先考察 (challenger), 连续达标 + **人工批准**才毕业为 champion 获资金权重。

### 5. UMP 裁判机制 (`core/ump/`)
交易级 ML 否决闸门 (受 abu 启发, 独立实现): GMM 主裁标记历史高亏损形态簇 + 相似度边裁投票, 在下单前否决"长得像历史亏损单"的交易, 叠加在任意策略上。

### 6. 新闻宏观仪表盘 (`news/`, `macro/`)
- 财联社/东财多源容错快讯 + 中文情绪词典 + 个股舆情。
- 宏观指标看板 (CPI/PPI/PMI/GDP/M2/LPR, 查 DuckDB) + 规则化事件日历。
- 联动分析: 市态判断 + 品种影响 + 宏观↔品种关联度 + 远期展望。

### 7. 模拟交易 (`simulation/`)
持仓/历史/关注列表 JSON 持久化, 实时价 5 秒刷新, 从信号一键模拟开仓, 平仓记盈亏。

---

## 四、前端页面导览 (菜单)

| 菜单 | 路径 | 功能 |
|------|------|------|
| Dashboard | `/` | 总览看板 |
| 新闻宏观 | `/macro-news` | 快讯(hover看概述) + 宏观指标 + 事件日历 + 联动分析 + 右栏多agent交易信号(5分钟刷新) |
| 模拟交易 | `/trading` | 4 Tab: 持仓(5秒实时)/关注列表/挂单/历史成交 |
| 回测 | `/backtest` | 向量化回测 |
| 组合 | `/portfolio` | 组合管理 |
| 因子研究 | `/factors` | IC分析/分层回测/因子组合 |
| ML+期权 | `/phase3` | ML预测 + 期权深度分析 |
| 策略军火库 | `/strategy-library` | 55个内置策略按类型分组浏览 |
| 锦标赛 | `/tournament` | 跑真实回测 + 晋升验证 + Champion/Challenger 生命周期 |
| 智能中心 | `/iteration` | 迭代监控(参数演化/walk-forward窗口明细/重训历史) + 自动化开关 + ML模型 |
| 反馈闭环 | `/feedback` | 锦标赛→策略表现回填历史 |
| LLM配置 | `/llm-config` | 15个LLM提供商状态 + 策略建议 + 代码生成 |
| 数据中心 | `/data` | 按年全量同步 + 实时增量同步 + 数据校验 + 仓库预览 |
| 信号详情 | `/signal/:id` | 单信号全链路: 交易参数 + 多agent委员会裁决 + 各agent意见 + 宏观联动 + 风险提示 |

---

## 五、关键 API

```
# 数据中心
POST /api/v1/warehouse/sync/year?asset_type=&year=&with_minute=  # 按年全量同步(可含分钟线)
GET  /api/v1/warehouse/sync/year/verify?asset_type=&year=        # 数据质量校验
POST /api/v1/data-center/sync/add / start / stop / remove        # 实时增量同步(持久化+自恢复)

# 交易信号(多agent委员会)
GET  /api/v1/alerts                  # 当前活跃信号列表
GET  /api/v1/alerts/{id}             # 单信号全链路(含各agent意见)
POST /api/v1/alerts/refresh          # 手动触发委员会全扫描

# 锦标赛 / 自迭代
POST /api/v1/tournament/run-backtest # 真实回测→反馈→排名
POST /api/v1/tournament/promote      # walk-forward晋升验证
GET  /api/v1/tournament/lifecycle    # Champion/Challenger名单
POST /api/v1/tournament/graduate     # 人工批准毕业(安全闸门)
POST /api/v1/intelligence/retrain/cycle      # 触发式三层重训
GET/POST /api/v1/intelligence/automation/*   # 自动迭代配置/运行/日志
POST /api/v1/intelligence/ump/train          # 训练UMP裁判

# 新闻宏观
GET  /api/v1/macro-news/dashboard    # 全量聚合(新闻+宏观+日历+联动+展望)
GET  /api/v1/macro-news/guba         # 东财个股舆情

# LLM
GET  /api/v1/llm/providers           # 15个LLM提供商状态
POST /api/v1/llm/strategy/advise     # LLM策略建议(无key降级)
```

完整接口见 http://localhost:8000/docs (FastAPI 自动文档)。

---

## 六、配置 (含 LLM API Key)

所有密钥通过 `.env` 配置 (复制 `.env.example` 为 `.env`, 不提交 git)。

### LLM Key 配置 (开启 agent 主席 AI 点评 / 策略建议)
```bash
# .env 中填入 (以 DeepSeek 为例, 性价比最高、中文最好)
DEEPSEEK_API_KEY=sk-你的key
DEFAULT_LLM_PROVIDER=deepseek
```
- 支持 15 个 provider, 也可在 `config/models.yaml` 切换 `active_provider`。
- **无 key 时系统自动降级**为本地规则建议, 不影响运行。
- 多 agent 委员会的 LLM 点评默认关闭 (`use_llm=False`), 配 key 后可开启。

### 数据源 Key (可选)
- akshare / baostock / 通达信(easy_tdx): **免费, 无需 key, 默认启用**。
- tushare (深度历史/分钟线) / tqsdk (tick): 需注册 token, 填 `TUSHARE_TOKEN` / `TQ_ACCOUNT`。

---

## 七、运行

```bash
# 后端 (单进程, DuckDB 独占锁要求)
python main.py                       # http://localhost:8000

# 前端
cd frontend && npm run dev           # http://localhost:3000
```

启动后:
- 后台线程自动跑: 新闻刷新(30min) + 信号扫描(5min) + 自动迭代检查(每小时)
- 实时同步调度器: 若上次为运行态则**重启自动恢复**

---

## 八、重要约束与设计决策

1. **DuckDB 单进程独占锁**: 行情仓库只能一个进程打开, 全量采集与 API 共进程 (后台任务), 不可双进程。
2. **数据源现实**: 限流/黑名单/网络波动是常态, 所有外部拉取都有多源容错 + 超时 + 断点续传。
3. **分钟线限制**: 免费源(sina)只给近月(~6个月)分钟线, 历史分钟线需付费源。
4. **防过拟合优先**: 晋升用 walk-forward 样本外验证, 不用会"奖励亏钱策略"的 composite score。
5. **人工安全闸门**: 自动迭代只做安全可逆的事(回测+参数重优化), 晋升毕业/资金分配始终需人工批准。
6. **生产部署**: 用户完全通过页面操作即可完成同步/校验/信号/迭代全流程, 无需命令行。

---

## 九、测试

```bash
python -m pytest tests/ -q          # 全量约 1200 测试
```
单元测试覆盖: 策略/因子/共振/ML/RL/期权/缠论/UMP/委员会/锦标赛/自迭代/数据层。
