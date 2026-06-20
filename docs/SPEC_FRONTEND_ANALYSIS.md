# 前端一键分析 Spec — FactorResearch 页面改造

> 目标：把现有 7 个独立 Tab + 一堆按钮 + Mock 数据，
> 改成：输入合约代码 → 一键完整分析 → 展示所有结果

---

## 一、改动概览

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/pages/FactorResearch.tsx` | 🟡 大幅修改 | 新增"一键分析"模式+输入框+结果面板 |
| `frontend/src/services/factorApi.ts` | 🟡 新增方法 | 添加 `fullAnalysis()` API 调用 |
| `api/routes/factor_routes.py` | 🟡 新增接口 | 添加 `POST /api/factor/full-analysis` 端点 |

---

## 二、用户界面

### 2.1 页面顶部 — 输入区

```
┌─────────────────────────────────────────────────────────┐
│  [期货/股票/期权] 完整分析                               │
│                                                         │
│  ┌──────────────────────────┐  ┌──────────────┐         │
│  │ 输入合约代码 (如 RB2510)  │  │  完整分析    │         │
│  └──────────────────────────┘  └──────────────┘         │
│                                                         │
│  ⚡ 支持: 期货(RB2510) / 股票(600019.SH) / 期权(IO)     │
│     数据来源: 仓库直连 | 分析: Alpha 101 全因子          │
└─────────────────────────────────────────────────────────┘
```

- **输入框**: `<Input>` 组件，placeholder="输入合约代码，如 RB2510 / 600019.SH" 
- **按钮**: `<Button type="primary" size="large">` — "🧬 完整分析"
- 按 Enter 键也能触发
- 输入框下方显示一行提示文字

### 2.2 加载状态

点击后按钮变 loading，显示整体进度:

```
[🧬 完整分析] (loading...)
进度: ████████░░ 正在计算 IC 分析...
```

用 `<Progress>` 组件 + 文字进度提示:
1. "正在加载行情数据..."
2. "正在计算 101 个 Alpha 因子..."
3. "正在分析 IC / 分层回测..."
4. "正在检测因子健康 / 生成报告..."
5. "完成!"

### 2.3 结果展示 (四个面板)

加载完成后，下方展示四个结果卡片:

```
┌─ 📊 因子总览 ─────────────────────────────────────┐
│  IC 均值: +0.0324  │  ICIR: 0.85  │  健康状况:     │
│  正IC因子: 62/101   │ 推荐组合: 5个  │  ✅ 43 健康    │
│                                               │  ⚠️ 8 警告    │
│  Top 5 因子: alpha005(+0.042) alpha012(+0.038)...│  ❌ 2 失效    │
└──────────────────────────────────────────────────┘

┌─ 📈 IC 分析 ─────────────────────────────────────┐
│  [IC 时间序列图]         [IC 分布直方图]            │
│  (SVG 折线图)            (SVG 柱状图)              │
│                                                   │
│  [IC 衰减分析]                                    │
│  (折线: 各周期 IC 变化)                            │
└──────────────────────────────────────────────────┘

┌─ 🏆 因子排名 + 推荐组合 ──────────────────────────┐
│  # │因子  │ IC    │ ICIR │ 多空Sharpe │ 健康   │ 推荐 │
│  ──────────────────────────────────────────── │
│  1 │α005 │+0.042│ 0.85 │ 1.23      │ ✅    │ ★   │
│  2 │α012 │+0.038│ 0.72 │ 0.98      │ ✅    │ ★   │
│  3 │α089 │+0.031│ 0.65 │ 0.87      │ ⚠️   │     │
│  ...                                          │
│                                                │
│ 推荐组合: [alpha005] [alpha012] [alpha018] ...  │
│ 组合 IC: 0.035  组合 ICIR: 0.74                │
└──────────────────────────────────────────────────┘

┌─ 📉 分层回测 ────────────────────────────────────┐
│  ██ Q1: -0.23%                                   │
│  ████ Q2: -0.08%                                 │
│  ██████ Q3: +0.05%      ← 单调递增 ✅            │
│  ████████ Q4: +0.18%                             │
│  ██████████ Q5: +0.35%                           │
│                                                  │
│  多空收益: +0.58%  多空夏普: 1.23  换手率: 0.15   │
└──────────────────────────────────────────────────┘
```

### 2.4 保留原有 Tabs

在"一键分析"面板下方，保留原有的 Tabs 作为**详细查看**入口:

```
[一键分析] ← 新面板 (默认激活)
─────────────────────
[因子列表] [IC分析] [分层回测] [因子组合] [挖掘] [健康] [报告]
 (原有各 Tab, 但数据从一键分析结果共享, 不再各自调用 API)
```

---

## 三、后端 API

### 3.1 新增端点

```python
# api/routes/factor_routes.py 新增

class FullAnalysisRequest(BaseModel):
    symbol: str  # 合约代码, 如 "RB2510" / "600019.SH"


@router.post("/full-analysis")
async def full_analysis(request: FullAnalysisRequest):
    """
    一键完整分析。
    
    调用 factor_cli 的核心逻辑:
      1. 加载数据 (仓库/CSV)
      2. 计算 101 个 Alpha 因子
      3. IC/ICIR 评估
      4. 分层回测
      5. 衰减检测
      6. 冗余分析 + 推荐组合
      7. 聚合返回
    """
    # 复用 factor_cli 的函数, 不走 subprocess
    from core.alpha import factor_cli
    
    # 加载数据
    df = factor_cli._load_from_warehouse(request.symbol)
    if df is None or df.empty:
        raise HTTPException(404, f"{request.symbol} 无数据")
    
    fwd = df["close"].pct_change().shift(-1)
    
    # 计算因子
    factors = factor_cli._alpha101_factors(df)
    
    # IC 分析
    from research.factor_lab.factor_analyzer import FactorAnalyzer
    analyzer = FactorAnalyzer()
    
    # 健康检测
    from core.alpha.management.factor_decay import FactorDecayDetector
    detector = FactorDecayDetector()
    
    # 报告
    from core.alpha.management import FactorReportGenerator
    gen = FactorReportGenerator()
    report = gen.generate(factors, fwd, top_n=20)
    
    # 组装返回
    return {
        "symbol": request.symbol,
        "data_points": len(df),
        "ic_stats": {
            "mean": report.recommended_ic,
            "positive_count": sum(1 for f in report.top_factors if f.ic_mean > 0),
            "total": report.total_factors,
        },
        "health_distribution": {
            "healthy": report.healthy_count,
            "warning": report.warning_count,
            "decayed": report.decayed_count,
        },
        "top_factors": [  # Top 10
            {"name": f.name, "ic": f.ic_mean, "icir": f.icir,
             "sharpe": f.sharpe_q5q1, "health": f.health,
             "recommended": f.is_recommended}
            for f in report.top_factors[:10]
        ],
        "recommended": report.recommended,
        "recommended_ic": report.recommended_ic,
        "recommended_icir": report.recommended_icir,
        "layered": {  # 分层回测摘要 (取第一个因子示例)
            "quantiles": [...],
            "long_short_return": ...,
            "long_short_sharpe": ...,
        },
        "data_source": "warehouse" if len(df) > 0 else "unknown",
    }
```

---

## 四、前端改动 (FactorResearch.tsx)

### 4.1 状态变量新增

```typescript
// 输入
const [symbolInput, setSymbolInput] = useState("");  // 文本输入框
const [analysisLoading, setAnalysisLoading] = useState(false);
const [analysisProgress, setAnalysisProgress] = useState("");  // 进度文字
const [analysisResult, setAnalysisResult] = useState<any>(null);

// 旧状态保留但改为从 analysisResult 派生
// selectedSymbol 不再用 Select, 直接从 symbolInput 来
```

### 4.2 一键分析函数

```typescript
const handleFullAnalysis = async () => {
  if (!symbolInput.trim()) {
    message.warning("请输入合约代码");
    return;
  }
  setAnalysisLoading(true);
  setAnalysisProgress("正在加载行情数据...");
  setAnalysisResult(null);
  
  try {
    // 分步更新进度
    await delay(100);
    setAnalysisProgress("正在计算 101 个 Alpha 因子...");
    
    const result = await factorApi.fullAnalysis({
      symbol: symbolInput.trim().toUpperCase(),
    });
    
    setAnalysisResult(result);
    message.success(`${symbolInput} 完整分析完成`);
  } catch (error: any) {
    message.error(`分析失败: ${error.message}`);
  } finally {
    setAnalysisLoading(false);
    setAnalysisProgress("");
  }
};

// 支持 Enter 键触发
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === "Enter") handleFullAnalysis();
};
```

### 4.3 渲染函数新增

```typescript
// 总览卡片
const renderOverview = () => {
  // 显示: IC均值/正IC数/健康分布/推荐组合数
};

// IC 图表
const renderICCharts = () => {
  // 复用现有 renderICTimeSeries renderICDistribution renderICDecay
};

// 排名表格
const renderRankingTable = () => {
  // 复用现有 report 的表格逻辑
};

// 分层柱状图
const renderLayeredChart = () => {
  // 复用现有 renderLayeredBacktest 的柱状图
};
```

### 4.4 页面结构更新

```tsx
export default function FactorResearch() {
  // ... 状态定义 ...
  
  return (
    <div>
      {/* 新版: 输入区 */}
      <Card style={{ marginBottom: 16 }}>
        <Title level={4}>🧬 因子完整分析</Title>
        <Space.Compact style={{ width: "100%" }}>
          <Input
            size="large"
            placeholder="输入合约代码，如 RB2510 / 600019.SH / IO"
            value={symbolInput}
            onChange={e => setSymbolInput(e.target.value)}
            onKeyDown={handleKeyDown}
            prefix={<SearchOutlined />}
          />
          <Button
            type="primary"
            size="large"
            loading={analysisLoading}
            onClick={handleFullAnalysis}
          >
            {analysisLoading ? analysisProgress : "🧬 完整分析"}
          </Button>
        </Space.Compact>
        <Text type="secondary" style={{ marginTop: 8, display: "block" }}>
          支持: 期货合约(RB2510) / 股票(600019.SH) / 期权(IO) — 数据直连仓库
        </Text>
      </Card>
      
      {/* 进度条 */}
      {analysisLoading && (
        <Progress percent={...} status="active" />
      )}
      
      {/* 结果面板 */}
      {analysisResult && !analysisLoading && (
        <>
          {renderOverview()}
          {renderICCharts()}
          {renderRankingTable()}
          {renderLayeredChart()}
        </>
      )}
      
      {/* 空状态 */}
      {!analysisResult && !analysisLoading && (
        <Empty description="输入合约代码，点击「完整分析」开始" />
      )}
      
      {/* 下方保留原有 Tabs */}
      <Divider />
      <Card title="详细分析工具">
        <Tabs defaultActiveKey="list">
          {/* 原有 Tab 内容, 但数据从 analysisResult 共享 */}
        </Tabs>
      </Card>
    </div>
  );
}
```

---

## 五、数据流

```
用户输入 "RB2510" → 点击"完整分析"
       │
       ▼
factorApi.fullAnalysis({symbol: "RB2510"})
       │
       ▼
POST /api/factor/full-analysis
       │
       ▼
后端:
  _load_from_warehouse("RB2510")  →  取行情数据
  _alpha101_factors(df)           →  算 101 个因子
  FactorDecayDetector              →  健康检测
  FactorReportGenerator            →  排名+推荐
  FactorAnalyzer                   →  IC/分层
       │
       ▼
返回 JSON:
  {ic_stats, health_distribution, top_factors,
   recommended, layered, ...}
       │
       ▼
前端渲染:
  总览卡片 + IC图表 + 排名表 + 分层图
```

---

## 六、不要改的

1. **不动现有 `factor_routes.py` 其他端点** — 只新增 `full-analysis`
2. **不动 `factorApi.ts` 已有方法** — 只新增 `fullAnalysis()`
3. **不动原有 Tab 的 UI 代码** — 只新增"一键分析"面板放在顶部
4. **不动后端 CLI `factor_cli.py`** — 直接 import 它的函数复用

---

## 七、验收标准

| # | 验收项 | 验证方式 |
|---|--------|---------|
| 1 | 输入框可自由输入任意代码 | 输入 RB2510 / 600019.SH / SR609 均能触发 |
| 2 | 按 Enter 触发分析 | 焦点在输入框时按 Enter 触发 loading |
| 3 | 加载中显示进度文字 | 四种进度状态依次显示 |
| 4 | 结果展示 4 个面板 | 总览/IC图/排名/分层 都渲染 |
| 5 | 健康分布用颜色区分 | ✅绿色 ⚠️橙色 ❌红色 |
| 6 | 推荐组合用 ★ 标记 | 排名表中推荐因子有星号 |
| 7 | 错误状态合理提示 | 无数据/网络错误显示对应消息 |
| 8 | 空状态友好 | 初始状态显示"输入代码开始分析" |
