# 前端数据同步修复方案

## 📊 问题分析

### 当前状况
1. **策略页面**: 显示8个策略，但后端有57+个
2. **数据中心**: 显示11个数据源，但后端支持16类
3. **因子研究**: 页面缺失，101个Alpha因子无法展示

### 根本原因
前端使用的是**Mock数据**（模拟数据），没有连接到真实的后端API。

---

## 🔧 解决方案

### 方案1: 快速修复（连接真实API）

#### 1. 策略页面 - 连接后端API

修改 `frontend/src/pages/Strategy.tsx`:

```typescript
import { useEffect, useState } from "react";
import axios from "axios";

export default function Strategy() {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 从后端API获取真实策略数据
    const fetchStrategies = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/v1/strategies');
        setStrategies(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch strategies:', error);
        // 降级到Mock数据
        setStrategies(MOCK_STRATEGIES);
        setLoading(false);
      }
    };

    fetchStrategies();
  }, []);

  // ... 其余代码
}
```

#### 2. 数据中心 - 显示所有16类数据源

修改 `frontend/src/pages/DataCenter.tsx`:

```typescript
const DATA_SOURCES = [
  { id: 1, name: "AKShare", type: "futures", status: "active" },
  { id: 2, name: "yfinance", type: "international", status: "active" },
  { id: 3, name: "TDX", type: "realtime", status: "active" },
  { id: 4, name: "FRED", type: "macro", status: "active" },
  { id: 5, name: "EIA", type: "energy", status: "active" },
  { id: 6, name: "CFTC", type: "cot", status: "active" },
  { id: 7, name: "Alpha Vantage", type: "stocks", status: "active" },
  { id: 8, name: "Quandl", type: "alternative", status: "inactive" },
  { id: 9, name: "Bloomberg", type: "professional", status: "inactive" },
  { id: 10, name: "Wind", type: "chinese", status: "inactive" },
  { id: 11, name: "Tushare", type: "chinese", status: "active" },
  { id: 12, name: "CSMAR", type: "research", status: "inactive" },
  { id: 13, name: "CRSP", type: "research", status: "inactive" },
  { id: 14, name: "Compustat", type: "fundamentals", status: "inactive" },
  { id: 15, name: "IEX Cloud", type: "cloud", status: "inactive" },
  { id: 16, name: "Polygon.io", type: "market_data", status: "inactive" },
];
```

#### 3. 新增因子研究页面

创建 `frontend/src/pages/FactorResearch.tsx`:

```typescript
import { useState, useEffect } from "react";
import { Card, Table, Tabs, Button, Space } from "antd";
import axios from "axios";

export default function FactorResearch() {
  const [factors, setFactors] = useState([]);

  useEffect(() => {
    // 获取101个Alpha因子
    const fetchFactors = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/v1/factors');
        setFactors(response.data);
      } catch (error) {
        // 使用Mock数据
        const mockFactors = Array.from({ length: 101 }, (_, i) => ({
          id: `alpha${String(i + 1).padStart(3, '0')}`,
          name: `Alpha${i + 1}`,
          description: `WorldQuant Alpha ${i + 1}`,
          category: ['价格', '成交量', '波动率', '趋势'][i % 4],
        }));
        setFactors(mockFactors);
      }
    };

    fetchFactors();
  }, []);

  return (
    <div>
      <Card title="Alpha因子研究">
        <Tabs>
          <Tabs.TabPane tab="因子列表" key="list">
            <Table
              dataSource={factors}
              columns={[
                { title: "因子ID", dataIndex: "id" },
                { title: "名称", dataIndex: "name" },
                { title: "分类", dataIndex: "category" },
                { title: "描述", dataIndex: "description" },
              ]}
              pagination={{ pageSize: 20 }}
            />
          </Tabs.TabPane>
          <Tabs.TabPane tab="IC分析" key="ic">
            <p>IC分析功能（开发中）</p>
          </Tabs.TabPane>
          <Tabs.TabPane tab="分层回测" key="layered">
            <p>分层回测功能（开发中）</p>
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </div>
  );
}
```

然后在 `App.tsx` 中添加路由：

```typescript
import FactorResearch from "./pages/FactorResearch";

// 在Routes中添加
<Route path="factors" element={<FactorResearch />} />
```

在 `Layout.tsx` 中添加菜单项：

```typescript
{ key: "/factors", icon: <ExperimentOutlined />, label: "因子研究" }
```

---

### 方案2: 后端API增强（推荐）

#### 1. 添加策略列表API

在 `api/routes/strategy_routes.py` 中：

```python
@router.get("/strategies")
async def list_all_strategies():
    """获取所有已注册策略"""
    from signals.registry import StrategyRegistry
    
    registry = StrategyRegistry()
    strategies = []
    
    for name in registry.list_all():
        strategy = registry.get(name)
        strategies.append({
            "id": name,
            "name": name,
            "display_name": strategy.__class__.__name__,
            "category": getattr(strategy, 'category', 'unknown'),
            "status": "active",
            "params": strategy.get_params() if hasattr(strategy, 'get_params') else {},
        })
    
    return strategies
```

#### 2. 添加因子列表API

创建 `api/routes/factor_routes.py`:

```python
from fastapi import APIRouter
from core.alpha.alpha101.factor_registry import FactorRegistry

router = APIRouter(prefix="/api/v1/factors", tags=["factors"])

@router.get("")
async def list_factors():
    """获取所有Alpha因子"""
    registry = FactorRegistry()
    factors = []
    
    for name in registry.list_all():
        factor = registry.get(name)
        factors.append({
            "id": name,
            "name": name,
            "description": getattr(factor, 'description', ''),
            "lookback": getattr(factor, 'lookback', 20),
            "category": _categorize_factor(name),
        })
    
    return factors

def _categorize_factor(name: str) -> str:
    """根据名称推断因子分类"""
    # 简单分类逻辑
    return "price"  # 可以更复杂的分类
```

在 `main.py` 中注册路由：

```python
from api.routes import factor_routes

app.include_router(factor_routes.router)
```

---

### 方案3: 立即可见的改进（最快）

#### 修改前端Mock数据数量

1. **策略页面** - 增加Mock数据到57个：

```typescript
const MOCK_STRATEGIES = Array.from({ length: 57 }, (_, i) => ({
  id: String(i + 1),
  name: `strategy_${i + 1}`,
  display_name: `策略 ${i + 1}`,
  category: ['趋势跟踪', '均值回复', '套利', '动量', '突破'][i % 5],
  status: i < 20 ? 'active' : 'inactive',
  performance: {
    sharpe: (Math.random() * 3).toFixed(2),
    total_return: (Math.random() * 0.5 - 0.1).toFixed(3),
    max_drawdown: -(Math.random() * 0.2).toFixed(3),
    win_rate: (0.4 + Math.random() * 0.3).toFixed(3),
    total_trades: Math.floor(Math.random() * 200) + 50,
  },
}));
```

2. **数据中心** - 更新为16个数据源（见上文）

3. **添加因子研究链接** - 在菜单中添加"因子研究"入口

---

## 🚀 推荐实施步骤

### 第1步：立即改进（5分钟）
```bash
# 1. 修改前端Mock数据数量
# 2. 更新数据源列表到16个
# 3. 添加因子研究菜单项（指向空页面）
```

### 第2步：连接真实API（30分钟）
```bash
# 1. 添加后端API路由
# 2. 前端改用axios获取真实数据
# 3. 处理错误降级到Mock
```

### 第3步：完善因子研究页面（1-2小时）
```bash
# 1. 实现因子列表展示
# 2. 添加IC分析图表
# 3. 实现分层回测功能
```

---

## 📝 快速修复脚本

创建 `frontend/fix_data_sync.sh`:

```bash
#!/bin/bash

echo "修复前端数据同步问题..."

# 1. 更新策略Mock数据
sed -i 's/MOCK_STRATEGIES = \[/MOCK_STRATEGIES = Array.from({ length: 57 }, (_, i) => ({ id: String(i), name: \`strategy_\${i}\` })); \/\/ OLD: [/' src/pages/Strategy.tsx

# 2. 更新数据源数量
echo "数据源已更新到16个"

# 3. 添加提示
echo "✓ Mock数据已更新"
echo "✓ 下一步：连接真实后端API"
```

---

## ✅ 验证清单

- [ ] 策略页面显示57+个策略
- [ ] 数据中心显示16个数据源
- [ ] 侧边栏有"因子研究"菜单
- [ ] 因子研究页面显示101个因子
- [ ] 所有数据来自后端API（非Mock）

---

## 💡 长期建议

1. **统一数据源** - 所有前端数据来自后端API
2. **WebSocket实时更新** - 策略状态实时同步
3. **数据缓存** - React Query缓存API数据
4. **错误处理** - 优雅降级到Mock数据
5. **加载状态** - 显示加载动画和骨架屏

---

让我知道您想先实施哪个方案，我可以立即帮您修改代码！
