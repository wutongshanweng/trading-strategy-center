# 因子可读化 Spec — 中文翻译 + 交易建议翻译层

> 两个独立任务，可并行：
>   A: 101 个因子的中文描述 + 解读
>   B: 因子分析 → 可执行交易建议

---

# A 篇 — 101 因子中文翻译

## A.1 目标

现 `alpha001.py` 的 `description` 返回的是 WorldQuant 公式源码：
```
"Alpha001: (rank(Ts_ArgMax(SignedPower(...), 5)) - 0.5)"
```

用户看不懂。改成返回**中文解释**，让任何人一眼看懂这个因子在算什么。

## A.2 实现方式

### 方式一：不修改原文件，新建映射表（推荐）

新建 `core/alpha/alpha101/factor_descriptions.py`：

```python
"""
Alpha 101 因子中文描述字典。

每个条目包含:
  - name: 因子名
  - chinese_name: 中文名 (简明)
  - formula: 计算公式 (伪代码, 用户可理解)
  - interpretation: 值高/值低分别意味着什么
  - category: 分类
  - use_case: 适合什么场景

用法:
    from core.alpha.alpha101.factor_descriptions import get_description
    desc = get_description("alpha001")
    print(desc["chinese_name"])  # "价格动量-高峰位置"
    print(desc["interpretation"])
    # → "值高: 过去5天价格有显著的冲高走势, 后续可能回落"
    # → "值低: 过去5天价格冲高不明显, 动量平稳"
"""

from typing import Dict, Optional

ALPHA101_DESCRIPTIONS: Dict[str, dict] = {
    "alpha001": {
        "chinese_name": "价格动量-高峰位置",
        "formula": "对过去5天内价格最高点出现的时间位置打分, 越近值越高",
        "interpretation": "值高: 价格高点出现在最近 → 上涨势头强劲, 短期可能继续\n"
                          "值低: 价格高点出现在较远 → 上涨动力减弱",
        "use_case": "识别短期上涨趋势的持续性",
        "signal_logic": "正因子: 值高 → 做多; 值低 → 做空 (动量策略)",
    },
    "alpha002": {
        "chinese_name": "量价相关性-符号反转",
        "formula": "计算过去5天收盘价与成交量的相关系数, 取符号相反的排名",
        "interpretation": "值高: 价涨量缩或价跌量增 → 量价背离, 趋势可能反转\n"
                          "值低: 价量同步 → 趋势健康",
        "use_case": "识别趋势背离/反转信号",
        "signal_logic": "正因子: 值高 → 做空(背离); 值低 → 做多(同步)",
    },
    "alpha003": {
        "chinese_name": "价格位置-区间回归",
        "formula": "计算收盘价在过去20天高低点区间内的相对位置",
        "interpretation": "值高: 价格处于近期高位 → 接近阻力区\n"
                          "值低: 价格处于近期低位 → 接近支撑区",
        "use_case": "判断价格在震荡区间内的位置",
        "signal_logic": "正因子: 值高 → 做多(突破); 值低 → 做空(跌破)",
    },
    "alpha004": {
        "chinese_name": "日内振幅-趋势强度",
        "formula": "过去N天日内振幅(高低价差/均价)的趋势判断",
        "interpretation": "值高: 振幅持续扩大 → 趋势加速\n"
                          "值低: 振幅收窄 → 趋势减弱或盘整",
        "use_case": "衡量趋势的强度/加速度",
    },
    "alpha005": {
        "chinese_name": "开盘-均价偏离",
        "formula": "比较开盘价与过去10天均价, 结合价格与均价的距离",
        "interpretation": "值高: 开盘价显著高于均价但价格正接近均价 → 开盘透支\n"
                          "值低: 开盘价低于均价 → 开盘偏弱",
        "use_case": "判断开盘是否透支/低估",
    },
    "alpha006": {
        "chinese_name": "开盘-收盘相关系数",
        "formula": "开盘价与过去N天收盘价的相关系数",
        "interpretation": "值高: 开盘方向与近期趋势一致 → 趋势延续\n"
                          "值低: 开盘跳空与趋势相反 → 可能反转",
        "use_case": "判断开盘方向与趋势是否一致",
    },
    "alpha007": {
        "chinese_name": "成交量-价格趋势强度",
        "formula": "成交量与价格趋势的结合 (量价配合度)",
        "interpretation": "值高: 价涨量增 → 上涨健康\n"
                          "值低: 价涨量缩 → 上涨乏力",
        "use_case": "验证趋势的可信度",
    },
    "alpha008": {
        "chinese_name": "价格-移动均线乖离率",
        "formula": "当前价格与N日均线的偏离程度",
        "interpretation": "值高: 价格远高于均线 → 超买, 警惕回调\n"
                          "值低: 价格远低于均线 → 超卖, 关注反弹",
        "use_case": "超买超卖判断",
    },
    "alpha009": {
        "chinese_name": "日内动量-开盘贡献度",
        "formula": "过去N天涨跌幅中, 开盘跳空的贡献比例",
        "interpretation": "值高: 行情主要由开盘跳空驱动 → 趋势强势\n"
                          "值低: 行情由盘中波动驱动 → 趋势犹豫",
        "use_case": "区分开盘驱动 vs 盘中驱动行情",
    },
    "alpha010": {
        "chinese_name": "日涨跌幅-趋势平滑",
        "formula": "过去4天的每日涨跌幅做平滑处理",
        "interpretation": "值高: 最近涨幅大且持续 → 短期趋势向上\n"
                          "值低: 最近跌幅大且持续 → 短期趋势向下",
        "use_case": "捕捉短期趋势方向",
    },
    # ... 剩余 91 个因子, 格式同上
    # 每个因子的描述参考其 WorldQuant 公式和 category 分类
}

# 分类汇总:
CATEGORIES = {
    "momentum": "动量类 — 衡量价格变化的速度和方向",
    "trend": "趋势类 — 识别价格趋势的强度和持续性",
    "volume": "量价类 — 分析成交量与价格的关系",
    "volatility": "波动类 — 衡量价格波动的大小和变化",
    "vwap": "均价类 — 基于成交均价(VWAP)的分析",
    "reversal": "反转类 — 识别趋势末端/反转信号",
    "correlation": "相关类 — 不同时间维度价格的相关关系",
    "custom": "自定义 — 其他复合逻辑",
}


def get_description(name: str) -> Optional[dict]:
    """获取某个因子的中文描述"""
    return ALPHA101_DESCRIPTIONS.get(name)


def get_category_description(category: str) -> Optional[str]:
    """获取分类的中文描述"""
    return CATEGORIES.get(category)


# 在因子列表中展示时, 字段映射:
DISPLAY_FIELDS = {
    "chinese_name": "中文名",
    "formula": "计算公式",
    "interpretation": "值高/值低含义",
    "use_case": "适用场景",
}
```

### A.2.2 中文名 + 解读的完整列表 (前 30 个示例，剩余 71 个按同样格式补全)

因篇幅原因，完整 101 个因子的中文描述在 Spec 中给出关键信息。Claude Code 需要：

1. 读取 `core/alpha/alpha101/` 下所有 `alpha001.py` ~ `alpha101.py` 文件
2. 对**每个因子**提取其：
   - `name` (alpha001, alpha002...)
   - `category` (momentum, trend, volume...)
   - 从 `class docstring` 或原 `description` 理解公式含义
3. 用中文写出 `chinese_name`, `formula`, `interpretation`, `use_case`

### A.2.3 前端展示 — 工具提示

在 `FactorResearch.tsx` 的因子列表中，每行因子名加一个 `?` 图标，hover 时弹出：

```
alpha094 ─ [?]
          │
          ├ 中文名: 开盘-收盘趋势背离
          ├ 公式: 开盘方向与后续走势的对比
          ├ 值高: 开盘方向与趋势一致 → 趋势延续
          ├ 值低: 开盘方向与趋势相反 → 警惕反转
          └ 适合: 反向信号验证
```

用 Ant Design `Tooltip` 组件：

```tsx
import { Tooltip, Typography } from "antd";
import { QuestionCircleOutlined } from "@ant-design/icons";

const renderFactorName = (name: string) => {
  const desc = factorDescriptions[name]; // 从 API 加载或前端字典
  return (
    <Space>
      <Text strong>{name}</Text>
      {desc && (
        <Tooltip title={
          <div>
            <div><b>{desc.chinese_name}</b></div>
            <div style={{fontSize:12, marginTop:4}}>{desc.formula}</div>
            <div style={{fontSize:12, marginTop:4, color:"#aaa"}}>
              值高: {desc.interpretation.split("\n")[0]}
            </div>
          </div>
        }>
          <QuestionCircleOutlined style={{ color: "#888", cursor: "help" }} />
        </Tooltip>
      )}
    </Space>
  );
};
```

---

# B 篇 — 交易建议翻译层

## B.1 目标

现有的因子分析输出 IC/分层/排名，但用户想要一句话结论：
**"RB2510 → 🟢 做多, 置信度 中高, 理由: ..."**

## B.2 后端

### B.2.1 新建文件

`core/alpha/factor_advisor.py`

```python
"""
因子建议器 — 把因子分析结果翻译成可执行的交易建议。

用法:
    advisor = FactorAdvisor()
    advice = advisor.advise(symbol="RB2510", signals_df=combined_signal)
    print(advice["summary"])
    # → "【RB2510】🟢 做多 置信度:中高
    #    综合信号 +0.42, ICIR=0.74, 参与因子:10个"
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass, field


@dataclass
class TradingAdvice:
    """交易建议"""
    symbol: str                     # 标的
    action: str                     # "BUY" / "SELL" / "HOLD" / "WAIT"
    action_cn: str                  # "做多" / "做空" / "观望" / "谨慎"
    confidence: str                 # "高" / "中高" / "中" / "低" / "极低"
    confidence_score: float         # 0~1
    signal_value: float             # 综合信号值 (正=看多, 负=看空)
    reason: str                     # 一句话理由
    details: Dict = field(default_factory=dict)  # 详细数据
    risk_note: str = ""             # 风险提示


class FactorAdvisor:
    """
    因子建议器。
    
    输入: 因子分析结果
    输出: TradingAdvice (可执行建议)
    
    判定逻辑:
        方向 = signal_value 的符号
        置信度 = ICIR (越大越可靠)
        最终建议 = signal_value + confidence 的综合判断
    """
    
    def advise(
        self,
        symbol: str,
        combined_signal: pd.Series,     # 因子组合后的综合信号
        icir: float,                    # 综合 ICIR
        factor_count: int,              # 参与因子数
        top_factors: List[Dict],        # Top 因子信息
        health_distribution: Dict,      # 健康分布
    ) -> TradingAdvice:
        """
        生成交易建议。
        
        决策规则:
          signal > 0.15 且 ICIR > 0.5  → BUY (做多)
          signal < -0.15 且 ICIR > 0.5 → SELL (做空)
          ICIR < 0.2                    → HOLD (不交易, 信号不可靠)
          signal 绝对值 < 0.05          → WAIT (信号太弱)
          其他                           → 小仓位试探
        
        置信度:
          ICIR > 1.0  → "高"
          ICIR > 0.5  → "中高"
          ICIR > 0.2  → "中"
          ICIR > 0.0  → "低"
          否则         → "极低"
        """
        # 1. 计算综合信号值
        signal_val = float(combined_signal.mean()) if len(combined_signal) > 0 else 0.0
        
        # 2. 判定方向 + 动作
        if signal_val > 0.15 and icir > 0.5:
            action, action_cn = "BUY", "做多"
            reason = f"综合信号 {signal_val:+.2f} (正向偏多), ICIR={icir:.2f} (高置信度)"
        elif signal_val < -0.15 and icir > 0.5:
            action, action_cn = "SELL", "做空"
            reason = f"综合信号 {signal_val:+.2f} (负向偏空), ICIR={icir:.2f} (高置信度)"
        elif abs(signal_val) < 0.05 or icir < 0.1:
            action, action_cn = "HOLD", "观望"
            reason = f"综合信号 {signal_val:+.2f} 接近零 或 ICIR={icir:.2f} 过低, 方向不明确, 暂不建议交易"
        elif icir < 0.3:
            action, action_cn = "WAIT", "谨慎"
            reason = f"综合信号 {signal_val:+.2f}, 但 ICIR={icir:.2f} 偏低, 建议小仓位试探或等信号强化"
        else:
            action, action_cn = "WAIT", "谨慎"
            reason = f"信号方向存在但强度不足 (signal={signal_val:+.2f}, ICIR={icir:.2f})"
        
        # 3. 置信度文字
        if icir > 1.0: conf = "高"
        elif icir > 0.5: conf = "中高"
        elif icir > 0.2: conf = "中"
        elif icir > 0.0: conf = "低"
        else: conf = "极低"
        
        # 4. 风险提示
        health_ok = health_distribution.get("healthy", 0)
        health_total = sum(health_distribution.values())
        if health_ok / max(health_total, 1) < 0.3:
            risk = "⚠️ 大部分因子处于非健康状态, 建议谨慎对待当前信号"
        elif factor_count < 3:
            risk = "参与信号因子不足, 信号可能不稳定"
        else:
            risk = ""
        
        return TradingAdvice(
            symbol=symbol, action=action, action_cn=action_cn,
            confidence=conf, confidence_score=min(abs(icir), 1.0),
            signal_value=round(signal_val, 4), reason=reason,
            details={
                "icir": round(icir, 4),
                "factor_count": factor_count,
                "top_factors": top_factors[:5],
                "health": health_distribution,
            },
            risk_note=risk,
        )
    
    def advise_from_report(
        self,
        symbol: str,
        report,              # FactorResearchReport
        combined_signal: pd.Series,
    ) -> TradingAdvice:
        """从 FactorResearchReport 生成建议。"""
        return self.advise(
            symbol=symbol,
            combined_signal=combined_signal,
            icir=report.recommended_icir,
            factor_count=len(report.recommended),
            top_factors=[
                {"name": f.name, "ic": f.ic_mean, "health": f.health}
                for f in report.top_factors[:5]
            ],
            health_distribution={
                "healthy": report.healthy_count,
                "warning": report.warning_count,
                "decayed": report.decayed_count,
            },
        )
```

### B.2.2 集成到 full-analysis 接口

在 `POST /api/factor/full-analysis` 中新增：

```python
@router.post("/full-analysis")
async def full_analysis(request: FullAnalysisRequest):
    # ... 原有分析逻辑 ...
    
    # 新增: 综合信号
    combiner = FactorCombiner(factors)
    combined_signal = combiner.ic_weight(factors, ic_values)
    
    # 新增: 交易建议
    from core.alpha.factor_advisor import FactorAdvisor
    advisor = FactorAdvisor()
    advice = advisor.advise_from_report(
        symbol=request.symbol,
        report=report,
        combined_signal=combined_signal,
    )
    
    return {
        # ... 原有返回 ...
        "advice": {
            "action": advice.action,
            "action_cn": advice.action_cn,
            "confidence": advice.confidence,
            "reason": advice.reason,
            "signal_value": advice.signal_value,
            "risk_note": advice.risk_note,
        },
        "combined_signal": combined_signal.tail(10).to_dict(),
    }
```

### B.2.3 集成到 CLI

在 `factor_cli.py` 的 `cmd_report` 末尾新增:

```python
def cmd_report(args):
    # ... 原有逻辑 ...
    
    # 新增: 打印交易建议
    from core.alpha.factor_advisor import FactorAdvisor
    combiner = FactorCombiner(factors)
    signal = combiner.ic_weight(factors, {f.name: f.ic_mean for f in report.top_factors})
    advice = FactorAdvisor().advise_from_report(
        args.symbol or args.data, report, signal)
    
    print(f"\n{'='*60}")
    print(f"  【{advice.symbol}】{'🟢' if advice.action=='BUY' else '🔴' if advice.action=='SELL' else '⚪'} {advice.action_cn}")
    print(f"  置信度: {advice.confidence}  |  综合信号: {advice.signal_value:+.4f}")
    print(f"  理由: {advice.reason}")
    if advice.risk_note:
        print(f"  {advice.risk_note}")
    print(f"{'='*60}")
```

---

## B.3 前端展示

### B.3.1 新增结果卡 — 交易建议

在 `FactorResearch.tsx` 的一键分析结果中，**第一个卡片就是交易建议**：

```tsx
// 交易建议卡片 (放在结果最顶部)
const renderAdvice = (advice: any) => {
  const colorMap: Record<string, string> = {
    "BUY": "#52c41a", "SELL": "#ff4d4f",
    "HOLD": "#888", "WAIT": "#faad14",
  };
  const iconMap: Record<string, string> = {
    "BUY": "🟢", "SELL": "🔴", "HOLD": "⚪", "WAIT": "🟡",
  };
  
  return (
    <Card style={{
      borderLeft: `4px solid ${colorMap[advice.action]}`,
      marginBottom: 16,
    }}>
      <Row align="middle" gutter={24}>
        <Col>
          <div style={{fontSize: 36}}>{iconMap[advice.action]}</div>
        </Col>
        <Col flex="auto">
          <Title level={4} style={{margin: 0, color: colorMap[advice.action]}}>
            {advice.action_cn}
          </Title>
          <Text type="secondary">{advice.reason}</Text>
          {advice.risk_note && (
            <div style={{marginTop: 8}}>
              <Text type="warning">{advice.risk_note}</Text>
            </div>
          )}
        </Col>
        <Col>
          <Statistic title="置信度" value={advice.confidence} />
          <Statistic title="信号值" value={advice.signal_value} 
            valueStyle={{color: advice.signal_value > 0 ? "#52c41a" : "#ff4d4f"}} />
        </Col>
      </Row>
    </Card>
  );
};
```

### B.3.2 因子列表添加描述

在因子列表的 `columns` 中，将 `name` 列改为带 Tooltip 的展示：

```tsx
const columns = [
  {
    title: "因子",
    dataIndex: "name",
    key: "name",
    render: (name: string) => {
      // factorDescriptions 从后端 API 加载或内嵌字典
      const desc = factorDescriptions[name];
      return (
        <Space>
          <Text strong>{name}</Text>
          {desc && (
            <Tooltip title={
              <div style={{maxWidth: 300}}>
                <div><b>{desc.chinese_name}</b></div>
                <div style={{fontSize:12, marginTop:4, color:"#aaa"}}>
                  {desc.formula}
                </div>
                <div style={{fontSize:12, marginTop:4, borderTop:"1px solid #333", paddingTop:4}}>
                  <span style={{color:"#52c41a"}}>值高</span>: {desc.interpretation.split("\n")[0]}
                  <br />
                  <span style={{color:"#ff4d4f"}}>值低</span>: {desc.interpretation.split("\n")[1]}
                </div>
              </div>
            }>
              <QuestionCircleOutlined style={{color:"#888", cursor:"help"}} />
            </Tooltip>
          )}
        </Space>
      );
    },
  },
  // ... 原有其他列
];
```

### B.3.3 新增接口获取描述

```typescript
// factorApi.ts 新增
async getFactorDescriptions(): Promise<Record<string, any>> {
  const response = await axios.get(`${API_BASE_URL}/api/factor/factors/descriptions`);
  return response.data;
}
```

```python
# factor_routes.py 新增
@router.get("/factors/descriptions")
async def factor_descriptions():
    from core.alpha.alpha101.factor_descriptions import ALPHA101_DESCRIPTIONS
    return ALPHA101_DESCRIPTIONS
```

---

## 验收标准

| # | 验收项 | 归属 | 验证方式 |
|---|--------|------|---------|
| 1 | 101 个因子都有中文名 + 解读 | A | `len(ALPHA101_DESCRIPTIONS) == 101` |
| 2 | 每个因子的 interpretation 包含"值高/值低"含义 | A | 检查 key 存在且不为空 |
| 3 | 前端因子名 hover 显示描述弹窗 | A | 鼠标悬停 ? 图标可读 |
| 4 | 交易建议的决策规则覆盖 4 种场景 | B | BUY/SELL/HOLD/WAIT 均可触发 |
| 5 | 置信度文字与 ICIR 匹配 | B | ICIR>0.5="中高" |
| 6 | 前端建议卡片带颜色 | B | BUY=绿, SELL=红, HOLD=灰 |
| 7 | CLI 也打印交易建议 | B | `factor_cli report` 末尾显示 |
| 8 | factor_descriptions API 可用 | A | GET 返回完整 101 条 |
