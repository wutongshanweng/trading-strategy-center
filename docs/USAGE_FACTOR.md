# 因子系统使用指南 (USAGE)

> 一行命令跑出结果，无需 import 任何类。
> 入口: `core/alpha/factor_cli.py` | 全资产支持: 期货 / 股票 / 期权

---

## 0. 核心理念

因子研究**不限股票，全资产通用**。算法层(IC/分层/挖掘/中性化/报告)对任何 OHLCV
序列都适用。数据直连 **DuckDB 统一仓库**——你在数据中心采集的期货 `RB2510`、
股票 `600019.SH`、期权 `SR609C4600`，因子研究都能直接分析，按 `code` 取数即可。

**数据来源 (二选一)**:
- `--symbol RB2510` — 从仓库直取 (优先经后端 API，避开 DuckDB 独占锁；后端没跑时直读 DB)
- `--data file.csv` — 从 CSV 读 (需含 open/high/low/close/volume)

---

## 1. 命令速查

| 命令 | 作用 | 示例 |
|------|------|------|
| `report` | 一键全因子报告 (排名/冗余/推荐组合/HTML+JSON) | `report --symbol RB2510 --html r.html` |
| `combine` | 多因子合成一个综合信号 | `combine --symbol 600019.SH --method ic_weight` |
| `mine` | 遗传挖掘新因子 | `mine --symbol RB2510 --generations 20 --save mined.json` |
| `health` | 因子健康检测 (单个/全因子) | `health --symbol RB2510 --all` |
| `layered` | 单因子分层回测 | `layered --symbol 600019.SH --factor alpha005` |
| `scan` | 全市场批量巡检 (跨标的健康分布) | `scan --symbols RB2510,600019.SH,SR609C4600` |

运行方式: `python -m core.alpha.factor_cli <命令> [参数]`

---

## 2. 五大基础场景

### 场景 A — "这个因子还有用吗?"
```bash
python -m core.alpha.factor_cli health --symbol RB2510 --factor alpha005
python -m core.alpha.factor_cli health --symbol RB2510 --all      # 全因子巡检
```
输出三态评级:
```
alpha001  HEALTHY  IC=0.0320  ICIR=0.85
alpha002  WARNING  IC=0.0080  ICIR=0.12  近期IC不足长期一半
alpha003  DECAYED  IC=0.0030  ICIR=0.05  IC趋势下行
```

### 场景 B — "把 101 个因子合成 1 个信号选品种"
```bash
python -m core.alpha.factor_cli combine --symbol 600019.SH --method ic_weight
```
返回综合信号 → 排序选 Top/Bottom 做多空，或喂给 `signals/`、`resonance/` 引擎。

### 场景 C — "针对 RB 挖新因子"
```bash
python -m core.alpha.factor_cli mine --symbol RB2510 --generations 20 --top 10 --save mined.json
```
遗传演化产出 + 保存 JSON (含 IC/ICIR/Sharpe/表达式)。无 deap 自动用内置 numpy 引擎。

### 场景 D — "一键体检全因子库"
```bash
python -m core.alpha.factor_cli report --symbol RB2510 --html report.html --json report.json
```
排名 + 健康分布 + 冗余检测 + **低相关推荐组合** → HTML 浏览器打开看。

### 场景 E — "看单因子分层效果"
```bash
python -m core.alpha.factor_cli layered --symbol 600019.SH --factor alpha005 --quantiles 5
```

---

## 3. 进阶应用场景 (生产实战)

### 场景 F — 全市场批量巡检 (运维)
定期扫描整个仓库的因子健康，发现集体失效:
```bash
python -m core.alpha.factor_cli scan --symbols RB2510,RB2610,600019.SH,SR609C4600
```
```
标的            健康  警告  失效   数据
RB2510           1    5    0    243
600019.SH        3    1    2   1000
SR609C4600       2    3    1    180
```
→ 哪些标的因子集体衰减一目了然，指导因子下线。

### 场景 G — 跨资产因子对比
同一因子在期货 vs 股票 vs 期权上的表现差异:
```bash
python -m core.alpha.factor_cli health --symbol RB2510   --factor alpha005   # 期货
python -m core.alpha.factor_cli health --symbol 600019.SH --factor alpha005   # 股票
```
→ 发现某因子只在特定资产类别有效，避免误用。

### 场景 H — 定时自动巡检 (接 cron / OpenWolf 调度)
```bash
# 每个交易日收盘后跑全市场体检，输出报告归档
python -m core.alpha.factor_cli report --symbol RB2510 --json reports/$(date +%F).json
```
→ 配合系统的实时同步面板，形成"采集→巡检→下线"闭环。

### 场景 I — 挖掘 → 入库 → 投票 闭环
```bash
# 1. 挖因子
python -m core.alpha.factor_cli mine --symbol RB2510 --save new_factors.json
# 2. 验证健康后，纳入因子库 (FactorStore 版本管理)
# 3. combine 合成信号 → 输入 resonance 引擎参与 观山/楚风/听海 投票
```

### 场景 J — CSV 离线研究 (脱离仓库)
有自己的数据文件，不依赖系统仓库:
```bash
python -m core.alpha.factor_cli report --data my_data.csv --html out.html
```

---

## 4. Python API (需要嵌入自己代码时)

```python
# 因子挖掘 + 保存
from core.alpha.mining import GeneticFactorMiner, GeneticConfig
miner = GeneticFactorMiner(GeneticConfig(generations=20))
factors = miner.mine(df, n_factors=10)        # df 含 OHLCV
miner.save_factors(factors, "mined.json")

# 因子健康检测
from core.alpha.management import FactorDecayDetector
report = FactorDecayDetector().check("alpha001", ic_series, factor_values, forward_returns)
print(report.health.value)                    # HEALTHY / WARNING / DECAYED

# 行业中性化
from core.alpha.management import IndustryNeutralizer
neutral = IndustryNeutralizer().neutralize_by_mean(factor_values, industry_labels)

# 全因子报告
from core.alpha.management import FactorReportGenerator
gen = FactorReportGenerator()
rep = gen.generate(factors_df, forward_returns, industry_labels=industries)
gen.save_html(rep, "report.html")
```

---

## 5. Web 入口

前端「因子研究」页提供同等能力的可视化操作 (无需命令行):
- **因子挖掘** tab — 选标的 → 遗传挖掘 → 因子表
- **健康监控** tab — 三态评级 + IC趋势/单调性
- **研究报告** tab — 一键评估 → 排名 + 推荐组合

API: `POST /api/factor/{mine,health-check,report,neutralize}` — 全部接仓库真实数据。

---

## 6. 注意事项

1. **DuckDB 单进程独占锁**: CLI 优先经后端 HTTP API 取数 (后端在跑时)，无冲突；
   后端没跑时 CLI 直读 DB。两者都不行时用 `--data CSV`。
2. **数据量**: 部分 Alpha 因子需较长历史 (60+ bar) 才能计算，数据不足会被跳过。
3. **行业中性化**: 主要对股票有意义 (行业映射来自股票知识库)；期货/期权一般不做。
4. **deap 可选**: 安装了用其加速，没装自动回退内置 numpy 引擎，功能不受影响。
