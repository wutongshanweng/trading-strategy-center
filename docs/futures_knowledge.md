# 知识库升级方案

## 一、现状评估

当前系统有四个模块：

| 模块 | 内容 | 形态 |
|------|------|------|
| `futures_knowledge.py` | 品种百科全书（60+品种的波动特点/关联/警告） | 静态结构化数据 |
| `indicators.py` | K线技术指标（RSI/MACD/KDJ/布林/ATR/ADX等） | 纯函数计算 |
| `data.py` | easy_tdx 数据获取 + 主连合约 + 交易时段 | 数据层 |
| `contract_resolver.py` | 主力合约识别（规则+实时双引擎） | 推理层 |

**核心 gap**：知识库只有「品种描述」，没有「可投票的信号层」和「跨维度关联推理」。

---

## 二、升级方案总架构

```
knowledge/                          # 知识库根目录
├── futures_knowledge.py            # 🟢 已有，升级
├── stock_knowledge.py              # 🆕 股票知识库
├── macro_knowledge.py              # 🆕 宏观知识库
├── correlation_matrix.py           # 🆕 关联矩阵（品种×品种 + 品种×宏观）
├── event_calendar.py               # 🆕 数据发布日历 + 事件影响库
├── seasonal_patterns.py            # 🆕 季节性规律库
├── sentiment_signals.py            # 🆕 情绪信号（持仓/成交/期限结构）
└── scoring_engine.py               # 🆕 投票评分引擎（核心！）
```

---

## 三、合约知识库升级建议

在现有 `ProductInfo` 基础上增加字段，让每个品种**可评分**：

```python
@dataclass
class ProductInfo:
    # ... 现有字段保留 ...

    # 🆕 新增字段
    macro_sensitivity: dict[str, float]  # 宏观敏感度
    # 如 {"PMI": 0.8, "CPI": 0.3, "社融": 0.6, "美元指数": 0.9}
    # → 铜对PMI敏感0.8，黄金对美元指数敏感0.9

    seasonality: list[dict]        # 季节性规律结构化
    # [{"month": 3, "direction": "涨", "strength": 0.7, "reason": "金三银四"},
    #  {"month": 9, "direction": "涨", "strength": 0.6, "reason": "金九银十"}]

    data_releases: list[str]       # 关注的数据发布
    # 如 ["每周四钢联数据", "每月USDA报告", "MPOB月报"]

    key_indicators: dict[str, str] # 核心基本面指标
    # 如 {"库存": "港口库存+钢厂库存", "开工率": "高炉开工率",
    #      "焦化利润": "焦炭-焦煤价差"}
```

**升级后对比**：

| 维度 | 当前 | 升级后 |
|------|------|--------|
| 品种特点 | ✅ 有文本描述 | ✅ 结构化 + 可量化 |
| 宏观关联 | ❌ 无 | ✅ 可计算敏感度权重 |
| 季节性 | ❌ 隐含在文本 | ✅ 结构化，可用于seasonal trade |
| 基本面指标 | ❌ 无 | ✅ 定义清楚，可对接数据源 |
| 数据日历 | ❌ 无 | ✅ agent可提前研判 |

---

## 四、股票知识库方案

```python
# stock_knowledge.py

@dataclass
class SectorInfo:
    """行业板块知识"""
    code: str              # 申万行业代码
    name: str              # 行业名
    index_code: str        # 对应指数，如 '801030.SI'
    chars: list[str]       # 波动特点
    related_futures: list[str]  # 关联期货品种
    # 如 钢铁→RB/I/J, 有色→CU/AL/NI, 化工→MA/TA/L
    macro_sensitivity: dict[str, float]
    seasonality: list[dict]

@dataclass
class StockFuturesRelation:
    """股票-期货联动关系"""
    sector: str            # 行业
    futures_symbol: str    # 关联期货代码
    correlation: float     # 历史相关性
    lead_lag: str          # "期货领先" / "股票领先" / "同步"
    logic: str             # 联动逻辑描述
    # 示例：钢铁板块 → RB.I.J
    #   钢铁股通常滞后于期货1-3天
    #   期货夜盘走势→次日钢铁板块开盘方向
```

**核心场景**：

| 场景 | 举例 |
|------|------|
| 期货夜盘大涨 → 次日A股哪个板块受益？ | 铁矿夜盘大涨 → 钢铁/有色板块 |
| A股某个板块暴涨 → 期货端有无套利机会？ | 光伏板块暴涨 → 纯碱/白银联动 |
| 宏观数据发布 → 影响哪些股票行业？ | PMI超预期 → 周期股、黑色系共振 |

**推荐接入的数据源**：
- 申万行业分类（31个一级行业 + 细分）
- 行业指数日线（用 akshare 或 tushare）
- 北向资金流向（行业维度）
- 行业轮动指标（相对强度 RPS）

---

## 五、K线外的分析维度（评分引擎核心）

这是整个方案的重头戏。每个分析维度作为一个**独立评分器**，统一输出 `Signal`。

```python
@dataclass
class Signal:
    product: str           # 品种代码如"沪深300"、"铜板块"
    dimension: str         # 评分维度
    direction: int         # +1=多, -1=空, 0=中性
    strength: float        # 0~1 置信度
    weight: float          # 该维度的权重
    reason: str            # 推理摘要
    data_sources: list[str] # 数据来源
```

**可接入的分析维度**（K线之外的）：

### 1. 宏观信号 (macro_signals.py)

```
- PMI/工业增加值 → 顺周期品种（如黑色/化工）
- CPI/PPI → 通胀敏感品种（农产品/能源）
- 社融/M2 → 流动性敏感（金融期货/有色）
- 美元指数 → 所有外盘联动品种
- 风险偏好（VIX/A股成交额）→ 股指期货
```

### 2. 基本面信号 (fundamental_signals.py)

```
- 库存周期：累库/去库阶段 → 方向判断
- 利润指标：焦化利润/加工利润/养殖利润 → 产业链传导
- 开工率：高炉/PTA/甲醇 → 供应端
- 进口利润：进口盈亏 → 内外套利
```

### 3. 情绪信号 (sentiment_signals.py)

```
- 持仓量变化：增仓上涨vs减仓上涨
- 成交持仓比：投机热度
- 期限结构：backwardation/contango → 供需紧张度
- 现货升贴水：期现价差
```

### 4. 跨市场信号 (cross_market_signals.py)

```
- 股期联动：A股板块vs期货共振
- 内外盘价差：沪铜vsLME铜
- 汇率影响：人民币升值/贬值对品种影响
- 板块间比价：卷螺差、油粕比、金银比
```

### 5. 事件驱动信号 (event_signals.py)

```
- 数据发布日历：USDA→农产品，EIA→原油，钢联→黑色
- 政策预期：房地产政策→黑色/玻璃，新能源政策→有色
- 天气事件：干旱→农产品，飓风→能源
```

---

## 六、评分引擎设计（核心）

```python
# scoring_engine.py
class ScoringEngine:
    """
    Agent综合分析入口。
    输入：目标品种/板块
    流程：
      1. 调用所有注册的评分器（每个返回Signal列表）
      2. 按品种group/关联性加权聚合
      3. 输出：最终方向、置信度、各维度投票明细

    Agent prompt用法：
    >>> signals = engine.analyze("RB")
    >>> 螺纹钢综合得分: +2.3/10 (偏多)
    >>>   - 宏观信号: +0.3 (权重0.15)
    >>>   - 基本面(库存): -0.5 (权重0.25) -- 累库压力
    >>>   - 技术面: +0.6 (权重0.20) -- 趋势向上
    >>>   - 跨市场: +0.9 (权重0.15) -- 铁矿强势联动
    >>>   - 情绪(持仓): +0.7 (权重0.10) -- 增仓上涨
    >>>   - 季节性: +0.3 (权重0.10) -- 金九银十
    >>>   - 事件: +0.0 (权重0.05) -- 无近期待发数据
    """
```

**关键设计点**：
- **权重可调**：不同品种在不同周期权重不同（比如农产品USDA报告日权重×2）
- **投票可视化**：agent拿到投票矩阵后，可自主决定是否采纳
- **知识库即权重**：`futures_knowledge.py` 里的 `macro_sensitivity` 决定了宏观信号对该品种的权重

---

# 期权知识库设计方案

## 一、期权在系统中的定位

```
期货分析线:         基本面→技术面→情绪→跨市场→最终方向判断
期权分析线(新增):   波动率→Greeks→策略选择→IV偏度→对期货方向的验证/反验证

两条线互为指导：
 · 期货方向信号 → 期权策略选择（买call还是卖put）
 · 期权IV结构 → 期货的恐惧/贪婪情绪反馈（恐慌→IV飙高→可能反转）
```

---

## 二、期权知识库模块结构

```
knowledge/
└── options_knowledge.py          # 🆕 期权知识库
├── options/                      # 🆕 期权信号/分析
   ├── options_greeks.py          # Greeks计算 + 风险暴露分析
   ├── options_iv_analysis.py     # IV结构分析（skew/term structure/IV rank）
   ├── options_strategies.py      # 策略知识库 + 推荐引擎
   ├── options_signals.py         # 期权信号（PCR/持仓分布/最大痛点）
   └── commodity_options.py       # 商品期权特性（国内商品期权特有规则）
```

---

## 三、核心数据结构

### 3.1 期权合约知识 (OptionsContractInfo)

```python
@dataclass
class OptionsProductInfo:
    """每个标的的期权市场特征"""
    underlying: str               # 标的代码，如 '510050' / 'IF' / 'RB'
    underlying_type: str          # 'ETF' / '指数' / '商品'
    exchange: str                 # 上市交易所
    option_type: str              # '金融期权' / '商品期权'

    # 合约规则
    contract_unit: int            # 合约单位
    strike_interval: float        # 行权价间距
    listed_months: list[int]      # 挂牌月份规律
    last_trading_day: str         # 最后交易日规则

    # 市场特征
    avg_iv: float                 # 历史平均隐含波动率
    iv_range: tuple[float, float] # IV常见范围 (min%, max%)
    liquidity_level: str          # '极高' / '高' / '中' / '低'

    # 特有现象
    chars: list[str]              # 该品种期权波动特点
    # 示例：['50ETF期权到期日效应明显',
    #        'IO期权IV在升贴水转换时剧烈波动',
    #        '商品期权行权交割复杂，注意自动行权规则']

    strategy_preferences: list[str]  # 该标的常用的期权策略
```

### 3.2 Greeks 暴露分析 (GreeksExposure)

```python
@dataclass
class GreeksSnapshot:
    """当前期权市场的 Greeks 概况"""
    # 标的整体Greeks暴露（所有合约汇总）
    total_delta: float            # 市场总Delta（正=偏多持仓）
    total_gamma: float            # 总Gamma（高→可能剧烈波动）
    total_vega: float             # 总Vega（高→波动率敏感）
    total_theta: float            # 总Theta（正=时间价值净收取）

    # ATM附近的Greeks（最能反映当前市场状态）
    atm_iv: float                 # 平值IV
    atm_delta: float
    atm_gamma: float              # Gamma峰值（ATM附近gamma最大）

    # 偏度
    skew_25d: float               # 25Delta call/put IV差
    # 如 put更贵→恐惧情绪，call更贵→贪婪情绪
```

### 3.3 信号输出 (OptionsSignal)

```python
@dataclass
class OptionsSignal:
    underlying: str
    signal_type: str              # 'iv_rank', 'pcr', 'skew', 'max_pain', 'gamma_squeeze'
    direction: int                # +1=利多, -1=利空, 0=中性
    strength: float               # 0~1 置信度
    value: float                  # 原始数值

    interpretation: str           # 对期货方向的解读
    # 示例:
    #   'PCR极端高位(1.5) → 市场过度看空 → 期货可能反弹'
    #   'IV skew急剧转负 → call被疯狂买入 → 市场极度乐观 → 警惕反转'
    #   '最大痛点显著偏离现价 → 期权到期前有向痛点回归的引力'
```

---

## 四、期权核心分析维度（6个信号级别）

### 4.1 波动率分析 (IV Analysis)

| 指标 | 计算方式 | 对期货方向的指导意义 |
|------|---------|---------------------|
| **IV rank/百分位** | 当前IV在历史区间的位置 | >80%→IV可能回归→卖方机会，<20%→买方机会 |
| **IV-HV溢价** | IV与历史波动率的差值 | 溢价太大→恐慌定价→可能反转 |
| **波动率锥** | 不同期限IV对比 | 近高远低→短期恐慌，近低远高→风险在远期 |
| **IV term structure** | 不同月份IV的曲线形状 | 陡峭→不确定性集中在近期 |

### 4.2 情绪类信号 (Sentiment via Options)

| 指标 | 期货方向的解读 |
|------|----------------|
| **Put/Call Ratio (PCR)** | 成交量PCR > 1 → 看空情绪浓；持仓量PCR > 0.8 → 专业投资者偏多 |
| **Skew (偏度)** | Put溢价高→恐慌情绪，Call溢价高→极度乐观（两者都是反向指标） |
| **最大痛点 (Max Pain)** | 期权到期时对标的的"引力"，偏离越远引力越强 |
| **未平仓量分布** | 大量OI集中的行权价构成支撑/阻力 |
| **Gamma squeeze 风险** | 大量ATM期权聚集 → 标的靠近时引爆gamma对冲 → 加速行情 |

### 4.3 策略知识库 (OptionsStrategy)

```python
@dataclass
class OptionsStrategy:
    name: str                     # 策略名称
    chinese_name: str             # 中文名
    setup: str                    # 适用场景
    components: list[str]         # 构成腿
    max_profit: str               # 最大盈利
    max_loss: str                 # 最大亏损
    breakeven: str                # 盈亏平衡点
    适合的市场: str                 # '大涨' / '小涨' / '震荡' / '小跌' / '大跌'
    适合的IV环境: str               # '低IV' / '高IV' / 'IV上升' / 'IV下降'

    greeks_profile: dict[str, float]  # 策略的Greeks暴露
    # 如跨式 {delta:0, gamma:+, vega:+, theta:-}

STRATEGIES = {
    "covered_call": OptionsStrategy(
        name="备兑开仓 (Covered Call)",
        setup="持有现货/期货多头，预期小涨或震荡",
        components=["long underlying", "short OTM call"],
        max_profit="权利金 + (行权价 - 买入价)",
        max_loss="持有现货的亏损 - 权利金",
        breakeven="买入价 - 权利金",
        适合的市场="小涨/震荡",
        适合的IV环境="高IV（赚取高权利金）",
        greeks_profile={"delta": "偏正(0.3-0.5)", "gamma": "负",
                       "vega": "负", "theta": "正"},
    ),
    # ... 20+ 策略
}
```

### 4.4 国内商品期权特有规则

```
商品期权（大商所/郑商所/上期所）与金融期权差异点：

1. 行权方式
   - 商品期权：美式（到期日前任意交易日可行权）
   - 金融期权（ETF）：欧式（仅到期日可行权）
   - 影响：美式期权有提前行权风险，需监控

2. 自动行权规则
   - 商品期权：实值额>0自动行权（不同交易所阈值不同）
   - 需关注：虚值期权不小心被行权的风险

3. 保证金计算
   - 商品期权卖方保证金 = 权利金 + max(标的保证金×比例 - 虚值额, ...)
   - 比金融期权公式复杂，不同品种公式不同

4. 涨跌停板联动
   - 商品期权随期货涨跌停而调整
   - 期货涨停→期权无法买入平仓
```

---

## 五、期权信号如何融入评分引擎

```python
# 在 scoring_engine.py 中新增一条处理链

def _process_options_signals(self, symbol: str) -> list[Signal]:
    """
    期权信号对期货方向的三大贡献：

      1. 情绪确认/反确认
         PCR极端 + IV飙高 + skew转负 → 市场过度一致 → 反向信号
         → 螺纹钢期货大涨，但期权PCR飙到1.5 → 看涨情绪过载 → 回调风险

      2. 引力效应（到期前3天最强）
         最大痛点偏离现价超过一定幅度 → 向痛点回归的统计倾向
         → 沪深300 3950，但最大痛点在3900 → 到期前可能回归

      3. 波动率预警
         IV sharp spike（一日涨幅超过30%）→ 市场在定价尾部风险
         → 铁矿IV一天内从35%飙升到50% → 可能有未知利空在酝酿
    """
```

**评分引擎集成后的完整流程**：

```
目标品种: RB 螺纹钢
┌──────────────────────────────────────────────────┐
│ ScoringEngine.analyze("RB")                      │
├──────────────────────────────────────────────────┤
│ K线信号:     MA5>MA10, RSI:58     +0.8 (w:0.15)  │
│ 基本面信号:  库存累库            -0.5 (w:0.20)   │
│ 宏观信号:    PMI回暖             +0.6 (w:0.15)   │
│ 跨市场信号:  铁矿强势            +0.7 (w:0.15)   │
│ 情绪信号:    持仓增加            +0.3 (w:0.10)   │
├──────────────────────────────────────────────────┤
│ 🆕 期权信号:                                      │
│   PCR: 0.95 (中性)              +0.1 (w:0.05)    │
│   IV rank: 35% (中性偏低)       +0.2 (w:0.05)    │
│   Skew: put溢价轻微 (正常)       +0.0 (w:0.05)    │
│   最大痛点偏离: 33元 (中等)      -0.3 (w:0.05)    │
│   Gamma压力: 无明显聚集          +0.0 (w:0.05)    │
├──────────────────────────────────────────────────┤
│ 综合得分: +1.9/10 (偏多，低置信度)                │
│ 期权维度加权: +0.0 (期权信号无明显指向)            │
│ Agent建议: 小仓位试多，关注周四钢联数据            │
└──────────────────────────────────────────────────┘
```

---

# 冷域交易系统 — 三库联动全方案

架构图已生成：`futures/system-architecture.html`，在浏览器打开可看可视化。下面是完整设计。

---

## 一、总架构（五层）

```
┌─────────────────────────────────────────────────┐
│  🏔️ 观山     🌊 楚风     🌌 听海     🌿 牧野     │ ← 决策层
│  (趋势)     (反转/套利)  (波动率/期权)  (基本面汇总) │   四大金刚
└──────────────────────┬──────────────────────────┘
                       │ 调用
┌──────────────────────▼──────────────────────────┐
│          ⚙️ 评分引擎 ScoringEngine               │ ← 评分层
│   Signal聚合 · 权重管理 · 多维度投票 · 综合置信度  │
└──────┬──────┬──────┬──────┬──────┬──────┬───────┘
       │      │      │      │      │      │
  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
  │技术 │ │宏观 │ │基本 │ │情绪 │ │跨市 │ │事件 │ │期权 │ ← 信号层
  │信号 │ │信号 │ │面   │ │信号 │ │场   │ │信号 │ │信号 │   7维度
  └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └──┬─┘
    │      │      │      │      │      │       │
    └──────┴──┬───┴──────┴──┬───┴──────┴───┬───┘
               │             │              │
         ┌─────▼────┐  ┌────▼────┐  ┌─────▼────┐
         │ 📊 期货  │  │ 📈 股票 │  │ 🎯 期权  │ ← 知识库层
         │ 知识库   │  │ 知识库  │  │ 知识库   │   三库联动
         └─────┬────┘  └────┬────┘  └─────┬────┘
               │            │             │
               └─────┬──────┴──────┬──────┘
                     │  关联矩阵   │
                     │correlation  │
                     │_matrix.py  │
               ┌─────┴─────────────┴──────┐
               │  easy_tdx  akshare  期权行情 │ ← 数据层
               │  宏观数据  事件日历          │
               └────────────────────────────┘
```

---

## 二、三库之间的联动关系

| 联动对 | 关联方式 | 信号价值 |
|--------|---------|---------|
| **期货 ↔ 股票** | 申万行业→期货品种映射表 | 期货夜盘→次日A股板块；A股板块暴涨→期货端机会 |
| **期货 ↔ 期权** | IV skew→市场恐惧/贪婪；PCR→多空情绪；Max Pain→到期引力 | 期权信号是期货方向的反向验证器 |
| **股票 ↔ 期权** | 个股/ETF期权PCR→市场对特定板块的情绪 | 50ETF/300ETF期权PCR对大盘的指向性 |
| **三库 ↔ 宏观** | 每个品种/行业的 macro_sensitivity 矩阵 | PMI超预期→哪些品种敏感？加权评分 |

**关联矩阵核心**: `correlation_matrix.py` 维护一张统一的关系表，三库共用：

```python
# 关联类型示例
correlation_matrix = {
    # 期货→期货
    ("RB", "HC"): 0.92,    # 卷螺
    ("RB", "I"):  0.85,    # 螺矿

    # 期货→股票行业
    ("RB", "钢铁行业"): 0.80,   # 螺纹→钢铁板块
    ("CU", "有色行业"): 0.85,   # 铜→有色板块

    # 期货→期权
    ("IF", "IO期权"): 0.90,     # 股指期货→股指期权
    ("RB", "RB期权"): 0.75,     # 螺纹期货→螺纹期权

    # 宏观→品种
    ("PMI", "CU"): 0.85,        # PMI对铜的影响
    ("美元指数", "AU"): 0.90,   # 美元对黄金的影响
}
```

---

## 三、7个信号维度的详细分工

| # | 信号维度 | 输入来源 | 输出格式 | 对Agent的价值 |
|---|---------|---------|---------|-------------|
| 1 | **技术** | `indicators.py`（已有） | 趋势/震荡/背离 | 入场时机 |
| 2 | **宏观** | PMI/社融/CPI/利率/美元 | 偏多/偏空/中性 | 大方向定调 |
| 3 | **基本面** | 库存/开工率/加工利润 | 供需松紧度 | 价格中枢判断 |
| 4 | **情绪** | 持仓变化/期限结构/投机度 | 市场温度 | 羊群效应反指 |
| 5 | **跨市场** | 股期联动/内外盘价差/汇率 | 共振/背离 | 方向确认 |
| 6 | **事件** | USDA/EIA/钢联/政策/天气 | 波动预警 | 风控+事件驱动 |
| 7 | **期权 🆕** | IV rank/PCR/skew/max pain | 恐惧/贪婪/引力 | 情绪的定量化 |

**关键设计**：期权信号不是独立做一个交易策略，而是作为**期货信号的增强/削弱因子**——它是市场上最聪明资金的「投票器」。

---

## 四、期权信号的三种用法

```python
# 1. 情绪反验证 — PCR极端时的反向信号
if pcr > 1.5:
    # 市场极度看空 → 可能是底部
    direction = +1  # 反向做多
    strength = 0.6

# 2. IV偏度 — 市场在定价什么风险？
if skew_25d < -5:
    # Call比Put贵 → 极度乐观
    direction = -1  # 警惕反转
    strength = 0.7

# 3. 最大痛点引力
if abs(spot - max_pain) / spot > 0.02:
    # 现价偏离痛点 > 2% → 到期前有回归力
    direction = -1 if spot > max_pain else +1
    strength = 0.5
```

---

## 五、评分引擎输出示例

```python
>>> engine = ScoringEngine()
>>> result = engine.analyze("RB")
>>> result.as_dict()
{
    "product": "RB",
    "composite_score": 2.3,       # 总分范围 -10 ~ +10
    "confidence": 0.55,           # 置信度 0~1
    "direction": "偏多",           # 最终建议

    "signals": [
        # 技术 +0.8 (w:0.15)
        Signal("RB","技术", +1, 0.8, 0.15, "MA5>MA10, RSI:58"),
        # 宏观 +0.6 (w:0.15)
        Signal("RB","宏观", +1, 0.6, 0.15, "PMI连续3月回暖"),
        # 基本面 -0.5 (w:0.25)  -- 权重最高
        Signal("RB","基本面", -1, 0.5, 0.25, "社库累库加速"),
        # 情绪 +0.3 (w:0.10)
        Signal("RB","情绪", +1, 0.3, 0.10, "持仓温和增加"),
        # 跨市场 +0.7 (w:0.15)
        Signal("RB","跨市场", +1, 0.7, 0.15, "铁矿强势联动"),
        # 事件 +0.0 (w:0.05)
        Signal("RB","事件", 0, 0.0, 0.05, "周四钢联数据待发"),
        # 期权 +0.2 (w:0.15)  -- 🆕
        Signal("RB","期权", +1, 0.2, 0.15, "PCR中性偏多"),
    ]
}
```
