from typing import Dict, Any
import numpy as np
import pandas as pd


class QuantModel:
    name: str = ""
    def fit(self, df: pd.DataFrame, **kwargs): raise NotImplementedError
    def predict(self, df: pd.DataFrame) -> np.ndarray: raise NotImplementedError
    def get_params(self) -> Dict[str, Any]: return {}
