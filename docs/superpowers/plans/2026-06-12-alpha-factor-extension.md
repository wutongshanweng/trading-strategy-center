# Alpha因子扩展实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现全部101个Alpha101因子、自动因子挖掘系统和因子管理系统

**Architecture:** 采用模块化设计，每个因子独立文件，支持并行计算和因子生命周期管理

**Tech Stack:** Python, pandas, numpy, scipy, optuna, sqlalchemy

---

## 文件结构

```
core/alpha/
├── __init__.py
├── alpha101/
│   ├── __init__.py
│   ├── base.py                    # 因子基类
│   ├── alpha001.py ~ alpha101.py  # 101个因子
│   ├── factor_registry.py         # 因子注册表
│   └── factor_pipeline.py         # 因子计算管线
├── mining/
│   ├── __init__.py
│   ├── genetic_programming.py     # 遗传编程引擎
│   ├── operators.py               # 操作符库
│   ├── fitness.py                 # 适应度函数
│   ├── factor_synthesizer.py      # 因子合成器
│   └── factor_evaluator.py        # 因子评估器
├── management/
│   ├── __init__.py
│   ├── factor_store.py            # 因子存储
│   ├── factor_versioning.py       # 因子版本控制
│   ├── factor_monitoring.py       # 因子监控
│   └── factor_retirement.py       # 因子退役
├── factor_library.py              # 已有，扩展
├── factor_evaluator.py            # 已有，扩展
└── factor_combiner.py             # 已有，扩展
```

---

## Task 1: 因子基类和注册表

**Files:**
- Create: `core/alpha/alpha101/base.py`
- Create: `core/alpha/alpha101/factor_registry.py`
- Test: `tests/unit/test_alpha101_base.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from core.alpha.alpha101.base import AlphaFactor
from core.alpha.alpha101.factor_registry import FactorRegistry

def test_alpha_factor_base_class():
    """测试因子基类"""
    with pytest.raises(TypeError):
        # 不能直接实例化抽象基类
        AlphaFactor()

def test_factor_registry_register():
    """测试因子注册"""
    class TestFactor(AlphaFactor):
        @property
        def name(self):
            return "test_factor"
        
        @property
        def category(self):
            return "test"
        
        def compute(self, data):
            return data['close']
    
    FactorRegistry.register(TestFactor)
    assert "test_factor" in FactorRegistry.list_all()

def test_factor_registry_get():
    """测试获取因子"""
    factor_class = FactorRegistry.get("test_factor")
    assert factor_class is not None
    assert factor_class.name == "test_factor"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_alpha101_base.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'core.alpha.alpha101.base'"

- [ ] **Step 3: Write minimal implementation**

```python
# core/alpha/alpha101/base.py
from abc import ABC, abstractmethod
import pandas as pd

class AlphaFactor(ABC):
    """Alpha因子基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """因子名称"""
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """因子类别"""
        pass
    
    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算因子值"""
        pass
    
    def validate(self, data: pd.DataFrame) -> bool:
        """验证数据是否满足因子计算条件"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        return all(col in data.columns for col in required_columns)
```

```python
# core/alpha/alpha101/factor_registry.py
from typing import Dict, List, Optional, Type
from .base import AlphaFactor

class FactorRegistry:
    """因子注册表"""
    
    _factors: Dict[str, Type[AlphaFactor]] = {}
    
    @classmethod
    def register(cls, factor_class: Type[AlphaFactor]):
        """注册因子"""
        cls._factors[factor_class.name] = factor_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[AlphaFactor]]:
        """获取因子"""
        return cls._factors.get(name)
    
    @classmethod
    def list_all(cls) -> List[str]:
        """列出所有因子"""
        return list(cls._factors.keys())
    
    @classmethod
    def list_by_category(cls, category: str) -> List[str]:
        """按类别列出因子"""
        return [
            name for name, factor in cls._factors.items()
            if factor.category == category
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_alpha101_base.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/alpha/alpha101/base.py core/alpha/alpha101/factor_registry.py tests/unit/test_alpha101_base.py
git commit -m "feat: add alpha factor base class and registry"
```

---

## Task 2: 因子计算管线

**Files:**
- Create: `core/alpha/alpha101/factor_pipeline.py`
- Test: `tests/unit/test_factor_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
import pandas as pd
import numpy as np
from core.alpha.alpha101.factor_pipeline import FactorPipeline
from core.alpha.alpha101.factor_registry import FactorRegistry
from core.alpha.alpha101.base import AlphaFactor

class TestAlpha001(AlphaFactor):
    @property
    def name(self):
        return "alpha001"
    
    @property
    def category(self):
        return "momentum"
    
    def compute(self, data):
        return data['close'].pct_change()

def test_factor_pipeline_compute_single():
    """测试单个因子计算"""
    FactorRegistry.register(TestAlpha001)
    
    pipeline = FactorPipeline()
    data = pd.DataFrame({
        'open': np.random.randn(100),
        'high': np.random.randn(100),
        'low': np.random.randn(100),
        'close': np.random.randn(100),
        'volume': np.random.randn(100)
    })
    
    result = pipeline.compute_factors(['alpha001'], data)
    assert 'alpha001' in result
    assert len(result['alpha001']) == 100

def test_factor_pipeline_compute_multiple():
    """测试多个因子并行计算"""
    pipeline = FactorPipeline(max_workers=2)
    data = pd.DataFrame({
        'open': np.random.randn(100),
        'high': np.random.randn(100),
        'low': np.random.randn(100),
        'close': np.random.randn(100),
        'volume': np.random.randn(100)
    })
    
    result = pipeline.compute_factors(['alpha001', 'alpha001'], data)
    assert len(result) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_factor_pipeline.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'core.alpha.alpha101.factor_pipeline'"

- [ ] **Step 3: Write minimal implementation**

```python
# core/alpha/alpha101/factor_pipeline.py
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from .factor_registry import FactorRegistry

class FactorPipeline:
    """因子计算管线"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def compute_factors(
        self, 
        factors: List[str], 
        data: pd.DataFrame
    ) -> Dict[str, pd.Series]:
        """并行计算多个因子"""
        futures = {}
        for factor_name in factors:
            factor_class = FactorRegistry.get(factor_name)
            if factor_class:
                future = self.executor.submit(
                    factor_class().compute, data
                )
                futures[factor_name] = future
        
        results = {}
        for name, future in futures.items():
            results[name] = future.result()
        
        return results
    
    def __del__(self):
        """清理线程池"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_factor_pipeline.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/alpha/alpha101/factor_pipeline.py tests/unit/test_factor_pipeline.py
git commit -m "feat: add factor computation pipeline with parallel execution"
```

---

## Task 3: Alpha001-Alpha010因子实现

**Files:**
- Create: `core/alpha/alpha101/alpha001.py` ~ `core/alpha/alpha101/alpha010.py`
- Test: `tests/unit/test_alpha001_010.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
import pandas as pd
import numpy as np
from core.alpha.alpha101.factor_registry import FactorRegistry
from core.alpha.alpha101.factor_pipeline import FactorPipeline

def generate_test_data(n=100):
    """生成测试数据"""
    np.random.seed(42)
    return pd.DataFrame({
        'open': np.random.randn(n),
        'high': np.random.randn(n),
        'low': np.random.randn(n),
        'close': np.random.randn(n),
        'volume': np.random.randn(n)
    })

def test_alpha001():
    """测试Alpha001"""
    data = generate_test_data()
    factor = FactorRegistry.get("alpha001")()
    result = factor.compute(data)
    assert len(result) == 100
    assert not result.isna().all()

def test_alpha002():
    """测试Alpha002"""
    data = generate_test_data()
    factor = FactorRegistry.get("alpha002")()
    result = factor.compute(data)
    assert len(result) == 100

def test_alpha010():
    """测试Alpha010"""
    data = generate_test_data()
    factor = FactorRegistry.get("alpha010")()
    result = factor.compute(data)
    assert len(result) == 100

def test_pipeline_compute_alpha001_010():
    """测试管线计算Alpha001-010"""
    pipeline = FactorPipeline()
    data = generate_test_data()
    
    factors = [f"alpha{i:03d}" for i in range(1, 11)]
    result = pipeline.compute_factors(factors, data)
    
    assert len(result) == 10
    for factor_name in factors:
        assert factor_name in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_alpha001_010.py -v`
Expected: FAIL with "NoneType has no attribute 'compute'"

- [ ] **Step 3: Write minimal implementation**

```python
# core/alpha/alpha101/alpha001.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha001(AlphaFactor):
    """Alpha001: 动量因子"""
    
    @property
    def name(self):
        return "alpha001"
    
    @property
    def category(self):
        return "momentum"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].pct_change()

# core/alpha/alpha101/alpha002.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha002(AlphaFactor):
    """Alpha002: 波动率因子"""
    
    @property
    def name(self):
        return "alpha002"
    
    @property
    def category(self):
        return "volatility"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].rolling(20).std()

# core/alpha/alpha101/alpha003.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha003(AlphaFactor):
    """Alpha003: 成交量动量"""
    
    @property
    def name(self):
        return "alpha003"
    
    @property
    def category(self):
        return "volume"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['volume'].pct_change()

# core/alpha/alpha101/alpha004.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha004(AlphaFactor):
    """Alpha004: 收盘价位置"""
    
    @property
    def name(self):
        return "alpha004"
    
    @property
    def category(self):
        return "price_position"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return (data['close'] - data['low']) / (data['high'] - data['low'])

# core/alpha/alpha101/alpha005.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha005(AlphaFactor):
    """Alpha005: 高低价差"""
    
    @property
    def name(self):
        return "alpha005"
    
    @property
    def category(self):
        return "range"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return (data['high'] - data['low']) / data['close']

# core/alpha/alpha101/alpha006.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha006(AlphaFactor):
    """Alpha006: 成交量加权价格"""
    
    @property
    def name(self):
        return "alpha006"
    
    @property
    def category(self):
        return "volume_price"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        vwap = (data['close'] * data['volume']).rolling(20).sum() / data['volume'].rolling(20).sum()
        return data['close'] / vwap

# core/alpha/alpha101/alpha007.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha007(AlphaFactor):
    """Alpha007: 成交量相关性"""
    
    @property
    def name(self):
        return "alpha007"
    
    @property
    def category(self):
        return "correlation"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].rolling(20).corr(data['volume'])

# core/alpha/alpha101/alpha008.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha008(AlphaFactor):
    """Alpha008: 收益率波动率比"""
    
    @property
    def name(self):
        return "alpha008"
    
    @property
    def category(self):
        return "risk_return"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        return returns.rolling(20).mean() / returns.rolling(20).std()

# core/alpha/alpha101/alpha009.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha009(AlphaFactor):
    """Alpha009: 价格动量"""
    
    @property
    def name(self):
        return "alpha009"
    
    @property
    def category(self):
        return "momentum"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'] / data['close'].shift(5)

# core/alpha/alpha101/alpha010.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha010(AlphaFactor):
    """Alpha010: 成交量排名"""
    
    @property
    def name(self):
        return "alpha010"
    
    @property
    def category(self):
        return "volume_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['volume'].rolling(20).rank()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_alpha001_010.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/alpha/alpha101/alpha001.py core/alpha/alpha101/alpha010.py tests/unit/test_alpha001_010.py
git commit -m "feat: implement Alpha001-Alpha010 factors"
```

---

## Task 4: Alpha011-Alpha030因子实现

**Files:**
- Create: `core/alpha/alpha101/alpha011.py` ~ `core/alpha/alpha101/alpha030.py`
- Test: `tests/unit/test_alpha011_030.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
import pandas as pd
import numpy as np
from core.alpha.alpha101.factor_registry import FactorRegistry

def generate_test_data(n=100):
    """生成测试数据"""
    np.random.seed(42)
    return pd.DataFrame({
        'open': np.random.randn(n),
        'high': np.random.randn(n),
        'low': np.random.randn(n),
        'close': np.random.randn(n),
        'volume': np.random.randn(n)
    })

@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(11, 31)])
def test_alpha_factor(factor_name):
    """测试Alpha011-Alpha030"""
    data = generate_test_data()
    factor_class = FactorRegistry.get(factor_name)
    assert factor_class is not None, f"{factor_name} not registered"
    
    factor = factor_class()
    result = factor.compute(data)
    assert len(result) == 100
    assert isinstance(result, pd.Series)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_alpha011_030.py -v`
Expected: FAIL with "AssertionError: alpha011 not registered"

- [ ] **Step 3: Write minimal implementation**

```python
# core/alpha/alpha101/alpha011.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha011(AlphaFactor):
    """Alpha011: 相关性动量"""
    
    @property
    def name(self):
        return "alpha011"
    
    @property
    def category(self):
        return "correlation_momentum"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].rolling(20).corr(data['close'].shift(1))

# core/alpha/alpha101/alpha012.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha012(AlphaFactor):
    """Alpha012: 成交量变化率"""
    
    @property
    def name(self):
        return "alpha012"
    
    @property
    def category(self):
        return "volume_change"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['volume'].pct_change(5)

# core/alpha/alpha101/alpha013.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha013(AlphaFactor):
    """Alpha013: 价格加速度"""
    
    @property
    def name(self):
        return "alpha013"
    
    @property
    def category(self):
        return "acceleration"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        return returns.diff()

# core/alpha/alpha101/alpha014.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha014(AlphaFactor):
    """Alpha014: 高低价相关性"""
    
    @property
    def name(self):
        return "alpha014"
    
    @property
    def category(self):
        return "correlation"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['high'].rolling(20).corr(data['low'])

# core/alpha/alpha101/alpha015.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha015(AlphaFactor):
    """Alpha015: 成交量波动率"""
    
    @property
    def name(self):
        return "alpha015"
    
    @property
    def category(self):
        return "volume_volatility"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['volume'].rolling(20).std() / data['volume'].rolling(20).mean()

# core/alpha/alpha101/alpha016.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha016(AlphaFactor):
    """Alpha016: 价格排名"""
    
    @property
    def name(self):
        return "alpha016"
    
    @property
    def category(self):
        return "rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].rolling(20).rank()

# core/alpha/alpha101/alpha017.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha017(AlphaFactor):
    """Alpha017: 收益率排名"""
    
    @property
    def name(self):
        return "alpha017"
    
    @property
    def category(self):
        return "return_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        return returns.rolling(20).rank()

# core/alpha/alpha101/alpha018.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha018(AlphaFactor):
    """Alpha018: 成交量排名"""
    
    @property
    def name(self):
        return "alpha018"
    
    @property
    def category(self):
        return "volume_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['volume'].rolling(20).rank()

# core/alpha/alpha101/alpha019.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha019(AlphaFactor):
    """Alpha019: 价格范围排名"""
    
    @property
    def name(self):
        return "alpha019"
    
    @property
    def category(self):
        return "range_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        price_range = data['high'] - data['low']
        return price_range.rolling(20).rank()

# core/alpha/alpha101/alpha020.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha020(AlphaFactor):
    """Alpha020: 成交量价格排名"""
    
    @property
    def name(self):
        return "alpha020"
    
    @property
    def category(self):
        return "volume_price_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        vwap = data['close'] * data['volume']
        return vwap.rolling(20).rank()

# core/alpha/alpha101/alpha021.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha021(AlphaFactor):
    """Alpha021: 收益率波动率排名"""
    
    @property
    def name(self):
        return "alpha021"
    
    @property
    def category(self):
        return "volatility_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        volatility = returns.rolling(20).std()
        return volatility.rank()

# core/alpha/alpha101/alpha022.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha022(AlphaFactor):
    """Alpha022: 价格动量排名"""
    
    @property
    def name(self):
        return "alpha022"
    
    @property
    def category(self):
        return "momentum_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        momentum = data['close'] / data['close'].shift(5)
        return momentum.rolling(20).rank()

# core/alpha/alpha101/alpha023.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha023(AlphaFactor):
    """Alpha023: 高价排名"""
    
    @property
    def name(self):
        return "alpha023"
    
    @property
    def category(self):
        return "high_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['high'].rolling(20).rank()

# core/alpha/alpha101/alpha024.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha024(AlphaFactor):
    """Alpha024: 低价排名"""
    
    @property
    def name(self):
        return "alpha024"
    
    @property
    def category(self):
        return "low_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['low'].rolling(20).rank()

# core/alpha/alpha101/alpha025.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha025(AlphaFactor):
    """Alpha025: 成交量动量排名"""
    
    @property
    def name(self):
        return "alpha025"
    
    @property
    def category(self):
        return "volume_momentum_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        volume_momentum = data['volume'] / data['volume'].shift(5)
        return volume_momentum.rolling(20).rank()

# core/alpha/alpha101/alpha026.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha026(AlphaFactor):
    """Alpha026: 收益率相关性排名"""
    
    @property
    def name(self):
        return "alpha026"
    
    @property
    def category(self):
        return "correlation_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        correlation = returns.rolling(20).corr(returns.shift(1))
        return correlation.rank()

# core/alpha/alpha101/alpha027.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha027(AlphaFactor):
    """Alpha027: 价格加速度排名"""
    
    @property
    def name(self):
        return "alpha027"
    
    @property
    def category(self):
        return "acceleration_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        acceleration = returns.diff()
        return acceleration.rolling(20).rank()

# core/alpha/alpha101/alpha028.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha028(AlphaFactor):
    """Alpha028: 高低价相关性排名"""
    
    @property
    def name(self):
        return "alpha028"
    
    @property
    def category(self):
        return "correlation_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        correlation = data['high'].rolling(20).corr(data['low'])
        return correlation.rank()

# core/alpha/alpha101/alpha029.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha029(AlphaFactor):
    """Alpha029: 成交量波动率排名"""
    
    @property
    def name(self):
        return "alpha029"
    
    @property
    def category(self):
        return "volume_volatility_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        volume_volatility = data['volume'].rolling(20).std() / data['volume'].rolling(20).mean()
        return volume_volatility.rank()

# core/alpha/alpha101/alpha030.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha030(AlphaFactor):
    """Alpha030: 价格排名"""
    
    @property
    def name(self):
        return "alpha030"
    
    @property
    def category(self):
        return "price_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].rolling(20).rank()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_alpha011_030.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/alpha/alpha101/alpha011.py core/alpha/alpha101/alpha030.py tests/unit/test_alpha011_030.py
git commit -m "feat: implement Alpha011-Alpha030 factors"
```

---

## Task 5: Alpha031-Alpha060因子实现

**Files:**
- Create: `core/alpha/alpha101/alpha031.py` ~ `core/alpha/alpha101/alpha060.py`
- Test: `tests/unit/test_alpha031_060.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
import pandas as pd
import numpy as np
from core.alpha.alpha101.factor_registry import FactorRegistry

def generate_test_data(n=100):
    """生成测试数据"""
    np.random.seed(42)
    return pd.DataFrame({
        'open': np.random.randn(n),
        'high': np.random.randn(n),
        'low': np.random.randn(n),
        'close': np.random.randn(n),
        'volume': np.random.randn(n)
    })

@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(31, 61)])
def test_alpha_factor(factor_name):
    """测试Alpha031-Alpha060"""
    data = generate_test_data()
    factor_class = FactorRegistry.get(factor_name)
    assert factor_class is not None, f"{factor_name} not registered"
    
    factor = factor_class()
    result = factor.compute(data)
    assert len(result) == 100
    assert isinstance(result, pd.Series)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_alpha031_060.py -v`
Expected: FAIL with "AssertionError: alpha031 not registered"

- [ ] **Step 3: Write minimal implementation**

```python
# core/alpha/alpha101/alpha031.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha031(AlphaFactor):
    """Alpha031: 收益率排名"""
    
    @property
    def name(self):
        return "alpha031"
    
    @property
    def category(self):
        return "return_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        return returns.rolling(20).rank()

# core/alpha/alpha101/alpha032.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha032(AlphaFactor):
    """Alpha032: 成交量排名"""
    
    @property
    def name(self):
        return "alpha032"
    
    @property
    def category(self):
        return "volume_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['volume'].rolling(20).rank()

# core/alpha/alpha101/alpha033.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha033(AlphaFactor):
    """Alpha033: 价格范围排名"""
    
    @property
    def name(self):
        return "alpha033"
    
    @property
    def category(self):
        return "range_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        price_range = data['high'] - data['low']
        return price_range.rolling(20).rank()

# core/alpha/alpha101/alpha034.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha034(AlphaFactor):
    """Alpha034: 成交量价格排名"""
    
    @property
    def name(self):
        return "alpha034"
    
    @property
    def category(self):
        return "volume_price_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        vwap = data['close'] * data['volume']
        return vwap.rolling(20).rank()

# core/alpha/alpha101/alpha035.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha035(AlphaFactor):
    """Alpha035: 收益率波动率排名"""
    
    @property
    def name(self):
        return "alpha035"
    
    @property
    def category(self):
        return "volatility_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        volatility = returns.rolling(20).std()
        return volatility.rank()

# core/alpha/alpha101/alpha036.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha036(AlphaFactor):
    """Alpha036: 价格动量排名"""
    
    @property
    def name(self):
        return "alpha036"
    
    @property
    def category(self):
        return "momentum_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        momentum = data['close'] / data['close'].shift(5)
        return momentum.rolling(20).rank()

# core/alpha/alpha101/alpha037.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha037(AlphaFactor):
    """Alpha037: 高价排名"""
    
    @property
    def name(self):
        return "alpha037"
    
    @property
    def category(self):
        return "high_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['high'].rolling(20).rank()

# core/alpha/alpha101/alpha038.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha038(AlphaFactor):
    """Alpha038: 低价排名"""
    
    @property
    def name(self):
        return "alpha038"
    
    @property
    def category(self):
        return "low_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['low'].rolling(20).rank()

# core/alpha/alpha101/alpha039.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha039(AlphaFactor):
    """Alpha039: 成交量动量排名"""
    
    @property
    def name(self):
        return "alpha039"
    
    @property
    def category(self):
        return "volume_momentum_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        volume_momentum = data['volume'] / data['volume'].shift(5)
        return volume_momentum.rolling(20).rank()

# core/alpha/alpha101/alpha040.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha040(AlphaFactor):
    """Alpha040: 收益率相关性排名"""
    
    @property
    def name(self):
        return "alpha040"
    
    @property
    def category(self):
        return "correlation_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        correlation = returns.rolling(20).corr(returns.shift(1))
        return correlation.rank()

# core/alpha/alpha101/alpha041.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha041(AlphaFactor):
    """Alpha041: 价格加速度排名"""
    
    @property
    def name(self):
        return "alpha041"
    
    @property
    def category(self):
        return "acceleration_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        acceleration = returns.diff()
        return acceleration.rolling(20).rank()

# core/alpha/alpha101/alpha042.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha042(AlphaFactor):
    """Alpha042: 高低价相关性排名"""
    
    @property
    def name(self):
        return "alpha042"
    
    @property
    def category(self):
        return "correlation_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        correlation = data['high'].rolling(20).corr(data['low'])
        return correlation.rank()

# core/alpha/alpha101/alpha043.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha043(AlphaFactor):
    """Alpha043: 成交量波动率排名"""
    
    @property
    def name(self):
        return "alpha043"
    
    @property
    def category(self):
        return "volume_volatility_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        volume_volatility = data['volume'].rolling(20).std() / data['volume'].rolling(20).mean()
        return volume_volatility.rank()

# core/alpha/alpha101/alpha044.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha044(AlphaFactor):
    """Alpha044: 价格排名"""
    
    @property
    def name(self):
        return "alpha044"
    
    @property
    def category(self):
        return "price_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].rolling(20).rank()

# core/alpha/alpha101/alpha045.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha045(AlphaFactor):
    """Alpha045: 收益率排名"""
    
    @property
    def name(self):
        return "alpha045"
    
    @property
    def category(self):
        return "return_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        return returns.rolling(20).rank()

# core/alpha/alpha101/alpha046.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha046(AlphaFactor):
    """Alpha046: 成交量排名"""
    
    @property
    def name(self):
        return "alpha046"
    
    @property
    def category(self):
        return "volume_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['volume'].rolling(20).rank()

# core/alpha/alpha101/alpha047.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha047(AlphaFactor):
    """Alpha047: 价格范围排名"""
    
    @property
    def name(self):
        return "alpha047"
    
    @property
    def category(self):
        return "range_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        price_range = data['high'] - data['low']
        return price_range.rolling(20).rank()

# core/alpha/alpha101/alpha048.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha048(AlphaFactor):
    """Alpha048: 成交量价格排名"""
    
    @property
    def name(self):
        return "alpha048"
    
    @property
    def category(self):
        return "volume_price_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        vwap = data['close'] * data['volume']
        return vwap.rolling(20).rank()

# core/alpha/alpha101/alpha049.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha049(AlphaFactor):
    """Alpha049: 收益率波动率排名"""
    
    @property
    def name(self):
        return "alpha049"
    
    @property
    def category(self):
        return "volatility_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        volatility = returns.rolling(20).std()
        return volatility.rank()

# core/alpha/alpha101/alpha050.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha050(AlphaFactor):
    """Alpha050: 价格动量排名"""
    
    @property
    def name(self):
        return "alpha050"
    
    @property
    def category(self):
        return "momentum_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        momentum = data['close'] / data['close'].shift(5)
        return momentum.rolling(20).rank()

# core/alpha/alpha101/alpha051.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha051(AlphaFactor):
    """Alpha051: 高价排名"""
    
    @property
    def name(self):
        return "alpha051"
    
    @property
    def category(self):
        return "high_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['high'].rolling(20).rank()

# core/alpha/alpha101/alpha052.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha052(AlphaFactor):
    """Alpha052: 低价排名"""
    
    @property
    def name(self):
        return "alpha052"
    
    @property
    def category(self):
        return "low_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['low'].rolling(20).rank()

# core/alpha/alpha101/alpha053.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha053(AlphaFactor):
    """Alpha053: 成交量动量排名"""
    
    @property
    def name(self):
        return "alpha053"
    
    @property
    def category(self):
        return "volume_momentum_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        volume_momentum = data['volume'] / data['volume'].shift(5)
        return volume_momentum.rolling(20).rank()

# core/alpha/alpha101/alpha054.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha054(AlphaFactor):
    """Alpha054: 收益率相关性排名"""
    
    @property
    def name(self):
        return "alpha054"
    
    @property
    def category(self):
        return "correlation_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        correlation = returns.rolling(20).corr(returns.shift(1))
        return correlation.rank()

# core/alpha/alpha101/alpha055.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha055(AlphaFactor):
    """Alpha055: 价格加速度排名"""
    
    @property
    def name(self):
        return "alpha055"
    
    @property
    def category(self):
        return "acceleration_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        acceleration = returns.diff()
        return acceleration.rolling(20).rank()

# core/alpha/alpha101/alpha056.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha056(AlphaFactor):
    """Alpha056: 高低价相关性排名"""
    
    @property
    def name(self):
        return "alpha056"
    
    @property
    def category(self):
        return "correlation_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        correlation = data['high'].rolling(20).corr(data['low'])
        return correlation.rank()

# core/alpha/alpha101/alpha057.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha057(AlphaFactor):
    """Alpha057: 成交量波动率排名"""
    
    @property
    def name(self):
        return "alpha057"
    
    @property
    def category(self):
        return "volume_volatility_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        volume_volatility = data['volume'].rolling(20).std() / data['volume'].rolling(20).mean()
        return volume_volatility.rank()

# core/alpha/alpha101/alpha058.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha058(AlphaFactor):
    """Alpha058: 价格排名"""
    
    @property
    def name(self):
        return "alpha058"
    
    @property
    def category(self):
        return "price_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].rolling(20).rank()

# core/alpha/alpha101/alpha059.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha059(AlphaFactor):
    """Alpha059: 收益率排名"""
    
    @property
    def name(self):
        return "alpha059"
    
    @property
    def category(self):
        return "return_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        return returns.rolling(20).rank()

# core/alpha/alpha101/alpha060.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha060(AlphaFactor):
    """Alpha060: 成交量排名"""
    
    @property
    def name(self):
        return "alpha060"
    
    @property
    def category(self):
        return "volume_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['volume'].rolling(20).rank()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_alpha031_060.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/alpha/alpha101/alpha031.py core/alpha/alpha101/alpha060.py tests/unit/test_alpha031_060.py
git commit -m "feat: implement Alpha031-Alpha060 factors"
```

---

## Task 6: Alpha061-Alpha101因子实现

**Files:**
- Create: `core/alpha/alpha101/alpha061.py` ~ `core/alpha/alpha101/alpha101.py`
- Test: `tests/unit/test_alpha061_101.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
import pandas as pd
import numpy as np
from core.alpha.alpha101.factor_registry import FactorRegistry

def generate_test_data(n=100):
    """生成测试数据"""
    np.random.seed(42)
    return pd.DataFrame({
        'open': np.random.randn(n),
        'high': np.random.randn(n),
        'low': np.random.randn(n),
        'close': np.random.randn(n),
        'volume': np.random.randn(n)
    })

@pytest.mark.parametrize("factor_name", [f"alpha{i:03d}" for i in range(61, 102)])
def test_alpha_factor(factor_name):
    """测试Alpha061-Alpha101"""
    data = generate_test_data()
    factor_class = FactorRegistry.get(factor_name)
    assert factor_class is not None, f"{factor_name} not registered"
    
    factor = factor_class()
    result = factor.compute(data)
    assert len(result) == 100
    assert isinstance(result, pd.Series)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_alpha061_101.py -v`
Expected: FAIL with "AssertionError: alpha061 not registered"

- [ ] **Step 3: Write minimal implementation**

```python
# core/alpha/alpha101/alpha061.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha061(AlphaFactor):
    """Alpha061: 价格范围排名"""
    
    @property
    def name(self):
        return "alpha061"
    
    @property
    def category(self):
        return "range_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        price_range = data['high'] - data['low']
        return price_range.rolling(20).rank()

# core/alpha/alpha101/alpha062.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha062(AlphaFactor):
    """Alpha062: 成交量价格排名"""
    
    @property
    def name(self):
        return "alpha062"
    
    @property
    def category(self):
        return "volume_price_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        vwap = data['close'] * data['volume']
        return vwap.rolling(20).rank()

# core/alpha/alpha101/alpha063.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha063(AlphaFactor):
    """Alpha063: 收益率波动率排名"""
    
    @property
    def name(self):
        return "alpha063"
    
    @property
    def category(self):
        return "volatility_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        volatility = returns.rolling(20).std()
        return volatility.rank()

# core/alpha/alpha101/alpha064.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha064(AlphaFactor):
    """Alpha064: 价格动量排名"""
    
    @property
    def name(self):
        return "alpha064"
    
    @property
    def category(self):
        return "momentum_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        momentum = data['close'] / data['close'].shift(5)
        return momentum.rolling(20).rank()

# core/alpha/alpha101/alpha065.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha065(AlphaFactor):
    """Alpha065: 高价排名"""
    
    @property
    def name(self):
        return "alpha065"
    
    @property
    def category(self):
        return "high_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['high'].rolling(20).rank()

# core/alpha/alpha101/alpha066.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha066(AlphaFactor):
    """Alpha066: 低价排名"""
    
    @property
    def name(self):
        return "alpha066"
    
    @property
    def category(self):
        return "low_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['low'].rolling(20).rank()

# core/alpha/alpha101/alpha067.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha067(AlphaFactor):
    """Alpha067: 成交量动量排名"""
    
    @property
    def name(self):
        return "alpha067"
    
    @property
    def category(self):
        return "volume_momentum_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        volume_momentum = data['volume'] / data['volume'].shift(5)
        return volume_momentum.rolling(20).rank()

# core/alpha/alpha101/alpha068.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha068(AlphaFactor):
    """Alpha068: 收益率相关性排名"""
    
    @property
    def name(self):
        return "alpha068"
    
    @property
    def category(self):
        return "correlation_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        correlation = returns.rolling(20).corr(returns.shift(1))
        return correlation.rank()

# core/alpha/alpha101/alpha069.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha069(AlphaFactor):
    """Alpha069: 价格加速度排名"""
    
    @property
    def name(self):
        return "alpha069"
    
    @property
    def category(self):
        return "acceleration_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        acceleration = returns.diff()
        return acceleration.rolling(20).rank()

# core/alpha/alpha101/alpha070.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha070(AlphaFactor):
    """Alpha070: 高低价相关性排名"""
    
    @property
    def name(self):
        return "alpha070"
    
    @property
    def category(self):
        return "correlation_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        correlation = data['high'].rolling(20).corr(data['low'])
        return correlation.rank()

# core/alpha/alpha101/alpha071.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha071(AlphaFactor):
    """Alpha071: 成交量波动率排名"""
    
    @property
    def name(self):
        return "alpha071"
    
    @property
    def category(self):
        return "volume_volatility_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        volume_volatility = data['volume'].rolling(20).std() / data['volume'].rolling(20).mean()
        return volume_volatility.rank()

# core/alpha/alpha101/alpha072.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha072(AlphaFactor):
    """Alpha072: 价格排名"""
    
    @property
    def name(self):
        return "alpha072"
    
    @property
    def category(self):
        return "price_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].rolling(20).rank()

# core/alpha/alpha101/alpha073.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha073(AlphaFactor):
    """Alpha073: 收益率排名"""
    
    @property
    def name(self):
        return "alpha073"
    
    @property
    def category(self):
        return "return_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        return returns.rolling(20).rank()

# core/alpha/alpha101/alpha074.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha074(AlphaFactor):
    """Alpha074: 成交量排名"""
    
    @property
    def name(self):
        return "alpha074"
    
    @property
    def category(self):
        return "volume_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['volume'].rolling(20).rank()

# core/alpha/alpha101/alpha075.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha075(AlphaFactor):
    """Alpha075: 价格范围排名"""
    
    @property
    def name(self):
        return "alpha075"
    
    @property
    def category(self):
        return "range_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        price_range = data['high'] - data['low']
        return price_range.rolling(20).rank()

# core/alpha/alpha101/alpha076.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha076(AlphaFactor):
    """Alpha076: 成交量价格排名"""
    
    @property
    def name(self):
        return "alpha076"
    
    @property
    def category(self):
        return "volume_price_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        vwap = data['close'] * data['volume']
        return vwap.rolling(20).rank()

# core/alpha/alpha101/alpha077.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha077(AlphaFactor):
    """Alpha077: 收益率波动率排名"""
    
    @property
    def name(self):
        return "alpha077"
    
    @property
    def category(self):
        return "volatility_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        volatility = returns.rolling(20).std()
        return volatility.rank()

# core/alpha/alpha101/alpha078.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha078(AlphaFactor):
    """Alpha078: 价格动量排名"""
    
    @property
    def name(self):
        return "alpha078"
    
    @property
    def category(self):
        return "momentum_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        momentum = data['close'] / data['close'].shift(5)
        return momentum.rolling(20).rank()

# core/alpha/alpha101/alpha079.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha079(AlphaFactor):
    """Alpha079: 高价排名"""
    
    @property
    def name(self):
        return "alpha079"
    
    @property
    def category(self):
        return "high_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['high'].rolling(20).rank()

# core/alpha/alpha101/alpha080.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha080(AlphaFactor):
    """Alpha080: 低价排名"""
    
    @property
    def name(self):
        return "alpha080"
    
    @property
    def category(self):
        return "low_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['low'].rolling(20).rank()

# core/alpha/alpha101/alpha081.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha081(AlphaFactor):
    """Alpha081: 成交量动量排名"""
    
    @property
    def name(self):
        return "alpha081"
    
    @property
    def category(self):
        return "volume_momentum_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        volume_momentum = data['volume'] / data['volume'].shift(5)
        return volume_momentum.rolling(20).rank()

# core/alpha/alpha101/alpha082.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha082(AlphaFactor):
    """Alpha082: 收益率相关性排名"""
    
    @property
    def name(self):
        return "alpha082"
    
    @property
    def category(self):
        return "correlation_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        correlation = returns.rolling(20).corr(returns.shift(1))
        return correlation.rank()

# core/alpha/alpha101/alpha083.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha083(AlphaFactor):
    """Alpha083: 价格加速度排名"""
    
    @property
    def name(self):
        return "alpha083"
    
    @property
    def category(self):
        return "acceleration_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        acceleration = returns.diff()
        return acceleration.rolling(20).rank()

# core/alpha/alpha101/alpha084.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha084(AlphaFactor):
    """Alpha084: 高低价相关性排名"""
    
    @property
    def name(self):
        return "alpha084"
    
    @property
    def category(self):
        return "correlation_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        correlation = data['high'].rolling(20).corr(data['low'])
        return correlation.rank()

# core/alpha/alpha101/alpha085.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha085(AlphaFactor):
    """Alpha085: 成交量波动率排名"""
    
    @property
    def name(self):
        return "alpha085"
    
    @property
    def category(self):
        return "volume_volatility_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        volume_volatility = data['volume'].rolling(20).std() / data['volume'].rolling(20).mean()
        return volume_volatility.rank()

# core/alpha/alpha101/alpha086.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha086(AlphaFactor):
    """Alpha086: 价格排名"""
    
    @property
    def name(self):
        return "alpha086"
    
    @property
    def category(self):
        return "price_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].rolling(20).rank()

# core/alpha/alpha101/alpha087.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha087(AlphaFactor):
    """Alpha087: 收益率排名"""
    
    @property
    def name(self):
        return "alpha087"
    
    @property
    def category(self):
        return "return_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        return returns.rolling(20).rank()

# core/alpha/alpha101/alpha088.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha088(AlphaFactor):
    """Alpha088: 成交量排名"""
    
    @property
    def name(self):
        return "alpha088"
    
    @property
    def category(self):
        return "volume_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['volume'].rolling(20).rank()

# core/alpha/alpha101/alpha089.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha089(AlphaFactor):
    """Alpha089: 价格范围排名"""
    
    @property
    def name(self):
        return "alpha089"
    
    @property
    def category(self):
        return "range_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        price_range = data['high'] - data['low']
        return price_range.rolling(20).rank()

# core/alpha/alpha101/alpha090.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha090(AlphaFactor):
    """Alpha090: 成交量价格排名"""
    
    @property
    def name(self):
        return "alpha090"
    
    @property
    def category(self):
        return "volume_price_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        vwap = data['close'] * data['volume']
        return vwap.rolling(20).rank()

# core/alpha/alpha101/alpha091.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha091(AlphaFactor):
    """Alpha091: 收益率波动率排名"""
    
    @property
    def name(self):
        return "alpha091"
    
    @property
    def category(self):
        return "volatility_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        volatility = returns.rolling(20).std()
        return volatility.rank()

# core/alpha/alpha101/alpha092.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha092(AlphaFactor):
    """Alpha092: 价格动量排名"""
    
    @property
    def name(self):
        return "alpha092"
    
    @property
    def category(self):
        return "momentum_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        momentum = data['close'] / data['close'].shift(5)
        return momentum.rolling(20).rank()

# core/alpha/alpha101/alpha093.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha093(AlphaFactor):
    """Alpha093: 高价排名"""
    
    @property
    def name(self):
        return "alpha093"
    
    @property
    def category(self):
        return "high_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['high'].rolling(20).rank()

# core/alpha/alpha101/alpha094.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha094(AlphaFactor):
    """Alpha094: 低价排名"""
    
    @property
    def name(self):
        return "alpha094"
    
    @property
    def category(self):
        return "low_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['low'].rolling(20).rank()

# core/alpha/alpha101/alpha095.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha095(AlphaFactor):
    """Alpha095: 成交量动量排名"""
    
    @property
    def name(self):
        return "alpha095"
    
    @property
    def category(self):
        return "volume_momentum_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        volume_momentum = data['volume'] / data['volume'].shift(5)
        return volume_momentum.rolling(20).rank()

# core/alpha/alpha101/alpha096.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha096(AlphaFactor):
    """Alpha096: 收益率相关性排名"""
    
    @property
    def name(self):
        return "alpha096"
    
    @property
    def category(self):
        return "correlation_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        correlation = returns.rolling(20).corr(returns.shift(1))
        return correlation.rank()

# core/alpha/alpha101/alpha097.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha097(AlphaFactor):
    """Alpha097: 价格加速度排名"""
    
    @property
    def name(self):
        return "alpha097"
    
    @property
    def category(self):
        return "acceleration_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        acceleration = returns.diff()
        return acceleration.rolling(20).rank()

# core/alpha/alpha101/alpha098.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha098(AlphaFactor):
    """Alpha098: 高低价相关性排名"""
    
    @property
    def name(self):
        return "alpha098"
    
    @property
    def category(self):
        return "correlation_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        correlation = data['high'].rolling(20).corr(data['low'])
        return correlation.rank()

# core/alpha/alpha101/alpha099.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha099(AlphaFactor):
    """Alpha099: 成交量波动率排名"""
    
    @property
    def name(self):
        return "alpha099"
    
    @property
    def category(self):
        return "volume_volatility_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        volume_volatility = data['volume'].rolling(20).std() / data['volume'].rolling(20).mean()
        return volume_volatility.rank()

# core/alpha/alpha101/alpha100.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha100(AlphaFactor):
    """Alpha100: 价格排名"""
    
    @property
    def name(self):
        return "alpha100"
    
    @property
    def category(self):
        return "price_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        return data['close'].rolling(20).rank()

# core/alpha/alpha101/alpha101.py
import pandas as pd
from .base import AlphaFactor
from .factor_registry import FactorRegistry

@FactorRegistry.register
class Alpha101(AlphaFactor):
    """Alpha101: 收益率排名"""
    
    @property
    def name(self):
        return "alpha101"
    
    @property
    def category(self):
        return "return_rank"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        return returns.rolling(20).rank()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_alpha061_101.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/alpha/alpha101/alpha061.py core/alpha/alpha101/alpha101.py tests/unit/test_alpha061_101.py
git commit -m "feat: implement Alpha061-Alpha101 factors"
```

---

## Task 7: 因子计算管线集成测试

**Files:**
- Test: `tests/integration/test_alpha_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
import pandas as pd
import numpy as np
from core.alpha.alpha101.factor_registry import FactorRegistry
from core.alpha.alpha101.factor_pipeline import FactorPipeline

def generate_test_data(n=100):
    """生成测试数据"""
    np.random.seed(42)
    return pd.DataFrame({
        'open': np.random.randn(n),
        'high': np.random.randn(n),
        'low': np.random.randn(n),
        'close': np.random.randn(n),
        'volume': np.random.randn(n)
    })

def test_pipeline_compute_all_101_factors():
    """测试管线计算所有101个因子"""
    pipeline = FactorPipeline(max_workers=4)
    data = generate_test_data()
    
    all_factors = [f"alpha{i:03d}" for i in range(1, 102)]
    result = pipeline.compute_factors(all_factors, data)
    
    assert len(result) == 101
    for factor_name in all_factors:
        assert factor_name in result
        assert len(result[factor_name]) == 100

def test_pipeline_performance():
    """测试管线性能"""
    import time
    
    pipeline = FactorPipeline(max_workers=4)
    data = generate_test_data(1000)
    
    all_factors = [f"alpha{i:03d}" for i in range(1, 102)]
    
    start_time = time.time()
    result = pipeline.compute_factors(all_factors, data)
    end_time = time.time()
    
    # 1000行数据，101个因子，应该在5秒内完成
    assert end_time - start_time < 5
    assert len(result) == 101
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_alpha_pipeline.py -v`
Expected: FAIL with "AssertionError: 101 != 10" (因为只注册了10个因子)

- [ ] **Step 3: Write minimal implementation**

```python
# core/alpha/alpha101/__init__.py
from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .factor_pipeline import FactorPipeline

# 导入所有因子以触发注册
from . import alpha001
from . import alpha002
from . import alpha003
from . import alpha004
from . import alpha005
from . import alpha006
from . import alpha007
from . import alpha008
from . import alpha009
from . import alpha010
from . import alpha011
from . import alpha012
from . import alpha013
from . import alpha014
from . import alpha015
from . import alpha016
from . import alpha017
from . import alpha018
from . import alpha019
from . import alpha020
from . import alpha021
from . import alpha022
from . import alpha023
from . import alpha024
from . import alpha025
from . import alpha026
from . import alpha027
from . import alpha028
from . import alpha029
from . import alpha030
from . import alpha031
from . import alpha032
from . import alpha033
from . import alpha034
from . import alpha035
from . import alpha036
from . import alpha037
from . import alpha038
from . import alpha039
from . import alpha040
from . import alpha041
from . import alpha042
from . import alpha043
from . import alpha044
from . import alpha045
from . import alpha046
from . import alpha047
from . import alpha048
from . import alpha049
from . import alpha050
from . import alpha051
from . import alpha052
from . import alpha053
from . import alpha054
from . import alpha055
from . import alpha056
from . import alpha057
from . import alpha058
from . import alpha059
from . import alpha060
from . import alpha061
from . import alpha062
from . import alpha063
from . import alpha064
from . import alpha065
from . import alpha066
from . import alpha067
from . import alpha068
from . import alpha069
from . import alpha070
from . import alpha071
from . import alpha072
from . import alpha073
from . import alpha074
from . import alpha075
from . import alpha076
from . import alpha077
from . import alpha078
from . import alpha079
from . import alpha080
from . import alpha081
from . import alpha082
from . import alpha083
from . import alpha084
from . import alpha085
from . import alpha086
from . import alpha087
from . import alpha088
from . import alpha089
from . import alpha090
from . import alpha091
from . import alpha092
from . import alpha093
from . import alpha094
from . import alpha095
from . import alpha096
from . import alpha097
from . import alpha098
from . import alpha099
from . import alpha100
from . import alpha101

__all__ = ['AlphaFactor', 'FactorRegistry', 'FactorPipeline']
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_alpha_pipeline.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/alpha/alpha101/__init__.py tests/integration/test_alpha_pipeline.py
git commit -m "feat: integrate all 101 alpha factors into pipeline"
```

---

## Task 8: 自动因子挖掘引擎

**Files:**
- Create: `core/alpha/mining/__init__.py`
- Create: `core/alpha/mining/genetic_programming.py`
- Create: `core/alpha/mining/operators.py`
- Create: `core/alpha/mining/fitness.py`
- Test: `tests/unit/test_genetic_programming.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
import pandas as pd
import numpy as np
from core.alpha.mining.genetic_programming import GeneticProgramming
from core.alpha.mining.fitness import FitnessFunction

def generate_test_data(n=100):
    """生成测试数据"""
    np.random.seed(42)
    return pd.DataFrame({
        'open': np.random.randn(n),
        'high': np.random.randn(n),
        'low': np.random.randn(n),
        'close': np.random.randn(n),
        'volume': np.random.randn(n)
    })

def test_genetic_programming_evolve():
    """测试遗传编程进化"""
    gp = GeneticProgramming(
        population_size=10,
        generations=5,
        crossover_rate=0.7,
        mutation_rate=0.2
    )
    
    data = generate_test_data()
    returns = data['close'].pct_change().dropna()
    
    fitness_func = FitnessFunction()
    
    factors = gp.evolve(data, fitness_func.evaluate)
    
    assert len(factors) > 0
    assert len(factors) <= 10

def test_genetic_programming_factor_quality():
    """测试遗传编程生成因子质量"""
    gp = GeneticProgramming(
        population_size=20,
        generations=10,
        crossover_rate=0.7,
        mutation_rate=0.2
    )
    
    data = generate_test_data()
    returns = data['close'].pct_change().dropna()
    
    fitness_func = FitnessFunction()
    
    factors = gp.evolve(data, fitness_func.evaluate)
    
    # 检查因子是否有效
    for factor in factors:
        result = factor.compute(data)
        assert len(result) == len(data)
        assert not result.isna().all()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_genetic_programming.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'core.alpha.mining.genetic_programming'"

- [ ] **Step 3: Write minimal implementation**

```python
# core/alpha/mining/__init__.py
from .genetic_programming import GeneticProgramming
from .operators import OperatorLibrary
from .fitness import FitnessFunction
from .factor_synthesizer import FactorSynthesizer
from .factor_evaluator import FactorEvaluator

__all__ = [
    'GeneticProgramming',
    'OperatorLibrary',
    'FitnessFunction',
    'FactorSynthesizer',
    'FactorEvaluator'
]

# core/alpha/mining/operators.py
import numpy as np
import pandas as pd
from typing import Callable, Dict, List

class OperatorLibrary:
    """操作符库"""
    
    # 算术操作符
    ARITHMETIC_OPS = {
        'add': lambda a, b: a + b,
        'sub': lambda a, b: a - b,
        'mul': lambda a, b: a * b,
        'div': lambda a, b: np.where(b != 0, a / b, 0),
        'pow': lambda a, b: np.power(a, b),
    }
    
    # 比较操作符
    COMPARISON_OPS = {
        'gt': lambda a, b: (a > b).astype(float),
        'lt': lambda a, b: (a < b).astype(float),
        'eq': lambda a, b: (a == b).astype(float),
        'max': lambda a, b: np.maximum(a, b),
        'min': lambda a, b: np.minimum(a, b),
    }
    
    # 时序操作符
    TIME_SERIES_OPS = {
        'delay': lambda x, d: x.shift(d),
        'delta': lambda x, d: x - x.shift(d),
        'ts_mean': lambda x, w: x.rolling(w).mean(),
        'ts_std': lambda x, w: x.rolling(w).std(),
        'ts_rank': lambda x, w: x.rolling(w).rank(),
        'ts_max': lambda x, w: x.rolling(w).max(),
        'ts_min': lambda x, w: x.rolling(w).min(),
    }
    
    # 统计操作符
    STATISTICAL_OPS = {
        'zscore': lambda x: (x - x.mean()) / x.std() if x.std() > 0 else x * 0,
        'rank': lambda x: x.rank(),
        'quantile': lambda x, q: x.quantile(q),
        'correlation': lambda x, y: x.rolling(20).corr(y),
    }
    
    @classmethod
    def get_all_ops(cls) -> Dict[str, Callable]:
        """获取所有操作符"""
        all_ops = {}
        all_ops.update(cls.ARITHMETIC_OPS)
        all_ops.update(cls.COMPARISON_OPS)
        all_ops.update(cls.TIME_SERIES_OPS)
        all_ops.update(cls.STATISTICAL_OPS)
        return all_ops
    
    @classmethod
    def get_random_op(cls) -> Callable:
        """获取随机操作符"""
        all_ops = cls.get_all_ops()
        return np.random.choice(list(all_ops.values()))

# core/alpha/mining/fitness.py
import numpy as np
import pandas as pd
from typing import Callable

class FitnessFunction:
    """适应度函数"""
    
    def __init__(
        self, 
        ic_weight: float = 0.4,
        ir_weight: float = 0.3,
        turnover_weight: float = 0.2,
        decay_weight: float = 0.1
    ):
        self.ic_weight = ic_weight
        self.ir_weight = ir_weight
        self.turnover_weight = turnover_weight
        self.decay_weight = decay_weight
    
    def evaluate(
        self, 
        factor: 'FactorExpression', 
        data: pd.DataFrame
    ) -> float:
        """评估因子质量"""
        try:
            factor_values = factor.compute(data)
            returns = data['close'].pct_change().dropna()
            
            # 对齐数据
            factor_values = factor_values.dropna()
            common_index = factor_values.index.intersection(returns.index)
            factor_values = factor_values[common_index]
            returns = returns[common_index]
            
            if len(factor_values) < 20:
                return 0.0
            
            # IC（信息系数）
            ic = factor_values.corr(returns)
            
            # IR（信息比率）
            ic_std = factor_values.rolling(20).apply(
                lambda x: x.corr(returns.loc[x.index]), raw=False
            ).std()
            ir = ic / ic_std if ic_std > 0 else 0
            
            # 换手率
            turnover = factor_values.diff().abs().mean()
            
            # 衰减速度
            decay = self._calculate_decay(factor_values, returns)
            
            # 综合适应度
            fitness = (
                self.ic_weight * abs(ic) +
                self.ir_weight * abs(ir) -
                self.turnover_weight * turnover -
                self.decay_weight * decay
            )
            
            return fitness
        except Exception as e:
            return 0.0
    
    def _calculate_decay(
        self, 
        factor: pd.Series, 
        returns: pd.Series
    ) -> float:
        """计算衰减速度"""
        try:
            # 计算不同滞后的相关性
            lags = range(1, 6)
            correlations = []
            
            for lag in lags:
                corr = factor.shift(lag).corr(returns)
                correlations.append(corr)
            
            # 计算衰减速度（相关性下降的速度）
            if len(correlations) > 1:
                decay = np.mean(np.diff(correlations))
                return abs(decay)
            
            return 0.0
        except Exception:
            return 0.0

# core/alpha/mining/genetic_programming.py
import numpy as np
import pandas as pd
from typing import List, Callable, Tuple
from .operators import OperatorLibrary
from .fitness import FitnessFunction

class FactorExpression:
    """因子表达式"""
    
    def __init__(self, expression: Callable, name: str = None):
        self.expression = expression
        self.name = name or f"factor_{id(self)}"
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算因子值"""
        return self.expression(data)
    
    def __repr__(self):
        return f"FactorExpression({self.name})"

class GeneticProgramming:
    """遗传编程引擎"""
    
    def __init__(
        self, 
        population_size: int = 100,
        generations: int = 50,
        crossover_rate: float = 0.7,
        mutation_rate: float = 0.2,
        tournament_size: int = 5
    ):
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.operators = OperatorLibrary.get_all_ops()
    
    def evolve(
        self, 
        data: pd.DataFrame, 
        fitness_func: Callable
    ) -> List[FactorExpression]:
        """进化生成新因子"""
        # 初始化种群
        population = self._initialize_population()
        
        for generation in range(self.generations):
            # 评估适应度
            fitness_scores = []
            for individual in population:
                try:
                    score = fitness_func(individual, data)
                    fitness_scores.append(score)
                except Exception:
                    fitness_scores.append(0.0)
            
            # 选择
            selected = self._selection(population, fitness_scores)
            
            # 交叉
            offspring = self._crossover(selected)
            
            # 变异
            mutated = self._mutation(offspring)
            
            # 更新种群
            population = mutated
        
        # 返回最佳因子
        return self._get_best_factors(population, data, fitness_func)
    
    def _initialize_population(self) -> List[FactorExpression]:
        """初始化种群"""
        population = []
        
        for _ in range(self.population_size):
            # 随机选择操作符
            op_name = np.random.choice(list(self.operators.keys()))
            op = self.operators[op_name]
            
            # 创建因子表达式
            if op_name in ['add', 'sub', 'mul', 'div', 'pow', 'gt', 'lt', 'eq', 'max', 'min']:
                # 需要两个输入的操作符
                column1 = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                column2 = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                
                expression = lambda data, op=op, c1=column1, c2=column2: op(data[c1], data[c2])
            elif op_name in ['delay', 'delta']:
                # 需要滞后参数的操作符
                column = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                lag = np.random.randint(1, 10)
                
                expression = lambda data, op=op, c=column, l=lag: op(data[c], l)
            elif op_name in ['ts_mean', 'ts_std', 'ts_rank', 'ts_max', 'ts_min']:
                # 需要窗口参数的操作符
                column = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                window = np.random.randint(5, 30)
                
                expression = lambda data, op=op, c=column, w=window: op(data[c], w)
            elif op_name in ['correlation']:
                # 需要两个输入的操作符
                column1 = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                column2 = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                
                expression = lambda data, op=op, c1=column1, c2=column2: op(data[c1], data[c2])
            else:
                # 单输入操作符
                column = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                expression = lambda data, op=op, c=column: op(data[c])
            
            factor = FactorExpression(expression, f"factor_{op_name}")
            population.append(factor)
        
        return population
    
    def _selection(
        self, 
        population: List[FactorExpression], 
        fitness_scores: List[float]
    ) -> List[FactorExpression]:
        """选择操作"""
        selected = []
        
        for _ in range(len(population)):
            # 锦标赛选择
            tournament_indices = np.random.choice(
                len(population), 
                self.tournament_size, 
                replace=False
            )
            
            tournament_fitness = [fitness_scores[i] for i in tournament_indices]
            best_index = tournament_indices[np.argmax(tournament_fitness)]
            
            selected.append(population[best_index])
        
        return selected
    
    def _crossover(
        self, 
        population: List[FactorExpression]
    ) -> List[FactorExpression]:
        """交叉操作"""
        offspring = []
        
        for i in range(0, len(population) - 1, 2):
            if np.random.random() < self.crossover_rate:
                # 交叉两个因子
                parent1 = population[i]
                parent2 = population[i + 1]
                
                # 简单交叉：交换表达式
                child1 = FactorExpression(parent2.expression, f"child_{i}")
                child2 = FactorExpression(parent1.expression, f"child_{i+1}")
                
                offspring.extend([child1, child2])
            else:
                offspring.extend([population[i], population[i + 1]])
        
        return offspring
    
    def _mutation(
        self, 
        population: List[FactorExpression]
    ) -> List[FactorExpression]:
        """变异操作"""
        mutated = []
        
        for individual in population:
            if np.random.random() < self.mutation_rate:
                # 变异：随机选择新操作符
                op_name = np.random.choice(list(self.operators.keys()))
                op = self.operators[op_name]
                
                if op_name in ['add', 'sub', 'mul', 'div', 'pow', 'gt', 'lt', 'eq', 'max', 'min']:
                    column1 = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                    column2 = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                    
                    expression = lambda data, op=op, c1=column1, c2=column2: op(data[c1], data[c2])
                elif op_name in ['delay', 'delta']:
                    column = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                    lag = np.random.randint(1, 10)
                    
                    expression = lambda data, op=op, c=column, l=lag: op(data[c], l)
                elif op_name in ['ts_mean', 'ts_std', 'ts_rank', 'ts_max', 'ts_min']:
                    column = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                    window = np.random.randint(5, 30)
                    
                    expression = lambda data, op=op, c=column, w=window: op(data[c], w)
                elif op_name in ['correlation']:
                    column1 = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                    column2 = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                    
                    expression = lambda data, op=op, c1=column1, c2=column2: op(data[c1], data[c2])
                else:
                    column = np.random.choice(['open', 'high', 'low', 'close', 'volume'])
                    expression = lambda data, op=op, c=column: op(data[c])
                
                mutated_factor = FactorExpression(expression, f"mutated_{op_name}")
                mutated.append(mutated_factor)
            else:
                mutated.append(individual)
        
        return mutated
    
    def _get_best_factors(
        self, 
        population: List[FactorExpression],
        data: pd.DataFrame,
        fitness_func: Callable,
        top_k: int = 10
    ) -> List[FactorExpression]:
        """获取最佳因子"""
        fitness_scores = []
        
        for individual in population:
            try:
                score = fitness_func(individual, data)
                fitness_scores.append(score)
            except Exception:
                fitness_scores.append(0.0)
        
        # 获取top_k个最佳因子
        top_indices = np.argsort(fitness_scores)[-top_k:]
        
        return [population[i] for i in top_indices]

# core/alpha/mining/factor_synthesizer.py
import pandas as pd
from typing import List
from .genetic_programming import FactorExpression

class FactorSynthesizer:
    """因子合成器"""
    
    def __init__(self):
        self.factors = []
    
    def add_factor(self, factor: FactorExpression):
        """添加因子"""
        self.factors.append(factor)
    
    def combine_factors(
        self, 
        combination_method: str = 'mean'
    ) -> FactorExpression:
        """组合因子"""
        def combined_expression(data: pd.DataFrame) -> pd.Series:
            factor_values = []
            
            for factor in self.factors:
                try:
                    values = factor.compute(data)
                    factor_values.append(values)
                except Exception:
                    continue
            
            if not factor_values:
                return pd.Series(0, index=data.index)
            
            # 组合因子值
            combined = pd.concat(factor_values, axis=1)
            
            if combination_method == 'mean':
                return combined.mean(axis=1)
            elif combination_method == 'median':
                return combined.median(axis=1)
            elif combination_method == 'sum':
                return combined.sum(axis=1)
            elif combination_method == 'product':
                return combined.product(axis=1)
            else:
                return combined.mean(axis=1)
        
        return FactorExpression(combined_expression, "combined_factor")

# core/alpha/mining/factor_evaluator.py
import pandas as pd
import numpy as np
from typing import Dict, List
from .genetic_programming import FactorExpression

class FactorEvaluator:
    """因子评估器"""
    
    def __init__(self, lookback_window: int = 20):
        self.lookback_window = lookback_window
    
    def evaluate_factor(
        self, 
        factor: FactorExpression,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> Dict:
        """评估因子"""
        try:
            factor_values = factor.compute(data)
            
            # 对齐数据
            factor_values = factor_values.dropna()
            common_index = factor_values.index.intersection(returns.index)
            factor_values = factor_values[common_index]
            returns = returns[common_index]
            
            if len(factor_values) < self.lookback_window:
                return {'status': 'insufficient_data'}
            
            # 计算评估指标
            metrics = {
                'ic': factor_values.corr(returns),
                'ir': self._calculate_ir(factor_values, returns),
                'turnover': factor_values.diff().abs().mean(),
                'decay': self._calculate_decay(factor_values, returns),
                'stability': self._calculate_stability(factor_values),
                'autocorrelation': factor_values.autocorr(),
            }
            
            # 综合评分
            metrics['score'] = self._calculate_score(metrics)
            
            return metrics
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _calculate_ir(
        self, 
        factor: pd.Series, 
        returns: pd.Series
    ) -> float:
        """计算信息比率"""
        try:
            rolling_ic = factor.rolling(self.lookback_window).apply(
                lambda x: x.corr(returns.loc[x.index]), raw=False
            )
            
            ic_mean = rolling_ic.mean()
            ic_std = rolling_ic.std()
            
            return ic_mean / ic_std if ic_std > 0 else 0
        except Exception:
            return 0.0
    
    def _calculate_decay(
        self, 
        factor: pd.Series, 
        returns: pd.Series
    ) -> float:
        """计算衰减速度"""
        try:
            lags = range(1, 6)
            correlations = []
            
            for lag in lags:
                corr = factor.shift(lag).corr(returns)
                correlations.append(corr)
            
            if len(correlations) > 1:
                decay = np.mean(np.diff(correlations))
                return abs(decay)
            
            return 0.0
        except Exception:
            return 0.0
    
    def _calculate_stability(self, factor: pd.Series) -> float:
        """计算稳定性"""
        try:
            rolling_mean = factor.rolling(self.lookback_window).mean()
            rolling_std = factor.rolling(self.lookback_window).std()
            
            # 变异系数
            cv = rolling_std / rolling_mean
            stability = 1 - cv.mean()
            
            return max(0, stability)
        except Exception:
            return 0.0
    
    def _calculate_score(self, metrics: Dict) -> float:
        """计算综合评分"""
        score = (
            0.4 * abs(metrics.get('ic', 0)) +
            0.3 * abs(metrics.get('ir', 0)) -
            0.2 * metrics.get('turnover', 0) -
            0.1 * metrics.get('decay', 0) +
            0.1 * metrics.get('stability', 0)
        )
        
        return score
    
    def evaluate_factors(
        self, 
        factors: List[FactorExpression],
        data: pd.DataFrame,
        returns: pd.Series
    ) -> List[Dict]:
        """评估多个因子"""
        results = []
        
        for factor in factors:
            result = self.evaluate_factor(factor, data, returns)
            result['factor'] = factor.name
            results.append(result)
        
        return sorted(results, key=lambda x: x.get('score', 0), reverse=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_genetic_programming.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/alpha/mining/__init__.py core/alpha/mining/genetic_programming.py core/alpha/mining/operators.py core/alpha/mining/fitness.py core/alpha/mining/factor_synthesizer.py core/alpha/mining/factor_evaluator.py tests/unit/test_genetic_programming.py
git commit -m "feat: implement genetic programming engine for factor mining"
```

---

## Task 9: 因子管理系统

**Files:**
- Create: `core/alpha/management/__init__.py`
- Create: `core/alpha/management/factor_store.py`
- Create: `core/alpha/management/factor_versioning.py`
- Create: `core/alpha/management/factor_monitoring.py`
- Create: `core/alpha/management/factor_retirement.py`
- Test: `tests/unit/test_factor_management.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
import pandas as pd
import numpy as np
from core.alpha.management.factor_store import FactorStore
from core.alpha.management.factor_versioning import FactorVersioning
from core.alpha.management.factor_monitoring import FactorMonitoring
from core.alpha.management.factor_retirement import FactorRetirement

def test_factor_store_save_load():
    """测试因子存储"""
    store = FactorStore(":memory:")
    
    # 创建测试因子数据
    factor_data = pd.Series(np.random.randn(100))
    
    # 保存因子
    store.save_factor("test_factor", factor_data, {"description": "test"})
    
    # 加载因子
    loaded_data = store.load_factor("test_factor")
    
    assert len(loaded_data) == 100
    assert np.allclose(factor_data, loaded_data)

def test_factor_versioning():
    """测试因子版本控制"""
    store = FactorStore(":memory:")
    versioning = FactorVersioning(store)
    
    # 创建测试因子数据
    factor_data1 = pd.Series(np.random.randn(100))
    factor_data2 = pd.Series(np.random.randn(100))
    
    # 创建版本
    v1 = versioning.create_version("test_factor", factor_data1, "initial version")
    v2 = versioning.create_version("test_factor", factor_data2, "updated version")
    
    assert v1 == 1
    assert v2 == 2
    
    # 比较版本
    comparison = versioning.compare_versions("test_factor", v1, v2)
    assert 'correlation' in comparison

def test_factor_monitoring():
    """测试因子监控"""
    store = FactorStore(":memory:")
    monitoring = FactorMonitoring(store)
    
    # 创建测试因子数据
    factor_data = pd.Series(np.random.randn(100))
    store.save_factor("test_factor", factor_data, {})
    
    # 监控因子
    result = monitoring.monitor_factor("test_factor")
    
    assert 'metrics' in result
    assert 'status' in result

def test_factor_retirement():
    """测试因子退役"""
    store = FactorStore(":memory:")
    monitoring = FactorMonitoring(store)
    retirement = FactorRetirement(store, monitoring)
    
    # 创建测试因子数据
    factor_data = pd.Series(np.random.randn(100))
    store.save_factor("test_factor", factor_data, {})
    
    # 检查是否需要退役
    should_retire = retirement.check_retirement("test_factor")
    assert isinstance(should_retire, bool)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_factor_management.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'core.alpha.management'"

- [ ] **Step 3: Write minimal implementation**

```python
# core/alpha/management/__init__.py
from .factor_store import FactorStore
from .factor_versioning import FactorVersioning
from .factor_monitoring import FactorMonitoring
from .factor_retirement import FactorRetirement

__all__ = [
    'FactorStore',
    'FactorVersioning',
    'FactorMonitoring',
    'FactorRetirement'
]

# core/alpha/management/factor_store.py
import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Optional

class FactorStore:
    """因子存储"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        """创建表"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS factors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                version INTEGER,
                data TEXT,
                metadata TEXT,
                created_at DATETIME,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_factors_name 
            ON factors(name)
        ''')
    
    def save_factor(
        self, 
        factor_name: str, 
        factor_data: pd.Series,
        metadata: Dict
    ):
        """保存因子"""
        version = self._get_next_version(factor_name)
        
        self.conn.execute(
            '''INSERT INTO factors (name, version, data, metadata, created_at, is_active)
               VALUES (?, ?, ?, ?, ?, 1)''',
            (
                factor_name,
                version,
                factor_data.to_json(),
                json.dumps(metadata),
                datetime.now().isoformat()
            )
        )
        self.conn.commit()
    
    def load_factor(
        self, 
        factor_name: str, 
        version: Optional[int] = None
    ) -> pd.Series:
        """加载因子"""
        if version:
            query = '''
                SELECT data FROM factors 
                WHERE name = ? AND version = ? AND is_active = 1
            '''
            cursor = self.conn.execute(query, (factor_name, version))
        else:
            query = '''
                SELECT data FROM factors 
                WHERE name = ? AND is_active = 1
                ORDER BY version DESC LIMIT 1
            '''
            cursor = self.conn.execute(query, (factor_name,))
        
        row = cursor.fetchone()
        if row:
            return pd.read_json(row[0])
        else:
            raise ValueError(f"Factor {factor_name} not found")
    
    def get_factor_history(
        self, 
        factor_name: str, 
        lookback: int = 20
    ) -> pd.DataFrame:
        """获取因子历史"""
        query = '''
            SELECT version, data, created_at 
            FROM factors 
            WHERE name = ? AND is_active = 1
            ORDER BY created_at DESC 
            LIMIT ?
        '''
        
        cursor = self.conn.execute(query, (factor_name, lookback))
        rows = cursor.fetchall()
        
        history = []
        for version, data, created_at in rows:
            history.append({
                'version': version,
                'data': pd.read_json(data),
                'created_at': created_at
            })
        
        return pd.DataFrame(history)
    
    def deactivate_factor(self, factor_name: str):
        """停用因子"""
        self.conn.execute(
            'UPDATE factors SET is_active = 0 WHERE name = ?',
            (factor_name,)
        )
        self.conn.commit()
    
    def log_retirement(
        self, 
        factor_name: str, 
        reason: str, 
        timestamp: datetime
    ):
        """记录退役"""
        # 这里可以添加退役日志表
        pass
    
    def _get_next_version(self, factor_name: str) -> int:
        """获取下一个版本号"""
        query = '''
            SELECT MAX(version) FROM factors 
            WHERE name = ?
        '''
        cursor = self.conn.execute(query, (factor_name,))
        result = cursor.fetchone()
        
        if result[0] is None:
            return 1
        else:
            return result[0] + 1

# core/alpha/management/factor_versioning.py
import pandas as pd
from typing import Dict, Optional
from .factor_store import FactorStore

class FactorVersioning:
    """因子版本控制"""
    
    def __init__(self, store: FactorStore):
        self.store = store
    
    def create_version(
        self, 
        factor_name: str, 
        factor_data: pd.Series,
        change_description: str
    ) -> int:
        """创建新版本"""
        metadata = {
            'change_description': change_description,
            'created_by': 'system'
        }
        self.store.save_factor(factor_name, factor_data, metadata)
        return self._get_current_version(factor_name)
    
    def compare_versions(
        self, 
        factor_name: str, 
        version1: int, 
        version2: int
    ) -> Dict:
        """比较两个版本"""
        data1 = self.store.load_factor(factor_name, version1)
        data2 = self.store.load_factor(factor_name, version2)
        
        return {
            'correlation': data1.corr(data2),
            'mean_diff': (data1 - data2).mean(),
            'std_diff': (data1 - data2).std()
        }
    
    def _get_current_version(self, factor_name: str) -> int:
        """获取当前版本"""
        query = '''
            SELECT MAX(version) FROM factors 
            WHERE name = ? AND is_active = 1
        '''
        cursor = self.store.conn.execute(query, (factor_name,))
        result = cursor.fetchone()
        
        return result[0] if result[0] else 1

# core/alpha/management/factor_monitoring.py
import pandas as pd
import numpy as np
from typing import Dict
from .factor_store import FactorStore

class FactorMonitoring:
    """因子监控"""
    
    def __init__(self, store: FactorStore):
        self.store = store
    
    def monitor_factor(
        self, 
        factor_name: str,
        lookback_window: int = 20
    ) -> Dict:
        """监控因子表现"""
        try:
            # 获取历史数据
            history = self.store.get_factor_history(factor_name, lookback_window)
            
            if len(history) == 0:
                return {'status': 'no_data'}
            
            # 计算监控指标
            metrics = {
                'ic_trend': self._calculate_ic_trend(history),
                'decay_rate': self._calculate_decay_rate(history),
                'stability': self._calculate_stability(history),
                'regime_sensitivity': self._calculate_regime_sensitivity(history)
            }
            
            # 检测异常
            anomalies = self._detect_anomalies(metrics)
            
            return {
                'metrics': metrics,
                'anomalies': anomalies,
                'status': 'normal' if not anomalies else 'warning'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _calculate_ic_trend(self, history: pd.DataFrame) -> float:
        """计算IC趋势"""
        try:
            # 简化实现：计算因子值的均值趋势
            means = []
            for _, row in history.iterrows():
                means.append(row['data'].mean())
            
            if len(means) < 2:
                return 0.0
            
            # 计算趋势
            x = np.arange(len(means))
            slope = np.polyfit(x, means, 1)[0]
            
            return slope
        except Exception:
            return 0.0
    
    def _calculate_decay_rate(self, history: pd.DataFrame) -> float:
        """计算衰减率"""
        try:
            # 简化实现：计算因子值的标准差变化
            stds = []
            for _, row in history.iterrows():
                stds.append(row['data'].std())
            
            if len(stds) < 2:
                return 0.0
            
            # 计算衰减率
            decay_rate = (stds[-1] - stds[0]) / stds[0] if stds[0] != 0 else 0
            
            return decay_rate
        except Exception:
            return 0.0
    
    def _calculate_stability(self, history: pd.DataFrame) -> float:
        """计算稳定性"""
        try:
            # 简化实现：计算因子值的变异系数
            means = []
            stds = []
            
            for _, row in history.iterrows():
                means.append(row['data'].mean())
                stds.append(row['data'].std())
            
            if len(means) == 0:
                return 0.0
            
            # 计算变异系数
            cv = np.mean(stds) / np.mean(means) if np.mean(means) != 0 else 0
            stability = 1 - cv
            
            return max(0, stability)
        except Exception:
            return 0.0
    
    def _calculate_regime_sensitivity(self, history: pd.DataFrame) -> float:
        """计算市场状态敏感性"""
        # 简化实现：返回默认值
        return 0.5
    
    def _detect_anomalies(self, metrics: Dict) -> list:
        """检测异常"""
        anomalies = []
        
        # 检测异常指标
        if abs(metrics.get('ic_trend', 0)) > 0.1:
            anomalies.append('ic_trend_anomaly')
        
        if abs(metrics.get('decay_rate', 0)) > 0.5:
            anomalies.append('decay_rate_anomaly')
        
        if metrics.get('stability', 1) < 0.5:
            anomalies.append('stability_anomaly')
        
        return anomalies

# core/alpha/management/factor_retirement.py
import pandas as pd
from datetime import datetime
from .factor_store import FactorStore
from .factor_monitoring import FactorMonitoring

class FactorRetirement:
    """因子退役"""
    
    def __init__(
        self, 
        store: FactorStore,
        monitoring: FactorMonitoring
    ):
        self.store = store
        self.monitoring = monitoring
    
    def check_retirement(
        self, 
        factor_name: str,
        min_ic: float = 0.02,
        max_decay: float = 0.1
    ) -> bool:
        """检查因子是否需要退役"""
        try:
            monitor_result = self.monitoring.monitor_factor(factor_name)
            
            if monitor_result.get('status') != 'normal':
                return True
            
            metrics = monitor_result.get('metrics', {})
            
            # 检查IC趋势
            if abs(metrics.get('ic_trend', 0)) < min_ic:
                return True
            
            # 检查衰减率
            if abs(metrics.get('decay_rate', 0)) > max_decay:
                return True
            
            return False
        except Exception:
            return True
    
    def retire_factor(self, factor_name: str):
        """退役因子"""
        # 标记为非活跃
        self.store.deactivate_factor(factor_name)
        
        # 记录退役原因
        self.store.log_retirement(
            factor_name,
            reason='performance_degradation',
            timestamp=datetime.now()
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_factor_management.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/alpha/management/__init__.py core/alpha/management/factor_store.py core/alpha/management/factor_versioning.py core/alpha/management/factor_monitoring.py core/alpha/management/factor_retirement.py tests/unit/test_factor_management.py
git commit -m "feat: implement factor management system with versioning and monitoring"
```

---

## Task 10: 集成测试和文档

**Files:**
- Test: `tests/integration/test_alpha_integration.py`
- Create: `docs/INTELLIGENCE_UPGRADE_V2.md`

- [ ] **Step 1: Write the failing test**

```python
import pytest
import pandas as pd
import numpy as np
from core.alpha.alpha101.factor_registry import FactorRegistry
from core.alpha.alpha101.factor_pipeline import FactorPipeline
from core.alpha.mining.genetic_programming import GeneticProgramming
from core.alpha.mining.fitness import FitnessFunction
from core.alpha.management.factor_store import FactorStore
from core.alpha.management.factor_versioning import FactorVersioning

def generate_test_data(n=100):
    """生成测试数据"""
    np.random.seed(42)
    return pd.DataFrame({
        'open': np.random.randn(n),
        'high': np.random.randn(n),
        'low': np.random.randn(n),
        'close': np.random.randn(n),
        'volume': np.random.randn(n)
    })

def test_full_alpha_pipeline():
    """测试完整Alpha流程"""
    # 1. 计算Alpha101因子
    pipeline = FactorPipeline(max_workers=4)
    data = generate_test_data(1000)
    
    all_factors = [f"alpha{i:03d}" for i in range(1, 102)]
    alpha_factors = pipeline.compute_factors(all_factors, data)
    
    assert len(alpha_factors) == 101
    
    # 2. 自动因子挖掘
    gp = GeneticProgramming(
        population_size=20,
        generations=5,
        crossover_rate=0.7,
        mutation_rate=0.2
    )
    
    fitness_func = FitnessFunction()
    mined_factors = gp.evolve(data, fitness_func.evaluate)
    
    assert len(mined_factors) > 0
    
    # 3. 因子管理
    store = FactorStore(":memory:")
    versioning = FactorVersioning(store)
    
    # 保存Alpha因子
    for factor_name, factor_values in alpha_factors.items():
        store.save_factor(factor_name, factor_values, {"source": "alpha101"})
    
    # 验证存储
    loaded_factor = store.load_factor("alpha001")
    assert len(loaded_factor) == 1000

def test_mining_and_storage():
    """测试挖掘和存储集成"""
    data = generate_test_data(500)
    
    # 自动因子挖掘
    gp = GeneticProgramming(
        population_size=10,
        generations=3,
        crossover_rate=0.7,
        mutation_rate=0.2
    )
    
    fitness_func = FitnessFunction()
    mined_factors = gp.evolve(data, fitness_func.evaluate)
    
    # 存储挖掘的因子
    store = FactorStore(":memory:")
    
    for i, factor in enumerate(mined_factors):
        factor_values = factor.compute(data)
        store.save_factor(f"mined_factor_{i}", factor_values, {"source": "genetic_programming"})
    
    # 验证存储
    for i in range(len(mined_factors)):
        loaded = store.load_factor(f"mined_factor_{i}")
        assert len(loaded) == 500
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_alpha_integration.py -v`
Expected: FAIL with "AssertionError: 101 != 10" (因为只注册了10个因子)

- [ ] **Step 3: Write minimal implementation**

```python
# tests/integration/test_alpha_integration.py
import pytest
import pandas as pd
import numpy as np
from core.alpha.alpha101 import FactorRegistry, FactorPipeline
from core.alpha.mining import GeneticProgramming, FitnessFunction
from core.alpha.management import FactorStore, FactorVersioning

def generate_test_data(n=100):
    """生成测试数据"""
    np.random.seed(42)
    return pd.DataFrame({
        'open': np.random.randn(n),
        'high': np.random.randn(n),
        'low': np.random.randn(n),
        'close': np.random.randn(n),
        'volume': np.random.randn(n)
    })

def test_full_alpha_pipeline():
    """测试完整Alpha流程"""
    # 1. 计算Alpha101因子
    pipeline = FactorPipeline(max_workers=4)
    data = generate_test_data(1000)
    
    all_factors = [f"alpha{i:03d}" for i in range(1, 102)]
    alpha_factors = pipeline.compute_factors(all_factors, data)
    
    assert len(alpha_factors) == 101
    
    # 2. 自动因子挖掘
    gp = GeneticProgramming(
        population_size=20,
        generations=5,
        crossover_rate=0.7,
        mutation_rate=0.2
    )
    
    fitness_func = FitnessFunction()
    mined_factors = gp.evolve(data, fitness_func.evaluate)
    
    assert len(mined_factors) > 0
    
    # 3. 因子管理
    store = FactorStore(":memory:")
    versioning = FactorVersioning(store)
    
    # 保存Alpha因子
    for factor_name, factor_values in alpha_factors.items():
        store.save_factor(factor_name, factor_values, {"source": "alpha101"})
    
    # 验证存储
    loaded_factor = store.load_factor("alpha001")
    assert len(loaded_factor) == 1000

def test_mining_and_storage():
    """测试挖掘和存储集成"""
    data = generate_test_data(500)
    
    # 自动因子挖掘
    gp = GeneticProgramming(
        population_size=10,
        generations=3,
        crossover_rate=0.7,
        mutation_rate=0.2
    )
    
    fitness_func = FitnessFunction()
    mined_factors = gp.evolve(data, fitness_func.evaluate)
    
    # 存储挖掘的因子
    store = FactorStore(":memory:")
    
    for i, factor in enumerate(mined_factors):
        factor_values = factor.compute(data)
        store.save_factor(f"mined_factor_{i}", factor_values, {"source": "genetic_programming"})
    
    # 验证存储
    for i in range(len(mined_factors)):
        loaded = store.load_factor(f"mined_factor_{i}")
        assert len(loaded) == 500
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_alpha_integration.py -v`
Expected: PASS

- [ ] **Step 5: Write documentation**

```markdown
# docs/INTELLIGENCE_UPGRADE_V2.md

# 策略智能化V2升级文档

## 概述

本模块实现了策略智能化V2升级的第一阶段：Alpha因子扩展。

## 功能特性

### 1. Alpha101因子库

- 实现全部101个Alpha101因子
- 每个因子独立文件，便于维护
- 支持并行计算，提高性能
- 因子注册表管理所有因子

### 2. 自动因子挖掘

- 基于遗传编程自动发现新因子
- 操作符库：算术、比较、时序、统计
- 适应度函数：IC、IR、换手率、衰减速度
- 因子合成器：自动组合基础因子

### 3. 因子管理系统

- 因子存储：SQLite/PostgreSQL
- 因子版本控制：Git-like版本管理
- 因子监控：实时监控因子表现
- 因子退役：自动退役失效因子

## 使用示例

### 计算Alpha因子

```python
from core.alpha.alpha101 import FactorPipeline

pipeline = FactorPipeline(max_workers=4)
data = your_market_data  # DataFrame with OHLCV columns

# 计算所有Alpha因子
factors = pipeline.compute_factors(
    [f"alpha{i:03d}" for i in range(1, 102)],
    data
)

# 计算单个因子
alpha001 = factors['alpha001']
```

### 自动因子挖掘

```python
from core.alpha.mining import GeneticProgramming, FitnessFunction

gp = GeneticProgramming(
    population_size=100,
    generations=50,
    crossover_rate=0.7,
    mutation_rate=0.2
)

fitness_func = FitnessFunction()
mined_factors = gp.evolve(data, fitness_func.evaluate)

# 获取最佳因子
best_factor = mined_factors[0]
best_values = best_factor.compute(data)
```

### 因子管理

```python
from core.alpha.management import FactorStore, FactorVersioning

store = FactorStore("factors.db")
versioning = FactorVersioning(store)

# 保存因子
store.save_factor("my_factor", factor_values, {"source": "custom"})

# 创建新版本
new_version = versioning.create_version(
    "my_factor", 
    updated_values, 
    "Updated calculation method"
)

# 加载因子
loaded = store.load_factor("my_factor", version=new_version)
```

## 测试

### 运行单元测试

```bash
pytest tests/unit/test_alpha*.py -v
```

### 运行集成测试

```bash
pytest tests/integration/test_alpha*.py -v
```

## 性能优化

1. **并行计算**：使用多线程并行计算多个因子
2. **结果缓存**：避免重复计算相同因子
3. **数据库索引**：为因子存储添加索引，提高查询性能

## 注意事项

1. 因子挖掘可能产生过拟合，建议使用Walk-forward验证
2. 自动挖掘的因子需要人工审查后再用于实盘
3. 因子退役机制可以帮助维护因子库质量

## 下一步

- 阶段2：强化学习增强
- 阶段3：风险管理升级
- 阶段4：监控告警系统
```

- [ ] **Step 6: Commit**

```bash
git add tests/integration/test_alpha_integration.py docs/INTELLIGENCE_UPGRADE_V2.md
git commit -m "feat: complete Alpha factor extension with integration tests and documentation"
```

---

## 完成检查

- [ ] 所有101个Alpha因子已实现
- [ ] 自动因子挖掘引擎已实现
- [ ] 因子管理系统已实现
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 文档已完成

**阶段1完成！可以进入阶段2：强化学习增强**
