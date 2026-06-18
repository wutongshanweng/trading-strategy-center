"""资产类别采集器 — 编排 fetch -> normalize -> DuckDB 写入。"""

from .base_collector import BaseCollector
from .futures_collector import FuturesCollector
from .stocks_collector import StocksCollector
from .options_collector import OptionsCollector
from .macro_collector import MacroCollector

__all__ = [
    "BaseCollector", "FuturesCollector", "StocksCollector",
    "OptionsCollector", "MacroCollector",
]
