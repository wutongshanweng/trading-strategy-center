from typing import List, Optional, Dict
import pandas as pd
from loguru import logger
from signals.base import Signal, Direction
from signals.engine import StrategyEngine
from resonance.engine import ResonanceEngine, ResonanceOutput
from market_state.regime_detector import MarketRegimeDetector, MarketRegime
from core.data.market_data_manager import MarketDataManager


class SignalAdapter:
    def __init__(self, data: MarketDataManager, strategies: StrategyEngine,
                 resonance: ResonanceEngine, regime: MarketRegimeDetector):
        self.data = data
        self.strategies = strategies
        self.resonance = resonance
        self.regime = regime

    async def process_symbol(self, symbol: str, timeframe: str = "1d") -> Optional[ResonanceOutput]:
        feed = await self.data.get_data_feed(symbol, timeframe)
        if feed.quality_score < 0.5:
            logger.warning(f"Data quality too low for {symbol}: {feed.quality_score}")
            return None
        signals = self.strategies.compute_all(feed.df, symbol)
        if not signals:
            logger.debug(f"No signals for {symbol}")
            return None
        regime_info = self.regime.detect(feed.df)
        output = self.resonance.calculate(symbol, signals, regime_info.regime)
        return output

    async def process_batch(self, symbols: List[str], timeframe: str = "1d") -> Dict[str, ResonanceOutput]:
        results = {}
        for symbol in symbols:
            result = await self.process_symbol(symbol, timeframe)
            if result:
                results[symbol] = result
        return results
