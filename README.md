# Trading Strategy Center · 交易策略中心

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-green.svg)
![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.4+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**数据驱动、自我迭代的量化交易研究与决策平台**

</div>

---

## 这是什么

一个全栈量化平台,核心是一个正反馈飞轮:

```
统一数据中心(期货/股票/期权/宏观/新闻)
   → 策略库(55) + Alpha101因子 + ML模型 + 缠论买卖点
   → 多 agent 委员会综合决策 → 交易信号(可模拟, 后续可实盘)
   → 锦标赛赛马 + walk-forward晋升 + 触发式重训
   → (更强的策略回流) → 弹药库越来越丰富, 信号越来越准
```

> 完整设计见 **[系统说明文档 docs/SYSTEM_OVERVIEW.md](./docs/SYSTEM_OVERVIEW.md)**

---

## 核心能力

- **统一数据中心** — DuckDB 真实合约仓库, 多周期(D1/M5/M15/M30/H1/H4/W1/M1), 多源容错(限流/黑名单自动切换), 按年全量同步 + 实时增量同步(服务端常驻, 重启自恢复)
- **多 agent 交易委员会** — 技术面/因子面/机器学习/缠论/宏观消息 五个 agent 各看一维度, 主席加权裁决, 可选 LLM 自然语言点评
- **ML 自我迭代闭环** — 锦标赛真实回测 → walk-forward 防过拟合晋升 → 触发式三层重训 → Champion/Challenger 人工安全闸门
- **55 策略 + Alpha101 因子 + 专业缠论** — 规则策略 + WorldQuant 101 因子 + 一/二/三买卖点/背驰
- **UMP 裁判机制** — 交易级 ML 否决闸门, 下单前拦截"长得像历史亏损单"的交易
- **新闻宏观仪表盘** — 中文财经快讯(情绪分析) + 宏观指标看板 + 事件日历 + 品种联动分析
- **模拟交易** — 从信号一键开仓, 实时盈亏, 全程 JSON 持久化
- **15 个 LLM 多 provider** — DeepSeek/OpenAI/Claude/通义/智谱/Groq/Ollama 等, 无 key 自动降级

---

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/wutongshanweng/trading-strategy-center.git
cd trading-strategy-center

# 2. 依赖
pip install -e .
cd frontend && npm install && cd ..

# 3. 配置 (复制后填入你的 key, 全部可选)
cp .env.example .env

# 4. 启动
python main.py                 # 后端 http://localhost:8000
cd frontend && npm run dev     # 前端 http://localhost:3000
```

打开 http://localhost:3000 即可。免费数据源(akshare/baostock/通达信)无需任何 key。

---

## LLM 配置 (可选, 开启 AI 点评)

```bash
# .env 中填入 (以 DeepSeek 为例)
DEEPSEEK_API_KEY=sk-你的key
DEFAULT_LLM_PROVIDER=deepseek
```
不配也能跑——LLM 功能自动降级为本地规则建议。支持 15 个 provider, 详见 `config/models.yaml`。

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.10+, FastAPI, asyncio |
| 数据 | DuckDB(行情/宏观) + SQLite/PostgreSQL(交易侧) |
| ML | scikit-learn, scipy, numpy, pandas, statsmodels, empyrical |
| 前端 | React 18 + TypeScript 5, Ant Design 5, Vite 5, Zustand |
| 数据源 | akshare/baostock/通达信(免费) + tushare/tqsdk(需key) |

---

## 主要页面

新闻宏观 · 模拟交易 · 锦标赛 · 智能中心 · 数据中心 · 策略军火库 · 因子研究 · ML+期权 · LLM配置

完整页面导览见 [系统说明文档](./docs/SYSTEM_OVERVIEW.md#四前端页面导览-菜单)。

---

## API

启动后访问 **http://localhost:8000/docs** 查看 FastAPI 自动生成的完整接口文档。
关键接口清单见 [系统说明文档](./docs/SYSTEM_OVERVIEW.md#五关键-api)。

---

## 测试

```bash
python -m pytest tests/ -q     # 全量约 1200 个测试
```

---

## 文档

- [系统说明文档](./docs/SYSTEM_OVERVIEW.md) — 完整架构、模块、API、配置、约束
- [架构设计](./ARCHITECTURE.md)
- [快速入门](./QUICK_START.md)
- [贡献指南](./CONTRIBUTING.md)

---

## 重要约束

1. DuckDB 单进程独占锁 — 行情仓库不可双进程打开
2. 数据源限流/黑名单是常态 — 已做多源容错 + 断点续传
3. 免费源分钟线只到近月(~6月), 历史分钟线需付费源
4. 自动迭代只做安全可逆操作, 晋升毕业/资金分配需人工批准

---

## 许可证

MIT License — 详见 [LICENSE](./LICENSE)。
内置 `vendor/chanpy/` 为 chan.py (MIT) 的 vendored 核心算法。

<div align="center">

**如果这个项目对你有帮助, 请给个 ⭐ Star!**

</div>
