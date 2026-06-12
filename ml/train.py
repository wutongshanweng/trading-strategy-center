from typing import List, Dict
import pandas as pd
from datetime import datetime, timedelta
from ml.pipeline import MLPipeline


async def train_all_models(df: pd.DataFrame, symbols: List[str]) -> Dict:
    results = {}
    for symbol in symbols:
        results[symbol] = await train_pipeline_for_symbol(symbol, df)
    return results


async def train_pipeline_for_symbol(symbol: str, df: pd.DataFrame) -> Dict:
    pipe = MLPipeline()
    return await pipe.train(df, symbol)


async def retrain_if_needed(symbol: str, last_train_date, pipeline, df) -> bool:
    if last_train_date is None:
        await pipeline.train(df, symbol)
        return True
    days_since = (datetime.utcnow() - last_train_date).days
    if days_since >= pipeline.config.retrain_frequency:
        await pipeline.train(df, symbol)
        return True
    return False
