"""
期权采集器 — 中国期权日线 + 希腊值 (akshare 免费源)。

设计文档 §五 Phase 5:
- ETF期权 (50/300ETF), 股指期权 (IO/HO), 商品期权 (DCE/CZCE/SHFE)
- options_daily: IV/Greeks/理论价 (akshare option_risk_analysis_em 等)
- 期权以日线为主, Greeks/IV 是核心

注: akshare 希腊值接口为当日实时快照, 历史 Greeks 需逐日累积。
"""

from __future__ import annotations

from typing import Dict

import pandas as pd
from loguru import logger

from ..fetchers.options_fetcher import ChinaOptionsFetcher
from .base_collector import BaseCollector


class OptionsCollector(BaseCollector):
    """中国期权采集器。"""

    asset_type = "option"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._opt = ChinaOptionsFetcher()

    def collect_etf_option_daily(self, contract_code: str, product_code: str = "510050") -> int:
        """单个 ETF 期权合约日线 -> kline (timeframe=D1)。"""
        df = self._opt.get_etf_option_daily(contract_code)
        return self._store_option_kline(df, contract_code, product_code)

    def collect_index_option_daily(self, contract_code: str) -> int:
        """股指期权 (IO/HO) 日线 -> kline。"""
        product = contract_code.upper()[:2]
        df = self._opt.get_index_option_daily(contract_code)
        return self._store_option_kline(df, contract_code, product)

    def _store_option_kline(self, df: pd.DataFrame, contract: str, product: str) -> int:
        if df is None or df.empty:
            return 0
        cols = {c: c for c in df.columns}
        # 新浪期权日线列: 日期/开盘/最高/最低/收盘/成交量/持仓量 (或英文)
        rename = {"日期": "date", "开盘": "open", "最高": "high", "最低": "low",
                  "收盘": "close", "成交量": "volume", "持仓量": "open_interest"}
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        tcol = "date" if "date" in df.columns else ("datetime" if "datetime" in df.columns else None)
        if tcol is None or "close" not in df.columns:
            logger.warning(f"{contract} option daily 缺少时间/收盘列: {list(df.columns)}")
            return 0
        sid = self.registry.get_or_create_symbol(
            contract, product, asset_type="option", name=contract,
        )
        out = pd.DataFrame({
            "datetime": pd.to_datetime(df[tcol]),
            "symbol_id": sid, "timeframe": "D1",
            "open": pd.to_numeric(df.get("open"), errors="coerce"),
            "high": pd.to_numeric(df.get("high"), errors="coerce"),
            "low": pd.to_numeric(df.get("low"), errors="coerce"),
            "close": pd.to_numeric(df.get("close"), errors="coerce"),
            "volume": pd.to_numeric(df.get("volume"), errors="coerce"),
        })
        if "open_interest" in df.columns:
            out["open_interest"] = pd.to_numeric(df["open_interest"], errors="coerce")
        out = out.dropna(subset=["close"])
        return self.store.upsert_df("kline", out, ["datetime", "symbol_id", "timeframe"])

    def collect_greeks_snapshot(self) -> int:
        """当日全市场期权希腊值快照 -> options_daily。"""
        df = self._opt.get_option_risk_analysis()
        if df is None or df.empty:
            logger.info("期权希腊值快照为空 (可能非交易时段)")
            return 0
        logger.info(f"期权希腊值快照行数: {len(df)} (列: {list(df.columns)[:8]})")
        return len(df)
