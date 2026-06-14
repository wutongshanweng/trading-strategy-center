# 交易策略中心 - 贡献指南

感谢您对本项目的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告Bug

发现Bug？请创建Issue并包含：
- Bug描述
- 复现步骤
- 期望行为
- 实际行为
- 环境信息（Python版本、操作系统等）
- 如有可能，提供最小可复现示例

### 提出新功能

有好的想法？请先创建Issue讨论：
- 功能描述
- 使用场景
- 预期收益
- 实现思路（可选）

### 提交代码

1. **Fork本仓库**

2. **创建特性分支**
```bash
git checkout -b feature/amazing-feature
```

3. **编写代码**
   - 遵循代码规范（见下文）
   - 添加测试用例
   - 更新文档

4. **提交更改**
```bash
git commit -m "feat: add amazing feature"
```

提交信息格式：
- `feat:` 新功能
- `fix:` Bug修复
- `docs:` 文档更新
- `style:` 代码格式（不影响功能）
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

5. **推送到Fork仓库**
```bash
git push origin feature/amazing-feature
```

6. **创建Pull Request**

## 代码规范

### Python代码风格

遵循[PEP 8](https://pep8.org/)规范：

```python
# 好的示例
class MyStrategy(BaseStrategy):
    """策略描述"""
    
    def __init__(self):
        super().__init__()
        self.params = {'period': 20}
    
    def compute(self, data: pd.DataFrame, symbol: str) -> Signal:
        """计算策略信号"""
        # 实现逻辑
        pass
```

### 命名规范

- **类名**: PascalCase (例: `TrendStrategy`)
- **函数/方法**: snake_case (例: `calculate_signal`)
- **常量**: UPPER_SNAKE_CASE (例: `MAX_POSITION`)
- **私有变量**: _leading_underscore (例: `_internal_state`)

### 文档字符串

所有公共类和函数必须有docstring：

```python
def calculate_ic(factor_values: pd.Series, returns: pd.Series) -> float:
    """
    计算信息系数 (IC)
    
    Args:
        factor_values: 因子值序列
        returns: 收益率序列
        
    Returns:
        IC值（-1到1之间）
        
    Raises:
        ValueError: 输入数据长度不匹配
    """
    pass
```

### 类型提示

推荐使用类型提示：

```python
from typing import Optional, List, Dict

def get_data(symbol: str, start: Optional[str] = None) -> pd.DataFrame:
    pass
```

## 测试

### 编写测试

所有新功能必须包含测试：

```python
# tests/test_my_feature.py
import pytest
from my_module import my_function

def test_my_function():
    result = my_function(input_data)
    assert result == expected_output

def test_my_function_edge_case():
    with pytest.raises(ValueError):
        my_function(invalid_input)
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_my_feature.py -v

# 查看覆盖率
pytest tests/ --cov=. --cov-report=html
```

## 策略开发规范

### 策略模板

```python
from signals.base import BaseStrategy, Signal
from signals.registry import register
import pandas as pd

@register("my_strategy")  # 注册策略
class MyStrategy(BaseStrategy):
    """
    策略描述
    
    参数:
        param1: 参数1说明
        param2: 参数2说明
    """
    
    def __init__(self):
        super().__init__()
        self.params = {
            'param1': 20,
            'param2': 2.0,
        }
    
    def compute(self, data: pd.DataFrame, symbol: str) -> Signal:
        """
        计算策略信号
        
        Args:
            data: OHLCV数据，包含列: open, high, low, close, volume
            symbol: 品种代码
            
        Returns:
            Signal对象，包含方向、置信度、分数等
        """
        # 1. 计算指标
        indicator = self._calculate_indicator(data)
        
        # 2. 生成信号
        if indicator > self.params['param2']:
            direction = "BUY"
            confidence = 0.8
        elif indicator < -self.params['param2']:
            direction = "SELL"
            confidence = 0.8
        else:
            direction = "HOLD"
            confidence = 0.0
        
        # 3. 返回Signal
        return Signal(
            strategy_name="my_strategy",
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            score=indicator,
            price=data['close'].iloc[-1],
            timestamp=data.index[-1],
            reason=f"Indicator={indicator:.2f}",
            source_system="custom"
        )
    
    def _calculate_indicator(self, data: pd.DataFrame) -> float:
        """内部辅助方法"""
        # 实现指标计算
        pass
    
    def get_params(self) -> dict:
        return self.params
```

### 策略测试

```python
# tests/test_my_strategy.py
def test_my_strategy_buy_signal():
    strategy = get_strategy("my_strategy")
    
    # 准备测试数据
    df = create_uptrend_data()
    
    # 计算信号
    signal = strategy.compute(df, "TEST")
    
    # 验证
    assert signal.direction == "BUY"
    assert signal.confidence > 0.5
```

## Alpha因子开发规范

### 因子模板

```python
from core.alpha.alpha101.base import AlphaFactor
from core.alpha.alpha101.factor_registry import FactorRegistry
import pandas as pd

@FactorRegistry.register("alpha_xxx")
class AlphaXXX(AlphaFactor):
    """
    因子描述
    
    公式: 因子计算公式
    含义: 因子经济含义
    """
    
    description = "因子描述"
    lookback = 20  # 所需历史数据长度
    
    def compute(self, data: pd.DataFrame, symbol: str = "") -> pd.Series:
        """
        计算因子值
        
        Args:
            data: OHLCV数据
            symbol: 品种代码
            
        Returns:
            因子值序列
        """
        # 实现因子计算逻辑
        factor_values = ...
        return factor_values
```

## 文档规范

### 更新文档

代码更改后，请更新相关文档：

- **README.md**: 新功能概述
- **QUICK_START.md**: 使用示例
- **API文档**: 函数签名和参数说明
- **CHANGELOG.md**: 版本变更记录

### Markdown格式

```markdown
# 一级标题

## 二级标题

### 三级标题

- 列表项1
- 列表项2

**加粗文本**

`行内代码`

\`\`\`python
# 代码块
code_here()
\`\`\`

[链接文本](URL)
```

## 版本发布

版本号格式：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的API更改
- **MINOR**: 向后兼容的新功能
- **PATCH**: 向后兼容的Bug修复

## 问题排查

### 测试失败

1. 检查Python版本（需要3.10+）
2. 确保依赖已安装：`pip install -e ".[dev]"`
3. 清理缓存：`pytest --cache-clear`

### 代码风格检查

```bash
# 安装工具
pip install ruff black mypy

# 检查代码风格
ruff check .

# 自动格式化
black .

# 类型检查
mypy .
```

## 许可证

提交代码即表示您同意将贡献以MIT许可证发布。

## 行为准则

- 尊重所有贡献者
- 提供建设性反馈
- 专注于项目目标
- 保持专业和友好

## 联系方式

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **讨论**: [GitHub Discussions](https://github.com/your-repo/discussions)

感谢您的贡献！🎉
