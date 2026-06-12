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
