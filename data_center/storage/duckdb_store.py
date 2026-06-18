"""
DuckDB 统一数据仓库 — 行情数据存储层。

设计要点 (见 交易系统统一数据库设计.md):
- 单写入连接 (DuckDB 单写多读), 写操作加锁串行化
- 读操作使用独立只读连接
- products/symbols 两层结构, kline 统一多周期表
- PRIMARY KEY 天然去重, 重复拉取不产生重复数据
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd
from loguru import logger

_DB_DIR = Path(__file__).resolve().parent.parent  # data_center/
_DEFAULT_DB = _DB_DIR / "data_center.db"
_SCHEMA = _DB_DIR / "db" / "init_schema.sql"


class DuckDBStore:
    """行情数据仓库 — 单写多读。"""

    def __init__(self, db_path: str | Path = _DEFAULT_DB):
        self._path = str(db_path)
        self._write_lock = threading.Lock()
        self._conn = duckdb.connect(self._path)
        self._init_schema()

    def _init_schema(self) -> None:
        sql = _SCHEMA.read_text(encoding="utf-8")
        with self._write_lock:
            self._conn.execute(sql)
        logger.info(f"DuckDB schema initialized at {self._path}")

    # ---- 连接 --------------------------------------------------------------

    def _read_conn(self) -> duckdb.DuckDBPyConnection:
        """只读游标 (共享底层连接, DuckDB 支持并发读)。"""
        return self._conn.cursor()

    # ---- 通用写 ------------------------------------------------------------

    def execute(self, sql: str, params: Optional[list] = None) -> None:
        with self._write_lock:
            self._conn.execute(sql, params or [])

    def upsert_df(self, table: str, df: pd.DataFrame, key_cols: list[str]) -> int:
        """按主键 upsert 一个 DataFrame。返回写入行数。"""
        if df is None or df.empty:
            return 0
        with self._write_lock:
            self._conn.register("_staging_df", df)
            cols = list(df.columns)
            col_list = ", ".join(cols)
            # DELETE 冲突行再 INSERT (DuckDB 无原生 UPSERT 跨所有版本)
            key_match = " AND ".join(
                f"t.{k} = s.{k}" for k in key_cols
            )
            self._conn.execute(
                f"DELETE FROM {table} t USING _staging_df s WHERE {key_match}"
            )
            self._conn.execute(
                f"INSERT INTO {table} ({col_list}) SELECT {col_list} FROM _staging_df"
            )
            self._conn.unregister("_staging_df")
        return len(df)

    # ---- 查询 --------------------------------------------------------------

    def query(self, sql: str, params: Optional[list] = None) -> pd.DataFrame:
        cur = self._read_conn()
        try:
            return cur.execute(sql, params or []).fetchdf()
        finally:
            cur.close()

    def close(self) -> None:
        with self._write_lock:
            self._conn.close()


# 模块级单例
_store: Optional[DuckDBStore] = None
_store_lock = threading.Lock()


def get_store() -> DuckDBStore:
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = DuckDBStore()
    return _store
