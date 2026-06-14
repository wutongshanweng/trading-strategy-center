"""
快速修复前端数据显示
"""

print("=" * 60)
print("前端数据同步问题诊断")
print("=" * 60)

# 1. 检查策略注册
print("\n1. 策略系统检查...")
try:
    from signals.registry import discover, _STRATEGIES
    discover()  # 自动发现所有策略
    print(f"✓ 已注册策略数量: {len(_STRATEGIES)}")
    print(f"  前10个策略:")
    for name in list(_STRATEGIES.keys())[:10]:
        print(f"    - {name}")
except Exception as e:
    print(f"✗ 策略检查失败: {e}")

# 2. 检查Alpha因子
print("\n2. Alpha因子检查...")
try:
    from core.alpha.alpha101.factor_registry import FactorRegistry
    registry = FactorRegistry()
    factors = registry.list_all()
    print(f"✓ 已注册因子数量: {len(factors)}")
    print(f"  前10个因子:")
    for factor in factors[:10]:
        print(f"    - {factor}")
except Exception as e:
    print(f"✗ 因子检查失败: {e}")

# 3. 检查数据源
print("\n3. 数据源检查...")
try:
    from core.data.market_data_manager import MarketDataManager
    manager = MarketDataManager()
    sources = manager.list_sources()
    print(f"✓ 可用数据源数量: {len(sources)}")
    for name, info in list(sources.items())[:5]:
        print(f"    - {name}: {info.get('status', 'unknown')}")
except Exception as e:
    print(f"✗ 数据源检查失败: {e}")

print("\n" + "=" * 60)
print("建议修复方案:")
print("=" * 60)
print("""
1. 策略API: 修复 /api/v1/strategies 返回空数组
2. 前端Mock: 增加Mock数据数量匹配后端
3. 因子页面: 创建新页面展示101个因子
""")
