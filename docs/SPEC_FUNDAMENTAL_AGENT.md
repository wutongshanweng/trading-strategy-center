# SPEC: 基本面 Agent — 库存 × 成本链 × 季节性 × 需求 四维分析

> **开发人员：** Claude Code
> **仓库地址：** https://github.com/wutongshanweng/trading-strategy-center
> **分支：** main
> **安装依赖：** `pip install akshare pandas numpy loguru duckdb`
> **实现状态：** ✅ **已完成**（2026-06-24）

---

## 实现状态

| 章节 | 状态 | 文件 |
|:-----|:----:|:-----|
| 一、背景与现状 | ✅ | 系统已有资产确认 |
| 二、四维打分体系 | ✅ | `analysis/fundamental/model.py` |
| 三、文件清单 | ✅ | 6个新增文件 + 3个修改 |
| 四、核心实现 | ✅ | `inventory.py`, `cost_chain.py`, `seasonality.py`, `demand.py` |
| 五、委员会集成 | ✅ | `signals/agents.py` (fundamental 权重 0.25) |
| 六、API 端点 | ✅ | `api/routes/fundamental_routes.py` (4个端点) |
| 七、前端卡片 | ✅ | `frontend/src/pages/SignalDetail.tsx` |
| 八、单元测试 | ✅ | `tests/unit/test_fundamental_agent.py` (25/25 passed) |

---

## 一、背景与现状

### 系统已有基本面相关资产

| 资产 | 状态 | 说明 |
|:-----|:----:|:------|
| `fundamental/fundamental_analyzer.py` | ✅ 已有 | 基差计算 + 持有成本 + 公允价格（壳子，无数据源，无产业链分析） |
| `macro/aggregator.py` | ✅ 已有 | 宏观指标聚合（CPI/PPI/PMI/GDP/M2/LPR） |
| `macro/regime_adapter.py` | ✅ 已有 | 宏观→市态判断（趋势/震荡/高风险） |
| `news/fetchers/cls.py` | ✅ 已有 | 财联社快讯采集 |
| `core/config/watchlist.py` | ⚠️ 计划中 | 品种→关键词/关联表 |
| `wencai` 包 | 需安装 | 问财自然语言查询，用于搜库存/资金流向/行业数据 |

### 现有的多 Agent 委员会结构

已实现 5 个 agent（见 `api/routes/agent_routes.py` 或 `core/committee/`）：

```
委员会评判
├── 技术面 agent (权重30%) → StrategyEngine + ResonanceEngineV2
├── 因子面 agent (权重20%) → FactorAdvisor
├── 机器学习 agent (权重20%) → FeaturePipeline + MLSignalAdapter
├── 缠论 agent (权重15%)   → analysis/chan_pro (try/except 安全降级)
└── 宏观消息 agent (权重15%) → 新闻情绪 + 品种关联
```

**本 Spec 目标：新增第 6 个 agent — 基本面 agent（权重 20%），同时更新权重分配。**

---

## 二、基本面 Agent 整体设计

### 四维打分体系

```
基本面 agent
├── 📦 库存维度 (权重25%)  → 社会库存/仓单/企业库存  → 按品种查
├── ⛓️ 成本链维度 (权重25%) → 上游原料价格走势       → 品种映射表
├── 📅 季节性维度 (权重20%) → 近5年同月涨跌统计       → 历史回算
└── 🏭 需求端维度 (权重30%) → 下游开工/地产/宏观指标  → akshare + 映射表

每维度输出 ∈ [-1, +1]
综合得分 = 加权平均 ∈ [-1, +1]
```

### 与委员会对接

```python
# 委员会配置（在 signals/agents.py 中实现）
AGENT_WEIGHTS = {
    "technical":   0.25,  # 技术面 agent
    "factor":      0.10,  # 因子面 agent
    "ml":          0.15,  # 机器学习 agent
    "chan":        0.10,  # 缠论 agent
    "macro":       0.10,  # 宏观消息 agent
    "fundamental": 0.25,  # ✅ 基本面 agent（与技术面对等权重）
}
```

> **实现说明：** `signals/agents.py` 中的 `TradingCommittee` 已包含 `_agent_fundamental` 属性，通过 `analyze_fundamental()` 函数接入。

## 三、文件清单

### 新增文件 ✅

| 文件 | 状态 | 内容 |
|:-----|:----:|:------|
| `analysis/fundamental/__init__.py` | ✅ | 模块导出 |
| `analysis/fundamental/model.py` | ✅ | **基本面 agent 核心**：四维打分引擎 + 品种映射表 + 综合评分 |
| `analysis/fundamental/inventory.py` | ✅ | **库存采集器**：akshare + 静态种子数据 |
| `analysis/fundamental/cost_chain.py` | ✅ | **成本链映射**：品种→上游原料 + 期货价格采集 |
| `analysis/fundamental/seasonality.py` | ✅ | **季节性分析**：DuckDB 历史回算 |
| `analysis/fundamental/demand.py` | ✅ | **需求端指标**：akshare 宏观数据 + 静态种子 |
| `analysis/fundamental/product_map.py` | ✅ | **品种基本面映射表**：26 个品种 |
| `frontend/src/services/fundamentalApi.ts` | ✅ | 前端 API service |
| `tests/unit/test_fundamental_agent.py` | ✅ | 单元测试 (25/25 passed) |

### 修改文件 ✅

| 文件 | 改动 |
|:-----|:------|
| `signals/agents.py` | ✅ 新增 `fundamental` agent，权重 0.25 |
| `api/routes/fundamental_routes.py` | ✅ 新增 4 个 API 端点 |
| `frontend/src/pages/SignalDetail.tsx` | ✅ 新增基本面四维分析卡片 |

---

## 四、核心实现 — `analysis/fundamental/model.py`

### 数据类

```python
@dataclass
class FundamentalScore:
    """一个品种的基本面四维评分"""
    symbol: str                    # RB2510
    product_name: str              # 中文品名
    inventory_score: float = 0.0   # [-1,+1]   +1=库存极低(利多)
    cost_score: float = 0.0        # [-1,+1]   +1=成本上升(利多)
    seasonal_score: float = 0.0    # [-1,+1]   +1=历史上涨月(利多)
    demand_score: float = 0.0      # [-1,+1]   +1=需求旺盛(利多)
    combined: float = 0.0          # 加权综合
    detail: str = ""               # 自然语言解释
    data_quality: str = "medium"   # high/medium/low（数据源可信度）
```

### 品种基本面映射表（硬编码配置）

核心配置，定义每个品种的库存源、上游原料、需求指标：

```python
PRODUCT_FUNDAMENTALS = {
    "FG": {  # 玻璃
        "name": "平板玻璃",
        "exchange": "郑商所",
        "inventory_source": "隆众资讯/玻璃社会库存",
        "cost_chain": [{"原料": "纯碱", "占比": 0.25}, {"原料": "天然气", "占比": 0.20}],
        "demand_indicators": ["房地产竣工面积", "汽车产量", "光伏玻璃"],
        "season_months": {"bullish": [3, 4, 9, 10], "bearish": [1, 6, 7, 8]},
    },
    "RB": {  # 螺纹钢
        "name": "螺纹钢",
        "exchange": "上期所",
        "inventory_source": "Mysteel/螺纹钢社会库存",
        "cost_chain": [{"原料": "铁矿石", "占比": 0.40}, {"原料": "焦炭", "占比": 0.25}],
        "demand_indicators": ["房地产开发投资", "基建投资", "商品房销售面积"],
        "season_months": {"bullish": [3, 4, 9, 11], "bearish": [1, 6, 7, 12]},
    },
    "ZC": {  # 纯碱
        "name": "纯碱",
        "exchange": "郑商所",
        "inventory_source": "隆众资讯/纯碱企业库存",
        "cost_chain": [{"原料": "原盐", "占比": 0.15}, {"原料": "煤炭", "占比": 0.30}],
        "demand_indicators": ["平板玻璃产量", "光伏玻璃产能", "碳酸锂产量"],
        "season_months": {"bullish": [3, 8, 9, 10], "bearish": [1, 5, 6, 11]},
    },
    "CU": {  # 铜
        "name": "电解铜",
        "exchange": "上期所",
        "inventory_source": "SHFE铜库存/保税区库存",
        "cost_chain": [{"原料": "铜精矿TC", "占比": 0.70}, {"原料": "废铜", "占比": 0.15}],
        "demand_indicators": ["电网投资", "新能源汽车产量", "空调产量", "全球PMI"],
        "season_months": {"bullish": [1, 2, 7, 12], "bearish": [3, 5, 10, 11]},
    },
    "I": {  # 铁矿石
        "name": "铁矿石",
        "exchange": "大商所",
        "inventory_source": "Mysteel/港口铁矿石库存",
        "cost_chain": [{"原料": "海运费(西澳→青岛)", "占比": 0.10}],
        "demand_indicators": ["粗钢产量", "高炉开工率", "生铁产量"],
        "season_months": {"bullish": [1, 11, 12], "bearish": [3, 6, 7, 8]},
    },
    "MA": {  # 甲醇
        "name": "甲醇",
        "exchange": "郑商所",
        "inventory_source": "隆众资讯/甲醇港口库存",
        "cost_chain": [{"原料": "煤炭", "占比": 0.45}, {"原料": "天然气", "占比": 0.25}],
        "demand_indicators": ["甲醇开工率", "MTO开工率", "甲醛/醋酸产量"],
        "season_months": {"bullish": [9, 10, 11], "bearish": [5, 6, 7]},
    },
    "SA": {  # 纯碱 (同 ZC, 不同代码)
        "name": "纯碱",
        "exchange": "郑商所",
        "inventory_source": "隆众资讯/纯碱企业库存",
        "cost_chain": [{"原料": "原盐", "占比": 0.15}, {"原料": "煤炭", "占比": 0.30}],
        "demand_indicators": ["平板玻璃产量", "光伏玻璃产能", "碳酸锂产量"],
        "season_months": {"bullish": [3, 8, 9, 10], "bearish": [1, 5, 6, 11]},
    },
    # ... 可扩展更多品种
}
```

### 核心类

```python
class FundamentalAgent:
    """基本面 agent — 四维基本面评分"""

    def __init__(self):
        self.inventory = InventoryAnalyzer()       # 库存采集
        self.cost = CostChainAnalyzer()            # 成本链分析
        self.season = SeasonalityAnalyzer()        # 季节性分析
        self.demand = DemandAnalyzer()             # 需求端分析
        self.carry = FundamentalAnalyzer()         # 复用已有的基差计算

    def analyze(self, symbol: str) -> FundamentalScore:
        """对一个品种执行四维基本面评分"""
        ...

    def analyze_batch(self, symbols: List[str]) -> Dict[str, FundamentalScore]:
        """批量分析多个品种"""
        ...
```

**各维度打分逻辑：**

#### 1. 库存维度 `inventory.py`

```python
class InventoryAnalyzer:
    def score(self, symbol_prefix: str) -> tuple[float, str, str]:
        """
        返回: (score, detail, data_quality)
        score: +1=库存极低(利多) → 0=中性 → -1=库存极高(利空)

        采集顺序（容错降级）:
          try 问财搜索 "XX 社会库存 最新"
          except -> 静态种子数据（每周手动更新兜底）
        """
```

**打分参考：**
- 库存 5 年百分位 >80% → -0.7 到 -1.0（利空）
- 库存 5 年百分位 <20% → +0.7 到 +1.0（利多）
- 库存趋势连续 3 月上升 → 额外 -0.2
- 库存趋势连续 3 月下降 → 额外 +0.2

#### 2. 成本链维度 `cost_chain.py`

```python
class CostChainAnalyzer:
    def score(self, symbol_prefix: str) -> tuple[float, str, str]:
        """
        通过品种映射表查上游原料，获取原料价格走势。
        原料集体上涨 → 成本推升型利多
        原料集体下跌 → 成本塌陷型利空

        例: 玻璃(FG) → 查纯碱(SA) + 天然气价格
            纯碱(SA) → 查原盐 + 煤炭价格
            螺纹(RB) → 查铁矿石(I) + 焦炭(J)
        """
```

**打分参考：**
- 成本较上月 +5% → +0.3 偏多
- 成本较上月 -5% → -0.3 偏多
- 结合期货利润（期货价 - 成本估算），利润过高时即使成本涨也偏空

#### 3. 季节性维度 `seasonality.py`

```python
class SeasonalityAnalyzer:
    def __init__(self, years: int = 5):
        self.years = years  # 回看年数

    def score(self, symbol_prefix: str) -> tuple[float, str, str]:
        """
        查品种映射表 season_months，确定当前月份历史胜率。

        分析已有行情数据:
        for year in last N years:
            pct = (当月收盘 - 上月收盘) / 上月收盘
        输出当前月份历史平均涨跌幅 + 胜率
        """
```

**打分参考：**
- 历史胜率 > 60% 且平均涨幅 > 2% → +0.5
- 历史胜率 < 40% 且平均跌幅 > 2% → -0.5
- 否则按线性插值

#### 4. 需求端维度 `demand.py`

```python
class DemandAnalyzer:
    def score(self, symbol_prefix: str) -> tuple[float, str, str]:
        """
        从品种映射表 demand_indicators 读取需求端指标。
        通过 akshare 获取最新宏观/行业数据。
        各指标同比变化综合判断。

        例: 玻璃(FG) → 房地产竣工面积同比
            螺纹(RB) → 房地产开发投资同比 + 基建投资
            铜(CU)   → 电网投资 + 新能源汽车产量
        """
```

**数据源：**
- `akshare.tool_cx_supply_demand()` — 产业供需数据
- `akshare.energy_oil_hist()` — 原油等能源价格
- `akshare.macro_china_gdp()` — GDP、工业增加值
- 问财搜 "螺纹钢 下游 需求 开工率" 等

**打分参考：**
- 需求指标同比 +10% → +0.5
- 需求指标同比 -10% → -0.5
- 多个指标取均值

---

## 五、委员会集成

### 在委员会主文件（`api/routes/agent_routes.py` 或 `core/committee/__init__.py`）中添加

```python
def _agent_fundamental(symbol: str) -> Dict:
    """基本面 agent — 四维基本面评分"""
    from analysis.fundamental.model import FundamentalAgent
    try:
        agent = FundamentalAgent()
        score = agent.analyze(symbol)
        return {
            "score": score.combined,
            "direction": "BUY" if score.combined > 0.15 else "SELL" if score.combined < -0.15 else "HOLD",
            "confidence": abs(score.combined),
            "detail": {
                "inventory": round(score.inventory_score, 3),
                "cost": round(score.cost_score, 3),
                "seasonal": round(score.seasonal_score, 3),
                "demand": round(score.demand_score, 3),
                "explanation": score.detail,
                "data_quality": score.data_quality,
            }
        }
    except Exception as e:
        logger.warning(f"基本面 agent 失败({symbol}): {e}")
        return {"score": 0.0, "direction": "HOLD", "confidence": 0.0,
                "detail": {"error": str(e), "explanation": "基本面分析暂不可用"}}
```

### 前端 SignalDetail 页新增「基本面」卡片

参照现有的 ML预测 / 期权分析 / 宏观联动卡片样式，在 `frontend/src/pages/SignalDetail.tsx` 中新增：

```
📊 基本面分析
├── 📦 库存: +0.65 (库存低位，连续2月下降)
├── ⛓️ 成本: -0.30 (纯碱价格持续走弱)
├── 📅 季节: +0.50 (9月历史上涨概率70%)
├── 🏭 需求: -0.10 (地产竣工同比-8%)
└── 🎯 综合得分: +0.19 → 偏多
```

---

## 六、API 端点

```python
# api/routes/fundamental_routes.py

GET /api/v1/fundamental/{symbol}
  → 返回四维评分 + 综合得分 + 解释文本

POST /api/v1/fundamental/batch
  {"symbols": ["FG2609", "RB2510", "SA409"]}
  → 返回各品种评分

GET /api/v1/fundamental/product-map
  → 返回所有品种的基本面映射配置

GET /api/v1/fundamental/{symbol}/detail
  → 返回详细数据（库存值/成本链价格/季节性统计/需求指标值）
```

注册到 `main.py`：

```python
from api.routes.fundamental_routes import router as fundamental_router
app.include_router(fundamental_router)
```

---

## 七、安装与环境

```bash
# 仓库根目录执行
pip install wencai akshare pandas numpy loguru

# 验证
python -c "from wencai import search; print('wencai OK')"
python -c "import akshare as ak; print('akshare OK')"
```

### 环境变量（无需额外配置）

- wencai：无 API key 要求，免费使用（有调用频次限制，建议每秒不超过 2 次）
- akshare：纯免费，无认证要求
- 问财使用受同花顺服务条款约束，不建议生产环境高频调用

---

## 八、早报 Skill 参考

日常早报（`daily-morning-briefing` skill）中搜索的新闻源可作为基本面 agent 的补充信息来源。参考早报中从财联社、金十数据获取的产业新闻，将快讯中的**库存变化/开工率/政策消息**解析为基本面信号。

具体对接点：
```
早报采集的财联社快讯 → 筛选含"库存""开工""产量"等关键词的快讯
                      → 关联品种
                      → 输入基本面 agent 的需求/库存维度
```

---

## 九、验收标准 ✅

| # | 标准 | 状态 |
|:-:|:-----|:----:|
| 1 | 对 FG2609 调用基本面 agent，返回四维评分 + 综合得分 + 解释文本，无报错 | ✅ |
| 2 | 按权重 25% 接入委员会，委员会输出附带基本面理由 | ✅ |
| 3 | 品种映射表覆盖至少 6 个品种（FG/RB/ZC-CU/I/MA），数据合理 | ✅ (26品种) |
| 4 | 每个维度有 try/except 容错，单个维度失败不影响其他维度评分 | ✅ |
| 5 | akshare 连接失败时自动降级使用种子数据，不崩溃 | ✅ |
| 6 | API 端点 `/api/v1/fundamental/{symbol}` 返回 JSON 格式正确 | ✅ |
| 7 | 单元测试覆盖：模型打分逻辑、映射表完整性、容错降级 | ✅ (25 tests) |
| 8 | 全量测试通过，前端 tsc 无错误 | ✅ |

---

## 十、技术亮点

### 数据源分层降级

```
akshare (免费实时) → 静态种子数据 (兜底)
      ↓                    ↓
  数据质量: high       数据质量: medium/low
```

### DuckDB 季节性回算

- 利用现有 OHLCV 历史数据，无需额外下载
- 快速聚合计算近5年同月涨跌统计

### 品种映射扩展性

- `PRODUCT_FUNDAMENTALS` 字典式配置，新增品种只需添加一个字典
- 已覆盖 26 个国内商品期货品种

### 委员会投票机制

- 6 个 agent 加权投票，fundamental 与 technical 对等权重 (各 25%)
- 单个 agent 失败自动降级，不影响整体判断

---

## 十一、依赖风险

| 风险 | 缓解方案 |
|:-----|:---------|
| akshare 接口变更 | 包装层隔离，变更只改一个文件；失败降级种子数据 |
| 品种映射表覆盖不全 | `PRODUCT_FUNDAMENTALS` 预留扩展接口，随时加 |
| 季节性数据依赖历史 | 使用系统已有 OHLCV 数据回算，不额外下载 |
| 外部数据源不可用 | 全部三层降级：实时 → 种子 → 中性默认值 |

---

## 十二、运行说明

```bash
# 安装依赖
pip install akshare pandas numpy loguru duckdb

# 验证模块
python -c "from analysis.fundamental import FundamentalAgent; a=FundamentalAgent(); print(a.analyze('RB2510').combined)"

# 运行单元测试
python -m pytest tests/unit/test_fundamental_agent.py -v

# 启动后端
python main.py

# 访问 API
GET http://localhost:8000/api/v1/fundamental/RB2510
```

| 风险 | 缓解方案 |
|:-----|:---------|
| 问财接口变动 | 每个查询 try/except，失败降级到种子数据 |
| akshare 接口变更 | 包装层隔离，变更只改一个文件 |
| 季节性数据依赖行情历史 | 使用系统中已有的 OHLCV 数据回算，不额外下载 |
| 映射表覆盖不全 | 预留 `PRODUCT_FUNDAMENTALS` 扩展接口，随时加 |
