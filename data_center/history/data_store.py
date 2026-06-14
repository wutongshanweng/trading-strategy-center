"""
数据存储层 — 持久化已下载的市场数据。

支持存储后端:
- Parquet (默认，高性能列式存储)
- CSV (可读性强)
- SQLite (结构化查询)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.base_fetcher import KlineData, KlineInterval

logger = logging.getLogger(__name__)


class DataStore:
    """
    数据存储层。

    目录结构:
    data/
    └── market/
        ├── futures/
        │   ├── M/
        │   │   ├── main/       # 主力连续
        │   │   │   └── 1d.parquet
        │   │   └── contracts/  # 具体合约
        │   │       └── M2609_1d.parquet
        │   └── RB/
        ├── stock/
        └── options/
    """

    def __init__(self, base_path: str = "data/market"):
        self._base = Path(base_path)
        self._base.mkdir(parents=True, exist_ok=True)

    def _get_path(self, market: str, symbol: str, interval: str,
                  contract: Optional[str] = None) -> Path:
        """生成存储路径"""
        parts = [self._base, market, symbol]
        if contract:
            parts.append("contracts")
            fname = f"{contract}_{interval}"
        else:
            parts.append("main")
            fname = interval
        parts.append(f"{fname}.parquet")
        return Path(*parts)

    def save_kline(self, data: KlineData, market: str = "futures") -> bool:
        """保存 K 线数据"""
        if not data.timestamps:
            logger.warning(f"No data to save for {data.symbol}")
            return False

        df = pd.DataFrame({
            "timestamp": data.timestamps,
            "open": data.open,
            "high": data.high,
            "low": data.low,
            "close": data.close,
            "volume": data.volume,
        })
        df.set_index("timestamp", inplace=True)

        path = self._get_path(market, data.symbol, data.interval, data.contract)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            df.to_parquet(path, compression="zstd")
            logger.info(f"Saved {len(df)} bars to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            return False

    def load_kline(self, symbol: str, interval: str, market: str = "futures",
                   contract: Optional[str] = None) -> Optional[KlineData]:
        """加载 K 线数据"""
        path = self._get_path(market, symbol, interval, contract)
        if not path.exists():
            logger.info(f"No cached data at {path}")
            return None

        try:
            df = pd.read_parquet(path)
            df.reset_index(inplace=True)
            return KlineData(
                symbol=symbol, interval=interval,
                open=df["open"].tolist(), high=df["high"].tolist(),
                low=df["low"].tolist(), close=df["close"].tolist(),
                volume=df["volume"].tolist(),
                timestamps=df["timestamp"].tolist(),
                source="cache", contract=contract,
            )
        except Exception as e:
            logger.warning(f"Failed to load {path}: {e}")
            return None

    def exists(self, symbol: str, interval: str, market: str = "futures",
               contract: Optional[str] = None) -> bool:
        """检查数据是否存在"""
        path = self._get_path(market, symbol, interval, contract)
        return path.exists()

    def list_available(self, market: str = "futures") -> List[Dict[str, Any]]:
        """列出可用数据"""
        results = []
        market_dir = self._base / market
        if not market_dir.exists():
            return results

        for sym_dir in sorted(market_dir.iterdir()):
            if not sym_dir.is_dir():
                continue
            # 主力合约数据
            main_dir = sym_dir / "main"
            if main_dir.exists():
                for f in main_dir.glob("*.parquet"):
                    interval = f.stem
                    results.append({
                        "symbol": sym_dir.name,
                        "interval": interval,
                        "contract": None,
                        "path": str(f),
                        "size_kb": round(f.stat().st_size / 1024, 1),
                    })
            # 具体合约数据
            contracts_dir = sym_dir / "contracts"
            if contracts_dir.exists():
                for f in contracts_dir.glob("*.parquet"):
                    parts = f.stem.split("_")
                    contract = parts[0]
                    interval = "_".join(parts[1:]) if len(parts) > 1 else parts[0]
                    results.append({
                        "symbol": sym_dir.name,
                        "interval": interval,
                        "contract": contract,
                        "path": str(f),
                        "size_kb": round(f.stat().st_size / 1024, 1),
                    })
        return results

    def delete(self, symbol: str, interval: str, market: str = "futures",
               contract: Optional[str] = None) -> bool:
        """删除数据"""
        path = self._get_path(market, symbol, interval, contract)
        if path.exists():
            path.unlink()
            logger.info(f"Deleted {path}")
            return True
        return False

    def get_storage_usage(self) -> Dict[str, Any]:
        """获取存储使用统计"""
        total_size = 0
        file_count = 0
        for f in self._base.rglob("*.parquet"):
            total_size += f.stat().st_size
            file_count += 1
        return {
            "total_files": file_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "base_path": str(self._base),
        }
