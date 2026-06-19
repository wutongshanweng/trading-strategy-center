"""
期货采集器 — 中国期货全合约 D1 + M5 (akshare 免费源)。

流程:
1. discover_contracts: futures_zh_realtime(品种中文名) -> 真实合约列表 (RB2610, RB2609...)
2. collect_contract: 单合约 D1 (futures_zh_daily_sina) + M5 (futures_zh_minute_sina)
3. 写入 DuckDB kline 表 (具体合约, 不搞合成)

设计原则: 存真实可交易合约, 主力连续 (RB0) 单独标记 is_main 处理。
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

from ..core.base_fetcher import KlineInterval
from ..core.retry import retry_sync
from ..fetchers.akshare_fetcher import AKShareFetcher
from .base_collector import BaseCollector


class FuturesCollector(BaseCollector):
    """期货数据采集器 (akshare 免费源)。"""

    asset_type = "futures"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ak_fetcher = AKShareFetcher()
        self._product_meta = self._ak_fetcher.FUTURES_SYMBOL_MAP

    def _ak(self):
        return self._ak_fetcher._get_ak()

    def discover_contracts(self, product_code: str) -> List[str]:
        """返回某品种当前所有真实合约代码 (剔除主力连续 RB0)。"""
        return self._discover(product_code)[0]

    def _discover(self, product_code: str) -> tuple[List[str], Optional[str]]:
        """返回 (合约代码列表, 主力合约代码)。主力按持仓量取最大, 退化用成交量。"""
        product_code = product_code.upper()
        meta = self.store.query(
            "SELECT name FROM products WHERE code = ?", [product_code]
        )
        cn_name = meta.iloc[0]["name"] if not meta.empty else product_code
        ak = self._ak()
        try:
            df = ak.futures_zh_realtime(symbol=cn_name)
            if df is None or df.empty or "symbol" not in df.columns:
                return [], None
            df = df.copy()
            df["symbol"] = df["symbol"].str.upper()
            # 剔除连续合约 (以 0 结尾且无月份, 如 RB0)
            def _is_real(c: str) -> bool:
                return (not c.endswith("0")) or any(ch.isdigit() for ch in c[len(product_code):-1])
            df = df[df["symbol"].map(_is_real)]
            codes = df["symbol"].tolist()
            main = self._pick_main(df)
            return codes, main
        except Exception as e:
            logger.warning(f"discover_contracts({product_code}) failed: {e}")
            return [], None

    @staticmethod
    def _pick_main(df: pd.DataFrame) -> Optional[str]:
        """按持仓量(优先)或成交量选主力合约代码。"""
        for col in ("position", "hold", "持仓量", "volume", "成交量"):
            if col in df.columns:
                s = pd.to_numeric(df[col], errors="coerce")
                if s.notna().any():
                    return df.loc[s.idxmax(), "symbol"]
        return df.iloc[0]["symbol"] if not df.empty else None


    def collect_contract(self, contract: str, product_code: str,
                         exchange: Optional[str] = None,
                         with_minute: bool = True,
                         start_date: Optional[str] = None) -> Dict[str, int]:
        """采集单个真实合约 D1 + M5。start_date (YYYY-MM-DD) 可选, 只保留该日期之后的数据。"""
        written: Dict[str, int] = {}
        ak = self._ak()
        exch = exchange or self._product_meta.get(product_code.upper(), {}).get("exchange")
        cutoff = pd.to_datetime(start_date) if start_date else None

        def _trim(df: pd.DataFrame) -> pd.DataFrame:
            if cutoff is None or df is None or df.empty:
                return df
            tcol = "date" if "date" in df.columns else ("datetime" if "datetime" in df.columns else None)
            if tcol is None:
                return df
            return df[pd.to_datetime(df[tcol]) >= cutoff]

        # D1
        try:
            df = retry_sync(ak.futures_zh_daily_sina, symbol=contract)
            d1 = _trim(self._ak_fetcher._clean_futures_df(df))
            written["D1"] = self._store_df(d1, contract, product_code, "D1", exch)
        except Exception as e:
            logger.warning(f"{contract} D1 failed: {e}")
            written["D1"] = 0

        # M5 (近期)
        if with_minute:
            try:
                dfm = retry_sync(ak.futures_zh_minute_sina, symbol=contract, period="5")
                m5 = _trim(self._ak_fetcher._clean_futures_df(dfm))
                written["M5"] = self._store_df(m5, contract, product_code, "M5", exch)
            except Exception as e:
                logger.warning(f"{contract} M5 failed: {e}")
                written["M5"] = 0

        return written

    def mark_main_contract(self, product_code: str, main_code: str) -> None:
        """记录某品种主力合约到 main_contracts 表。
        用独立表而非 UPDATE symbols.is_main — DuckDB 禁止 UPDATE 被 kline 外键引用的行。"""
        if not main_code:
            return
        pid = self.store.query(
            "SELECT product_id FROM products WHERE code = ?", [product_code.upper()]
        )
        if pid.empty:
            return
        product_id = int(pid.iloc[0]["product_id"])
        try:
            self.store.execute("DELETE FROM main_contracts WHERE product_id = ?", [product_id])
            self.store.execute(
                "INSERT INTO main_contracts (product_id, symbol_code) VALUES (?, ?)",
                [product_id, main_code.upper()],
            )
        except Exception as e:  # noqa: BLE001 — 标注失败不影响采集主流程
            logger.warning(f"主力标注失败 {product_code}->{main_code}: {e}")


    def _store_df(self, df: pd.DataFrame, contract: str, product_code: str,
                  timeframe: str, exchange: Optional[str]) -> int:
        """清洗后的期货 DataFrame -> kline 表 (含 open_interest/settlement)。"""
        if df is None or df.empty:
            return 0
        sid = self.registry.get_or_create_symbol(
            contract, product_code, asset_type="futures", exchange=exchange, name=contract,
        )
        tcol = "date" if "date" in df.columns else "datetime"
        out = pd.DataFrame({
            "datetime": pd.to_datetime(df[tcol]),
            "symbol_id": sid,
            "timeframe": timeframe,
            "open": pd.to_numeric(df.get("open"), errors="coerce"),
            "high": pd.to_numeric(df.get("high"), errors="coerce"),
            "low": pd.to_numeric(df.get("low"), errors="coerce"),
            "close": pd.to_numeric(df.get("close"), errors="coerce"),
            "volume": pd.to_numeric(df.get("volume"), errors="coerce"),
        })
        if "open_interest" in df.columns:
            out["open_interest"] = pd.to_numeric(df["open_interest"], errors="coerce")
        if "settlement" in df.columns:
            out["settlement"] = pd.to_numeric(df["settlement"], errors="coerce")
        out = out.dropna(subset=["close"])
        # 生命周期守卫: 真实合约不应有生命周期外数据 (防误存主力连续)
        from ..knowledge.contract_lifecycle import lifecycle_guard
        before = len(out)
        out = lifecycle_guard(out, contract, "datetime")
        if len(out) < before:
            logger.warning(f"{contract} 裁剪 {before - len(out)} 条生命周期外数据 "
                           f"(疑似误存连续合约)")
        return self.store.upsert_df("kline", out, ["datetime", "symbol_id", "timeframe"])

    def collect_product(self, product_code: str, with_minute: bool = True,
                        sleep: float = 0.3, start_date: Optional[str] = None) -> Dict[str, int]:
        """采集某品种当前在交易的真实合约 (实时枚举, 供同步器增量用)。不标注主力。"""
        contracts, _ = self._discover(product_code)
        return self._collect_codes(product_code, contracts, with_minute, sleep, start_date)

    def collect_product_year(self, product_code: str, year: int,
                             with_minute: bool = False, sleep: float = 0.3,
                             start_date: Optional[str] = None) -> Dict[str, int]:
        """按年份枚举某品种全部12个月合约 (M2601~M2612) 并下载。
        过期/无数据的合约自然为空。不判断主力 — 主力标注是独立动作。"""
        yy = f"{year % 100:02d}"
        codes = [f"{product_code.upper()}{yy}{m:02d}" for m in range(1, 13)]
        return self._collect_codes(product_code, codes, with_minute, sleep, start_date)

    def _collect_codes(self, product_code: str, codes: List[str], with_minute: bool,
                       sleep: float, start_date: Optional[str]) -> Dict[str, int]:
        """下载一组合约代码。返回各周期写入行数 + 合约数。"""
        totals: Dict[str, int] = {"D1": 0, "M5": 0, "contracts": 0}
        for c in codes:
            res = self.collect_contract(c, product_code, with_minute=with_minute,
                                        start_date=start_date)
            written = res.get("D1", 0) + res.get("M5", 0)
            totals["D1"] += res.get("D1", 0)
            totals["M5"] += res.get("M5", 0)
            if written > 0:
                totals["contracts"] += 1
            time.sleep(sleep)  # 限速, 避免被封
        return totals

    def refresh_main_contract(self, product_code: str) -> Optional[str]:
        """按实时持仓量算主力并写 main_contracts 表。独立于下载。返回主力代码。"""
        _, main = self._discover(product_code)
        self.mark_main_contract(product_code, main)
        return main
