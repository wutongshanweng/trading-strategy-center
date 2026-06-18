"""DuckDB 统一数据仓库存储层。"""

from .duckdb_store import DuckDBStore, get_store

__all__ = ["DuckDBStore", "get_store"]
