"""期权策略子包。

导入各策略模块以触发 @register 装饰器,使策略进入注册表。
新增策略文件后,在此处补一行 import 即可。
"""
from options.strategies import (  # noqa: F401
    directional,
    term_structure,
    volatility_long,
    volatility_short,
)
from options.strategies.term_arbitrage import TermArbitrageSignals  # noqa: F401
from options.strategies.futures_combo import FuturesOptionsComboSignals  # noqa: F401

__all__ = [
    "directional",
    "volatility_short",
    "volatility_long",
    "term_structure",
    "TermArbitrageSignals",
    "FuturesOptionsComboSignals",
]
