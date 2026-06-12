from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import pandas as pd


class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    symbol: str
    direction: Direction
    confidence: float
    score: float = 0.0
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: str = ""
    strategy_name: str = ""
    timeframe: str = "1d"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    extra: Dict[str, Any] = field(default_factory=dict)
    source_system: str = ""
    resonance_layer: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseStrategy:
    name: str = ""
    description: str = ""
    timeframes: List[str] = ["1d"]
    params: Dict[str, Any] = {}

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.params[k] = v

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Optional[Signal]:
        raise NotImplementedError

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"
