"""
宏观采集器 — 中国宏观经济指标 (akshare 免费源)。

设计文档 §2.8 / Phase 6:
CPI/PPI/PMI/GDP/M2/LPR 等 -> macro_data 表 (按 product_id + date)。
"""

from __future__ import annotations

from typing import Callable, Dict

import pandas as pd
from loguru import logger

from .base_collector import BaseCollector


class MacroCollector(BaseCollector):
    """宏观经济数据采集器。"""

    asset_type = "macro"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ak = None

    def _get_ak(self):
        if self._ak is None:
            import akshare as ak
            self._ak = ak
        return self._ak

    def _indicators(self) -> Dict[str, Callable]:
        ak = self._get_ak()
        return {
            "CPI": ak.macro_china_cpi,
            "PPI": ak.macro_china_ppi,
            "PMI": ak.macro_china_pmi,
            "GDP": ak.macro_china_gdp,
            "M2": ak.macro_china_money_supply,
            "LPR1Y": ak.macro_china_lpr,
        }

    def collect(self, code: str) -> int:
        """采集单个宏观指标 -> macro_data。"""
        fn = self._indicators().get(code.upper())
        if fn is None:
            logger.warning(f"未知宏观指标: {code}")
            return 0
        try:
            df = fn()
        except Exception as e:
            logger.warning(f"{code} 宏观采集失败: {e}")
            return 0
        if df is None or df.empty:
            return 0

        # 取 product_id
        pid_df = self.store.query("SELECT product_id FROM products WHERE code = ?", [code.upper()])
        if pid_df.empty:
            logger.warning(f"宏观品种未建档: {code}")
            return 0
        pid = int(pid_df.iloc[0]["product_id"])

        # 第一列通常是日期/月份, 第二列是值 (各指标列名不同, 取前两数值列)
        date_col = df.columns[0]
        val_cols = [c for c in df.columns[1:] if pd.api.types.is_numeric_dtype(df[c])]
        if not val_cols:
            logger.warning(f"{code} 无数值列: {list(df.columns)}")
            return 0
        out = pd.DataFrame({
            "date": self._parse_date(df[date_col]),
            "product_id": pid,
            "value": pd.to_numeric(df[val_cols[0]], errors="coerce"),
            "source": "akshare",
        }).dropna(subset=["date", "value"])
        return self.store.upsert_df("macro_data", out, ["date", "product_id"])

    @staticmethod
    def _parse_date(s: pd.Series) -> pd.Series:
        """兼容 '2026年05月份' / '2026年第1季度' / '2026-05' / 标准日期。"""
        raw = s.astype(str)
        # 季度格式: 2026年第1季度 / 2025年第1-4季度 -> 季末月
        if raw.str.contains("季度").any():
            import re
            q_to_month = {"1": "03", "2": "06", "3": "09", "4": "12"}
            def conv(v: str) -> str:
                ym = re.search(r"(\d{4})年", v)
                # 取紧邻"季度"前的数字 (第1-4季度 -> 4, 第3季度 -> 3)
                q = re.search(r"([1-4])\s*季度", v)
                if not ym or not q:
                    return ""
                return f"{ym.group(1)}-{q_to_month[q.group(1)]}-01"
            return pd.to_datetime(raw.map(conv), errors="coerce")
        cleaned = (
            raw.str.replace("年", "-", regex=False)
            .str.replace("月份", "", regex=False)
            .str.replace("月", "", regex=False)
            .str.rstrip("-")
        )
        return pd.to_datetime(cleaned, errors="coerce")

    def collect_all(self) -> Dict[str, int]:
        return {code: self.collect(code) for code in self._indicators()}
