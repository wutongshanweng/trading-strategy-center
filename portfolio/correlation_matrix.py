from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class CorrelationMatrix:
    def __init__(self):
        self._price_data: Dict[str, pd.Series] = {}

    def add_price(self, symbol: str, price: float):
        if symbol not in self._price_data:
            self._price_data[symbol] = []
        self._price_data[symbol].append(price)

    def compute(self, symbols: Optional[List[str]] = None) -> pd.DataFrame:
        data = {}
        target = symbols or list(self._price_data.keys())
        for s in target:
            if s in self._price_data:
                series = pd.Series(self._price_data[s])
                if len(series) > 1:
                    data[s] = series.pct_change().dropna()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        return df.corr() if len(df) > 1 else pd.DataFrame()

    def diversify_score(self, symbols: List[str]) -> float:
        corr = self.compute(symbols)
        if corr.empty or len(corr) < 2:
            return 0.0
        upper = corr.values[np.triu_indices_from(corr.values, k=1)]
        return 1.0 - float(np.mean(upper)) if len(upper) > 0 else 0.0
