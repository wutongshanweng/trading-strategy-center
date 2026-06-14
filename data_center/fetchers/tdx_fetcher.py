"""
TDX (通达信) Fetcher — 中国市场实时行情获取器 (基于 easy-tdx)。

底层: easy-tdx 库 (UnifiedTdxClient)
支持: 中国期货实时行情 / K线 / 分笔成交 / 资金流向

TDX 市场编号 (已验证):
  Market 28 = CZCE (郑商所): MA(甲醇) FG(玻璃) CF(棉花) RM(菜粕) OI(菜油) SA(纯碱) AP(苹果) PF(短纤) PK(花生)
  Market 29 = DCE (大商所): I(铁矿石) J(焦炭) JM(焦煤) L(PE) EG(乙二醇) A(豆一) B(豆二) C(玉米) CS(淀粉) JD(鸡蛋) LH(生猪) EB(苯乙烯) 
  Market 30 = SHFE+INE (上期所+能源): CU(铜) AL(铝) AU(黄金) AG(白银) HC(热卷) NI(镍) RU(橡胶) BU(沥青) BC(国际铜) FU(燃料油) LU(低硫油) NR(20号胶)

API 方法 (已验证):
  goods_quotes([(market, code)])  → DataFrame (cols: market,code,name,pre_close,open,high,low,close,vol,amount,…)
  goods_kline(market, code, period, start, count) → DataFrame (cols: datetime,open,high,low,close,vol,amount)
  goods_list(market, start, count) → DataFrame (cols: category,market,code,name,desc)
  goods_tick_chart(market, code)   → DataFrame (分笔)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from ..core.base_fetcher import (
    BaseFetcher, KlineData, KlineInterval, RealtimeQuote,
    DataSourceStatus,
)

logger = logging.getLogger(__name__)


class TDXFetcher(BaseFetcher):
    """通达信数据获取器 — 中国期货实时行情 (基于 easy-tdx)"""

    name = "tdx"
    display_name = "TDX (通达信)"

    # ======== 已验证的 TDX 市场编号映射 ========
    # Market 28 = CZCE (郑商所)
    # Market 29 = DCE (大商所)
    # Market 30 = SHFE (上期所) + INE (能源中心)
    TDX_MARKET_CZCE = 28
    TDX_MARKET_DCE = 29
    TDX_MARKET_SHFE = 30

    # 品种 → (TDX市场, TDX品种代码前缀)
    FUTURES_MAP: Dict[str, Tuple[int, str]] = {
        # ---- SHFE (Market 30) ----
        "CU": (30, "CU"), "AL": (30, "AL"), "ZN": (30, "ZN"),
        "PB": (30, "PB"), "NI": (30, "NI"), "SN": (30, "SN"),
        "AU": (30, "AU"), "AG": (30, "AG"),
        "RB": (30, "RB"), "HC": (30, "HC"),
        "RU": (30, "RU"), "BU": (30, "BU"),
        "SP": (30, "SP"), "SS": (30, "SS"),
        "FU": (30, "FU"), "WR": (30, "WR"),
        # ---- INE (also Market 30) ----
        "SC": (30, "SC"), "NR": (30, "NR"),
        "LU": (30, "LU"), "BC": (30, "BC"),
        # ---- DCE (Market 29) ----
        "M": (29, "M"), "Y": (29, "Y"), "P": (29, "P"),
        "A": (29, "A"), "B": (29, "B"),
        "C": (29, "C"), "CS": (29, "CS"),
        "JD": (29, "JD"), "LH": (29, "LH"),
        "I": (29, "I"), "J": (29, "J"), "JM": (29, "JM"),
        "L": (29, "L"), "PP": (29, "PP"), "V": (29, "V"),
        "EG": (29, "EG"), "EB": (29, "EB"),
        "PG": (29, "PG"),
        # ---- CZCE (Market 28) ----
        "SR": (28, "SR"), "CF": (28, "CF"),
        "TA": (28, "TA"), "MA": (28, "MA"),
        "FG": (28, "FG"), "RM": (28, "RM"),
        "OI": (28, "OI"), "SA": (28, "SA"),
        "AP": (28, "AP"), "PK": (28, "PK"),
        "CJ": (28, "CJ"), "UR": (28, "UR"),
        "PF": (28, "PF"), "SM": (28, "SM"),
        "SF": (28, "SF"), "ZC": (28, "ZC"),
    }

    # K线周期 → Period 枚举值
    # Period.DAILY=4, WEEKLY=5, MONTHLY=6
    # MIN_5=0, MIN_15=1, MIN_30=2, MIN_60=3
    KLINE_PERIOD_MAP = {
        "1d": 4, "1w": 5, "1M": 6,
        "5m": 0, "15m": 1, "30m": 2, "60m": 3,
    }

    # 常规合约后缀（主力合约会去掉数字部分加特定后缀）
    MAIN_CONTRACT_SUFFIX = "L"  # 如 'M.L' 表示豆粕主力连续

    _client = None
    _connected = False

    def _get_client(self):
        """懒加载 TDX 客户端"""
        if not self._connected or self._client is None:
            try:
                from easy_tdx import UnifiedTdxClient
                self._client = UnifiedTdxClient()
                self._client.connect()
                self._connected = True
                logger.info("TDX client connected successfully")
            except ImportError:
                raise ImportError("请安装 easy-tdx: pip install easy-tdx")
            except Exception as e:
                self._connected = False
                logger.error(f"TDX 连接失败: {e}")
                raise
        return self._client

    def _resolve_contract(self, symbol: str, contract: Optional[str] = None) -> Tuple[int, str]:
        """
        解析品种 → (market, full_code)
        
        如果 contract 提供了具体合约号 (如 'M2609')，使用该合约。
        否则使用品种主力连续 (如 'M' -> 市场28上找 'M' 的相关合约)。
        """
        sym = symbol.upper()
        info = self.FUTURES_MAP.get(sym)
        if not info:
            return 0, sym

        market, code_prefix = info

        if contract:
            # 使用指定合约号
            return market, contract.upper()
        else:
            # 主力连续: 使用品种代码直接查询
            # TDX 中主力连续合约直接用品种代码前缀查询
            return market, code_prefix

    def get_kline(self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
                  start_date: Optional[str] = None, end_date: Optional[str] = None,
                  contract: Optional[str] = None) -> KlineData:
        """
        获取 K 线数据 (使用 goods_kline)，支持日期范围过滤和分页加载。
        
        TDX goods_kline 参数: market, code, period, start(偏移), count(数量,最大800)
        策略:
        - count=800 一次拉取 (日线约3年, M5约7天, M15约22天)
        - 若需要更早数据，分页向后偏移 (start+=800) 拉取
        - 拉取完后按 start_date/end_date 过滤
        """
        try:
            market, code = self._resolve_contract(symbol, contract)
            period = self.KLINE_PERIOD_MAP.get(interval.value, 4)
            client = self._get_client()

            # 日期范围解析
            start_dt = _parse_date(start_date)
            end_dt = _parse_date(end_date)

            # 估算需要多少根K线
            est_bars = self._estimate_bars(interval, start_dt, end_dt)
            page_size = 800
            all_data = []

            # 分页拉取（最多拉5页 = 4000根）
            for page in range(max(1, (est_bars + page_size - 1) // page_size)):
                if page >= 5:
                    break
                offset = page * page_size
                df = client.goods_kline(market, code, period=period,
                                         start=offset, count=page_size)

                if df is None or df.empty:
                    # 尝试主力连续 (L后缀)
                    if page == 0:
                        df = client.goods_kline(market, f"{code}L",
                                                 period=period, start=0, count=page_size)
                    if df is None or df.empty:
                        break

                all_data.append(df)

                # 如果返回不足 page_size，说明没更多数据了
                if len(df) < page_size:
                    break

            if not all_data:
                return KlineData(symbol=symbol, interval=interval.value,
                                 open=[], high=[], low=[], close=[],
                                 volume=[], timestamps=[], source=self.name)

            # 合并所有分页
            combined = pd.concat(all_data, ignore_index=True)
            combined = combined.drop_duplicates(subset=["datetime"]).sort_values("datetime")

            # 按日期范围过滤
            if start_dt:
                combined = combined[combined["datetime"] >= start_dt]
            if end_dt:
                combined = combined[combined["datetime"] <= end_dt]

            if combined.empty:
                return KlineData(symbol=symbol, interval=interval.value,
                                 open=[], high=[], low=[], close=[],
                                 volume=[], timestamps=[], source=self.name)

            return KlineData(
                symbol=symbol, interval=interval.value,
                open=combined["open"].tolist(),
                high=combined["high"].tolist(),
                low=combined["low"].tolist(),
                close=combined["close"].tolist(),
                volume=combined["vol"].tolist(),
                timestamps=pd.to_datetime(combined["datetime"]).tolist(),
                source=self.name, contract=contract,
            )
        except Exception as e:
            logger.warning(f"TDX get_kline failed for {symbol}: {e}")
            return KlineData(symbol=symbol, interval=interval.value,
                             open=[], high=[], low=[], close=[],
                             volume=[], timestamps=[], source=self.name)

    def _estimate_bars(self, interval: KlineInterval,
                        start_dt: Optional[datetime],
                        end_dt: Optional[datetime]) -> int:
        """估算日期范围内的K线数量（用于分页）"""
        if not start_dt or not end_dt:
            return 800
        days = (end_dt - start_dt).days
        interval_minutes = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "60m": 60, "1d": 1440, "1w": 10080, "1M": 43200,
        }
        mins = interval_minutes.get(interval.value, 1440)
        bars = int(days * 1440 / mins * 1.5)  # 1.5倍余量
        return max(200, min(bars, 4000))

    def get_realtime(self, symbol: str, contract: Optional[str] = None) -> RealtimeQuote:
        """
        获取实时行情 (使用 goods_quotes)。
        
        goods_quotes([(market, code)]) -> DataFrame
          columns: market, code, name, pre_close, open, high, low, close, vol, amount, ...
        """
        try:
            market, code = self._resolve_contract(symbol, contract)

            client = self._get_client()
            df = client.goods_quotes([(market, code)])

            if df is None or df.empty:
                # 试试主力连续
                main_code = f"{code}L"
                df = client.goods_quotes([(market, main_code)])

            if df is None or df.empty:
                logger.info(f"TDX quote empty for {symbol} (market={market}, code={code})")
                return self._empty_quote(symbol, contract)

            row = df.iloc[0]
            return RealtimeQuote(
                symbol=symbol,
                last_price=float(row.get("close", row.get("price", 0)) or 0),
                open_price=float(row.get("open", 0) or 0),
                high_price=float(row.get("high", 0) or 0),
                low_price=float(row.get("low", 0) or 0),
                pre_close=float(row.get("pre_close", 0) or 0),
                volume=int(row.get("vol", 0) or 0),
                turnover=float(row.get("amount", 0) or 0),
                bid_price=float(row.get("bid1", row.get("close", 0)) or 0),
                ask_price=float(row.get("ask1", row.get("close", 0)) or 0),
                bid_volume=int(row.get("bid_vol1", row.get("vol", 0)) or 0),
                ask_volume=int(row.get("ask_vol1", 0) or 0),
                timestamp=datetime.now(),
                source=self.name, contract=contract,
            )
        except Exception as e:
            logger.warning(f"TDX realtime failed for {symbol}: {e}")
            return self._empty_quote(symbol, contract)

    def get_batch_quotes(self, symbols: List[Tuple[str, Optional[str]]]) -> Dict[str, RealtimeQuote]:
        """
        批量获取实时行情。
        
        Args:
            symbols: [(symbol, contract_or_None), ...]
        """
        results = {}
        try:
            client = self._get_client()
            # 构建批量查询参数
            params = []
            for sym, contract in symbols:
                market, code = self._resolve_contract(sym, contract)
                params.append((market, code))

            df = client.goods_quotes(params)

            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    sym = row.get("code", "")
                    results[sym] = RealtimeQuote(
                        symbol=sym,
                        last_price=float(row.get("close", 0) or 0),
                        open_price=float(row.get("open", 0) or 0),
                        high_price=float(row.get("high", 0) or 0),
                        low_price=float(row.get("low", 0) or 0),
                        pre_close=float(row.get("pre_close", 0) or 0),
                        volume=int(row.get("vol", 0) or 0),
                        turnover=float(row.get("amount", 0) or 0),
                        bid_price=float(row.get("bid1", row.get("close", 0)) or 0),
                        ask_price=float(row.get("ask1", row.get("close", 0)) or 0),
                        bid_volume=int(row.get("bid_vol1", 0) or 0),
                        ask_volume=int(row.get("ask_vol1", 0) or 0),
                        timestamp=datetime.now(),
                        source=self.name,
                    )
        except Exception as e:
            logger.warning(f"TDX batch quotes failed: {e}")

        # 如果有单个查询失败的，逐个查询
        for sym, contract in symbols:
            if sym not in results:
                try:
                    results[sym] = self.get_realtime(sym, contract)
                except Exception:
                    pass

        return results

    def get_tick_data(self, symbol: str, contract: Optional[str] = None) -> pd.DataFrame:
        """获取分笔成交数据"""
        try:
            market, code = self._resolve_contract(symbol, contract)
            client = self._get_client()
            return client.goods_tick_chart(market, code)
        except Exception as e:
            logger.warning(f"TDX tick data failed: {e}")
            return pd.DataFrame()

    def get_transactions(self, symbol: str, date: Optional[str] = None,
                          contract: Optional[str] = None) -> pd.DataFrame:
        """获取逐笔成交"""
        try:
            market, code = self._resolve_contract(symbol, contract)
            client = self._get_client()
            return client.goods_transaction(market, code, date)
        except Exception as e:
            logger.warning(f"TDX transactions failed: {e}")
            return pd.DataFrame()

    def get_contract_list(self, symbol: str) -> List[str]:
        """获取品种的所有可用合约列表"""
        info = self.FUTURES_MAP.get(symbol.upper())
        if not info:
            return []
        market, prefix = info
        try:
            client = self._get_client()
            cnt = client.goods_count(market)
            lst = client.goods_list(market, 0, min(cnt, 500))
            if lst is not None and not lst.empty:
                contracts = []
                for _, row in lst.iterrows():
                    code = row["code"]
                    # 合约格式: 前缀 + 4位数字(2位年份+2位月份) 如 A2607, RB2609
                    # 严格匹配避免 'A' 匹配到 'AD', 'AL' 等不同品种
                    digits = code[len(prefix):]
                    if (code.startswith(prefix) and len(digits) == 4 
                        and digits.isdigit() and not code.endswith("L")):
                        contracts.append(code)
                return sorted(contracts)
        except Exception as e:
            logger.warning(f"TDX contract list failed: {e}")
        return []

    def validate(self) -> bool:
        """验证 TDX 连接 — 尝试连接并查询行情"""
        try:
            client = self._get_client()
            # 测试连接 — 使用多个市场/品种尝试
            test_pairs = [(30, "CU"), (29, "M"), (28, "MA")]
            for market, prefix in test_pairs:
                try:
                    # 先获取合约列表找到实际合约号
                    cnt = client.goods_count(market)
                    if cnt and cnt > 0:
                        lst = client.goods_list(market, 0, min(cnt, 100))
                        if lst is not None and not lst.empty:
                            for _, row in lst.iterrows():
                                code = row["code"]
                                digits = code[len(prefix):]
                                if (code.startswith(prefix) and len(digits) == 4 
                                    and digits.isdigit()):
                                    # 找到实际合约，查询行情
                                    df = client.goods_quotes([(market, code)])
                                    if df is not None and not df.empty:
                                        self._status = DataSourceStatus.ACTIVE
                                        self._connected = True
                                        return True
                except Exception:
                    continue
            
            # 连接成功但无实时数据（非交易时段）
            self._status = DataSourceStatus.DEGRADED
            self._connected = True
            return True
        except Exception:
            self._status = DataSourceStatus.DOWN
            self._connected = False
            return False

    def _empty_quote(self, symbol: str, contract: str = None) -> RealtimeQuote:
        return RealtimeQuote(
            symbol=symbol, last_price=0, open_price=0, high_price=0, low_price=0,
            pre_close=0, volume=0, turnover=0, bid_price=0, ask_price=0,
            bid_volume=0, ask_volume=0, timestamp=datetime.now(),
            source=self.name, contract=contract,
        )

    def _get_supported_markets(self) -> List[str]:
        return ["futures"]

    def _get_description(self) -> str:
        return "通达信(easy-tdx)数据接口，支持中国期货实时行情/K线/分笔成交，对中国期货市场支持最佳"


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """解析日期字符串 → datetime，支持多种格式"""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None
