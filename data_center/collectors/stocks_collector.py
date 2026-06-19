"""
股票采集器 — A股 D1 (BaoStock 免费) + 基本信息/财报 (akshare 免费)。

流程:
1. collect_kline: BaoStock 前复权日线 -> kline 表 (timeframe=D1)
2. collect_info:   akshare 个股信息 -> stocks_info
3. collect_financial: akshare 财务指标 -> stocks_financial
"""

from __future__ import annotations

from typing import Dict, Optional

import pandas as pd
from loguru import logger

from ..core.base_fetcher import KlineInterval
from ..fetchers.baostock_fetcher import BaoStockFetcher
from .base_collector import BaseCollector


class StocksCollector(BaseCollector):
    """A股数据采集器。"""

    asset_type = "stock"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bs = BaoStockFetcher()
        self._ak = None

    def _get_ak(self):
        if self._ak is None:
            import akshare as ak
            self._ak = ak
        return self._ak

    def list_all_symbols(self, retries: int = 3) -> list[str]:
        """拉沪深全部 A 股代码 (带 .SH/.SZ 后缀)。退市/停牌的由下载时自然为空。

        主源用静态代码表 stock_info_a_code_name (稳定), 失败退到实时行情 spot_em。
        带重试+退避 — 用户环境网络波动 (RemoteDisconnected) 时不至于直接返回空。
        """
        import time
        ak = self._get_ak()

        def _extract(df, code_col: str) -> list[str]:
            if df is None or df.empty or code_col not in df.columns:
                return []
            out = []
            for code in df[code_col].astype(str):
                c = code.strip()
                if len(c) != 6 or not c.isdigit():
                    continue
                out.append(f"{c}.{'SH' if c[0] == '6' else 'SZ'}")
            return out

        for attempt in range(retries):
            try:
                df = ak.stock_info_a_code_name()  # 静态表: code/name
                codes = _extract(df, "code")
                if codes:
                    return codes
            except Exception as e:
                logger.warning(f"stock_info_a_code_name 第{attempt+1}次失败: {e}")
            try:
                df = ak.stock_zh_a_spot_em()  # 兜底: 实时行情
                codes = _extract(df, "代码")
                if codes:
                    return codes
            except Exception as e:
                logger.warning(f"stock_zh_a_spot_em 第{attempt+1}次失败: {e}")
            time.sleep(2 * (attempt + 1))  # 退避
        logger.error("全市场A股清单拉取失败 (网络波动?), 返回空")
        return []

    def collect_kline(self, symbol: str, start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> int:
        """BaoStock 前复权日线 -> kline。symbol 带后缀 600019.SH。"""
        data = self._bs.get_kline(symbol, KlineInterval.DAY, start_date, end_date)
        if not data or not data.timestamps:
            return 0
        sid = self.registry.get_or_create_symbol(
            symbol, symbol, asset_type="stock", name=symbol,
        )
        df = pd.DataFrame({
            "datetime": pd.to_datetime(data.timestamps),
            "symbol_id": sid, "timeframe": "D1",
            "open": data.open, "high": data.high, "low": data.low,
            "close": data.close, "volume": data.volume,
        })
        return self.store.upsert_df("kline", df, ["datetime", "symbol_id", "timeframe"])

    def collect_info(self, symbol: str) -> int:
        """akshare 个股信息 -> stocks_info。返回 1=写入 / 0=无数据。"""
        ak = self._get_ak()
        code = symbol.split(".")[0]
        try:
            df = ak.stock_individual_info_em(symbol=code)
        except Exception as e:
            logger.warning(f"{symbol} info failed: {e}")
            return 0
        if df is None or df.empty:
            return 0
        return self._store_info(df, symbol)

    def _store_info(self, df: pd.DataFrame, symbol: str) -> int:
        """item/value 两列 -> stocks_info 一行。"""
        # akshare 返回列名 item/value 或 中文; 统一成 dict
        cols = list(df.columns)
        kcol, vcol = cols[0], cols[1]
        kv = {str(r[kcol]): r[vcol] for _, r in df.iterrows()}
        sid = self.registry.get_or_create_symbol(
            symbol, symbol, asset_type="stock", name=str(kv.get("股票简称", symbol)))
        listing = kv.get("上市时间")
        listing_date = None
        if listing not in (None, "", "-"):
            try:
                listing_date = pd.to_datetime(str(int(float(listing))), format="%Y%m%d").date()
            except (ValueError, TypeError):
                try:
                    listing_date = pd.to_datetime(str(listing)).date()
                except (ValueError, TypeError):
                    listing_date = None
        row = pd.DataFrame([{
            "symbol_id": sid,
            "company_name": str(kv.get("股票简称", "")) or None,
            "industry": str(kv.get("行业", "")) or None,
            "listing_date": listing_date,
            "total_shares": _bigint(kv.get("总股本")),
            "float_shares": _bigint(kv.get("流通股")),
            "market_cap": _dec(kv.get("总市值")),
        }])
        n = self.store.upsert_df("stocks_info", row, ["symbol_id"])
        logger.info(f"{symbol} info 入库 (行业={kv.get('行业')})")
        return n

    def collect_financial(self, symbol: str) -> int:
        """akshare 财务摘要 -> stocks_financial。返回写入的报告期行数。"""
        ak = self._get_ak()
        code = symbol.split(".")[0]
        try:
            df = ak.stock_financial_abstract(symbol=code)
        except Exception as e:
            logger.warning(f"{symbol} financial failed: {e}")
            return 0
        if df is None or df.empty:
            return 0
        return self._store_financial(df, symbol)

    def _store_financial(self, df: pd.DataFrame, symbol: str) -> int:
        """财务摘要 (指标行 × 报告期列) -> stocks_financial 多行。

        akshare stock_financial_abstract: 列含 '选项'/'指标' + 多个报告期列 (YYYYMMDD)。
        转置: 每个报告期一行, 抽取核心指标。结构因版本而异 -> 用关键词模糊匹配。
        """
        idx_col = "指标" if "指标" in df.columns else df.columns[min(1, len(df.columns) - 1)]
        date_cols = [c for c in df.columns if str(c).isdigit() and len(str(c)) == 8]
        if not date_cols:
            logger.warning(f"{symbol} 财务摘要无报告期列: {list(df.columns)[:6]}")
            return 0
        sid = self.registry.get_or_create_symbol(symbol, symbol, asset_type="stock", name=symbol)

        def _find(*keywords) -> Optional[pd.Series]:
            for _, r in df.iterrows():
                name = str(r[idx_col])
                if any(k in name for k in keywords):
                    return r
            return None

        metrics = {
            "revenue": _find("营业总收入", "营业收入"),
            "net_profit": _find("净利润", "归母净利润"),
            "eps": _find("每股收益", "基本每股收益"),
            "bvps": _find("每股净资产"),
            "roe": _find("净资产收益率", "ROE"),
            "gross_margin": _find("毛利率", "销售毛利率"),
            "net_margin": _find("净利率", "销售净利率"),
            "debt_ratio": _find("资产负债率"),
        }
        rows = []
        for dc in date_cols:
            rep = pd.to_datetime(str(dc), format="%Y%m%d").date()
            rows.append({
                "symbol_id": sid, "report_date": rep,
                "report_type": _report_type(rep),
                **{k: (_dec(s[dc]) if s is not None else None) for k, s in metrics.items()},
            })
        out = pd.DataFrame(rows)
        n = self.store.upsert_df("stocks_financial", out, ["symbol_id", "report_date"])
        logger.info(f"{symbol} financial 入库 {n} 个报告期")
        return n

    def _latest_synced_dates(self) -> Dict[str, pd.Timestamp]:
        """每只已入库股票的最新 D1 日期 (symbol code -> 最新 datetime)。"""
        df = self.store.query(
            """SELECT sy.code, MAX(k.datetime) AS last_dt
               FROM kline k JOIN symbols sy ON k.symbol_id = sy.symbol_id
               JOIN products p ON sy.product_id = p.product_id
               WHERE p.asset_type = 'stock' AND k.timeframe = 'D1'
               GROUP BY sy.code"""
        )
        if df.empty:
            return {}
        return {r["code"].upper(): pd.Timestamp(r["last_dt"]) for _, r in df.iterrows()}

    def _latest_trade_date(self) -> Optional[pd.Timestamp]:
        """交易日历里 <= 今天的最近交易日 (判断哪些票落后)。"""
        ak = self._get_ak()
        try:
            cal = ak.tool_trade_date_hist_sina()
            cal["trade_date"] = pd.to_datetime(cal["trade_date"])
            past = cal[cal["trade_date"] <= pd.Timestamp.now().normalize()]
            return past["trade_date"].max() if not past.empty else None
        except Exception as e:
            logger.warning(f"交易日历获取失败: {e}")
            return None

    def incremental_sync(self, symbols: Optional[list[str]] = None,
                         buffer_days: int = 5, full_start: str = "2015-01-01") -> Dict[str, int]:
        """增量同步: 只拉落后于最近交易日的票。

        - 未入库的票: 从 full_start 全量拉。
        - 已入库但落后的票: 从 (最新日期 - buffer_days) 补齐 (buffer 容忍前复权回填)。
        - 已是最新的票: 跳过。
        symbols 留空 = 全市场。返回 {synced, skipped, new, rows, universe}。
        """
        symbols = symbols or self.list_all_symbols()
        target = self._latest_trade_date()
        synced_map = self._latest_synced_dates()
        stats = {"synced": 0, "skipped": 0, "new": 0, "rows": 0, "universe": len(symbols)}

        for code in symbols:
            up = code.upper()
            last = synced_map.get(up)
            if last is None:
                start = full_start
                stats["new"] += 1
            elif target is not None and last >= target:
                stats["skipped"] += 1
                continue
            else:
                start = (last - pd.Timedelta(days=buffer_days)).strftime("%Y-%m-%d")
            try:
                n = self.collect_kline(code, start_date=start)
                stats["rows"] += n
                stats["synced"] += 1
            except Exception as e:  # noqa: BLE001
                logger.warning(f"{code} 增量同步失败: {e}")
        logger.info(f"股票增量同步: {stats}")
        return stats


def _bigint(v):
    n = pd.to_numeric(v, errors="coerce")
    return None if pd.isna(n) else int(n)


def _dec(v):
    if isinstance(v, str):
        v = v.replace("%", "").replace(",", "").strip()
    n = pd.to_numeric(v, errors="coerce")
    return None if pd.isna(n) else float(n)


def _report_type(d) -> str:
    m = d.month
    return {3: "Q1", 6: "Q2", 9: "Q3", 12: "annual"}.get(m, f"M{m}")
