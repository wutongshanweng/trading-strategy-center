"""
Data Center — 单元测试。

覆盖模块:
- core: BaseFetcher, DataSourceManager, KlineInterval, KlineData, RealtimeQuote
- knowledge: ContractKnowledgeBase, MainContractResolver, exchanges
- history: DownloadManager, DataStore
- verification: DataVerifier, QualityReport, CrossValidationResult
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import os
import tempfile
from datetime import datetime, date
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import pytest

# ====================================================================
#  core / base_fetcher
# ====================================================================

from data_center.core.base_fetcher import (
    BaseFetcher, KlineData, KlineInterval, RealtimeQuote,
    DataSourceStatus, DataSourceInfo,
)


class TestKlineInterval:
    """K线周期枚举测试"""

    def test_values(self):
        assert KlineInterval.M1.value == "1m"
        assert KlineInterval.M5.value == "5m"
        assert KlineInterval.M15.value == "15m"
        assert KlineInterval.M30.value == "30m"
        assert KlineInterval.M60.value == "60m"
        assert KlineInterval.DAY.value == "1d"
        assert KlineInterval.WEEK.value == "1w"
        assert KlineInterval.MONTH.value == "1M"

    def test_all_cover_required(self):
        """必须覆盖用户要求的 M5/M15/M30/1H + 日/周/月"""
        values = {i.value for i in KlineInterval}
        required = {"5m", "15m", "30m", "60m", "1d", "1w", "1M"}
        assert required.issubset(values), f"Missing: {required - values}"


class TestKlineData:
    """K线数据模型测试"""

    def test_minimal_create(self):
        kd = KlineData(
            symbol="M", interval="1d",
            open=[], high=[], low=[], close=[], volume=[], timestamps=[],
            source="test",
        )
        assert kd.symbol == "M"
        assert kd.interval == "1d"
        assert len(kd.timestamps) == 0

    def test_with_data(self):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        kd = KlineData(
            symbol="RB", interval="1d",
            open=[4000, 4010, 4020, 4015, 4030],
            high=[4020, 4030, 4040, 4030, 4045],
            low=[3990, 4000, 4010, 4005, 4020],
            close=[4010, 4020, 4015, 4030, 4040],
            volume=[1000, 1200, 1100, 1300, 1400],
            timestamps=dates.tolist(),
            source="test", contract="RB2505",
        )
        assert len(kd.close) == 5
        assert kd.close[-1] == 4040
        assert kd.source == "test"
        assert kd.contract == "RB2505"


class TestRealtimeQuote:
    """实时行情模型测试"""

    def test_create(self):
        now = datetime.now()
        q = RealtimeQuote(
            symbol="M2609", last_price=2761.0,
            open_price=2750.0, high_price=2780.0, low_price=2745.0,
            pre_close=2755.0, volume=50000, turnover=137500000.0,
            bid_price=2760.0, ask_price=2762.0,
            bid_volume=100, ask_volume=200,
            timestamp=now, source="tdx", contract="M2609",
        )
        assert q.symbol == "M2609"
        assert q.last_price == 2761.0
        assert q.bid_volume == 100
        assert q.source == "tdx"


class TestBaseFetcher:
    """BaseFetcher 抽象基类测试"""

    def test_cannot_instantiate_abstract(self):
        """抽象基类不能直接实例化"""
        with pytest.raises(TypeError):
            BaseFetcher()

    def test_concrete_subclass(self):
        """实现所有抽象方法后可实例化"""
        class TestFetcher(BaseFetcher):
            name = "test"
            display_name = "Test"

            def get_kline(self, *a, **kw):
                return KlineData("T", "1d", [], [], [], [], [], [], "test")
            def get_realtime(self, *a, **kw):
                return RealtimeQuote("T", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, datetime.now(), "test")

        f = TestFetcher()
        assert f.name == "test"
        assert f.display_name == "Test"
        assert f.info.name == "test"


# ====================================================================
#  core / data_source
# ====================================================================

from data_center.core.data_source import DataSourceManager


class TestDataSourceManager:
    """数据源管理器测试"""

    def test_empty_manager(self):
        mgr = DataSourceManager()
        assert mgr.list_sources() == []

    def test_register_fetcher(self):
        """注册一个模拟获取器"""
        class MockFetcher(BaseFetcher):
            name = "mock"
            display_name = "Mock"
            def get_kline(self, *a, **kw):
                return KlineData("M", "1d", [1], [2], [3], [4], [5], [datetime.now()], [], "mock")
            def get_realtime(self, *a, **kw):
                return RealtimeQuote("M", 100, 99, 101, 98, 99, 1000, 100000, 100, 101, 10, 20, datetime.now(), "mock")

        mgr = DataSourceManager()
        mgr.register(MockFetcher(), priority=10)
        sources = mgr.list_sources()
        assert len(sources) == 1
        assert sources[0].name == "mock"

    def test_priority_ordering(self):
        """低 priority 值应先返回"""
        class LowFetcher(BaseFetcher):
            name = "low"
            display_name = "Low"
            def get_kline(self, *a, **kw):
                return KlineData("T", "1d", [], [], [], [], [], [], "low")
            def get_realtime(self, *a, **kw):
                return RealtimeQuote("T", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, datetime.now(), "low")

        class HighFetcher(BaseFetcher):
            name = "high"
            display_name = "High"
            def get_kline(self, *a, **kw):
                return KlineData("T", "1d", [], [], [], [], [], [], "high")
            def get_realtime(self, *a, **kw):
                return RealtimeQuote("T", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, datetime.now(), "high")

        mgr = DataSourceManager()
        mgr.register(HighFetcher(), priority=100)
        mgr.register(LowFetcher(), priority=10)
        # 第一个应该是 low（priority=10 更优先）
        assert mgr.get_best_source("T").name == "low"

    def test_get_futures_info(self):
        mgr = DataSourceManager()
        info = mgr.get_futures_info("M")
        assert info is not None
        assert info["exchange"] == "DCE"
        assert info["name"] == "豆粕"
        assert info["category"] == "农产品"

        info = mgr.get_futures_info("CU")
        assert info is not None
        assert info["exchange"] == "SHFE"

        info = mgr.get_futures_info("nonexistent")
        assert info is None

    def test_market_has_all_major_symbols(self):
        """验证主要期货品种都在映射中"""
        mgr = DataSourceManager()
        major = ["CU", "AL", "ZN", "AU", "AG", "RB", "HC",
                 "M", "Y", "P", "I", "J", "JM", "L", "PP",
                 "SR", "CF", "TA", "MA", "FG", "RM", "OI", "SA",
                 "SC", "IF", "IH", "IC"]
        for sym in major:
            info = mgr.get_futures_info(sym)
            assert info is not None, f"Missing: {sym}"


# ====================================================================
#  knowledge / contract_knowledge
# ====================================================================

from data_center.knowledge.contract_knowledge import ContractKnowledgeBase, ContractDetail


class TestContractKnowledgeBase:
    """合约知识库测试"""

    def setup_method(self):
        self.kb = ContractKnowledgeBase()

    def test_major_contracts_exist(self):
        """验证主要品种都存在"""
        for sym in ["CU", "M", "RB", "AU", "AG", "SC", "IF", "I", "MA", "CF"]:
            c = self.kb.get_contract(sym)
            assert c is not None, f"合约 {sym} 不存在"

    def test_contract_detail_fields(self):
        """验证合约字段正确"""
        cu = self.kb.get_contract("CU")
        assert cu is not None
        assert cu.symbol == "CU"
        assert cu.exchange == "SHFE"
        assert cu.name_cn == "沪铜"
        assert cu.contract_multiplier == 5
        assert cu.min_tick == 10
        assert cu.margin_rate > 0
        assert cu.commission_open > 0
        assert cu.commission_type in ("fixed", "ratio")
        assert cu.price_limit_pct > 0

    def test_all_contracts_have_required_fields(self):
        """所有合约必须填写关键字段"""
        required_fields = [
            "symbol", "exchange", "name_cn", "contract_multiplier",
            "min_tick", "margin_rate", "commission_open",
            "price_limit_pct", "delivery_months",
        ]
        for sym, c in self.kb._contracts.items():
            for field in required_fields:
                val = getattr(c, field, None)
                assert val is not None, f"{sym}.{field} is None"

    def test_list_by_exchange(self):
        shfe = self.kb.list_by_exchange("SHFE")
        dce = self.kb.list_by_exchange("DCE")
        czce = self.kb.list_by_exchange("CZCE")
        assert len(shfe) > 0
        assert len(dce) > 0
        assert len(czce) > 0
        for c in shfe:
            assert c.exchange == "SHFE"

    def test_list_by_category(self):
        metals = self.kb.list_by_category("金属")
        agri = self.kb.list_by_category("农产品")
        assert len(metals) > 0
        assert len(agri) > 0

    def test_search(self):
        results = self.kb.search("铜")
        assert len(results) >= 1
        assert any("铜" in c.name_cn for c in results)

    def test_get_all_exchanges(self):
        exchanges = self.kb.get_all_exchanges()
        exchange_codes = {e["exchange"] for e in exchanges}
        assert "SHFE" in exchange_codes
        assert "DCE" in exchange_codes
        assert "CZCE" in exchange_codes
        assert "CFFEX" in exchange_codes

    def test_list_all_symbols(self):
        symbols = self.kb.list_all_symbols()
        assert len(symbols) >= 50  # 至少有50+品种
        assert "CU" in symbols
        assert "M" in symbols
        assert "RB" in symbols


# ====================================================================
#  knowledge / main_contract
# ====================================================================

from data_center.knowledge.main_contract import MainContractResolver


class TestMainContractResolver:
    """主力合约解析器测试"""

    def setup_method(self):
        self.resolver = MainContractResolver()

    def test_parse_full_contract_code(self):
        result = self.resolver.parse_contract_code("M2609")
        assert result["symbol"] == "M"
        assert result["year"] == 2026
        assert result["month"] == 9
        assert result["full_code"] == "M2609"
        assert not result["is_main_contract"]

    def test_parse_short_code(self):
        """无年份的短格式: M09"""
        result = self.resolver.parse_contract_code("M05")
        assert result["symbol"] == "M"
        assert result["month"] == 5
        # 年份自动推断
        assert result["year"] is not None

    def test_parse_just_symbol(self):
        """纯品种代码（无合约号）"""
        result = self.resolver.parse_contract_code("RB")
        assert result["symbol"] == "RB"
        assert result["is_main_contract"]

    def test_get_main_contract_month(self):
        month = self.resolver.get_main_contract_month("M", 6)
        assert month in [1, 5, 7, 8, 9, 11, 12]

        month = self.resolver.get_main_contract_month("RB", 6)
        assert month in list(range(1, 13))

    def test_get_main_contract_code(self):
        code = self.resolver.get_main_contract_code("M")
        assert code.startswith("M")
        assert len(code) == 5  # M + 2位年 + 2位月

    def test_get_contract_cycle(self):
        cycle = self.resolver.get_contract_cycle("M", 3)
        assert len(cycle) == 3
        for c in cycle:
            assert c.startswith("M")

    def test_is_valid_contract_month_valid(self):
        assert self.resolver.is_valid_contract_month("M", 9)
        assert self.resolver.is_valid_contract_month("M", 1)
        assert self.resolver.is_valid_contract_month("CU", 3)

    def test_is_valid_contract_month_invalid(self):
        # 未知品种默认所有月份有效
        assert self.resolver.is_valid_contract_month("ZZ", 5)
        # 国债只在 3/6/9/12 月交割
        assert self.resolver.is_valid_contract_month("T", 3)  # 国债 3/6/9/12
        assert not self.resolver.is_valid_contract_month("T", 5)  # 5月不是国债交割月

    def test_get_switch_date(self):
        date = self.resolver.get_switch_date("M")
        assert isinstance(date, str)
        assert "-" in date


# ====================================================================
#  knowledge / exchanges
# ====================================================================

from data_center.knowledge.exchanges import EXCHANGES, list_exchanges, get_exchange


class TestExchanges:
    """交易所信息测试"""

    def test_all_exchanges_present(self):
        codes = {"SHFE", "DCE", "CZCE", "CFFEX", "INE", "GFEX"}
        assert set(EXCHANGES.keys()) == codes

    def test_exchange_details(self):
        shfe = EXCHANGES["SHFE"]
        assert shfe.name_cn == "上海期货交易所"
        assert shfe.website == "https://www.shfe.com.cn"
        assert shfe.futures_count > 0

    def test_list_exchanges(self):
        lst = list_exchanges()
        assert len(lst) == 6

    def test_get_exchange(self):
        e = get_exchange("dce")  # 小写
        assert e is not None
        assert e.name_cn == "大连商品交易所"

        e = get_exchange("invalid")
        assert e is None


# ====================================================================
#  history / download_manager
# ====================================================================

from data_center.history.download_manager import DownloadManager, DownloadStatus


class TestDownloadManager:
    """下载管理器测试"""

    def setup_method(self):
        from data_center.core.data_source import DataSourceManager
        self.source_mgr = DataSourceManager()
        self.manager = DownloadManager(self.source_mgr)

    def test_create_task(self):
        task = self.manager.create_task("M", KlineInterval.DAY)
        assert task.symbol == "M"
        assert task.interval == KlineInterval.DAY
        assert task.status == DownloadStatus.PENDING
        assert task.id is not None

    def test_create_task_with_contract(self):
        task = self.manager.create_task("M", KlineInterval.DAY,
                                         contract="M2609")
        assert task.contract == "M2609"

    def test_list_tasks(self):
        self.manager.create_task("RB")
        self.manager.create_task("CU")
        tasks = self.manager.list_tasks()
        assert len(tasks) == 2

    def test_get_statistics_empty(self):
        stats = self.manager.get_statistics()
        assert stats["total_tasks"] == 0

    def test_get_statistics_after_tasks(self):
        self.manager.create_task("M")
        stats = self.manager.get_statistics()
        assert stats["total_tasks"] == 1
        assert stats["unique_symbols"] == 1

    def test_get_supported_intervals(self):
        intervals = self.manager.get_supported_intervals()
        assert "1d" in intervals
        assert "5m" in intervals
        assert "15m" in intervals
        assert "30m" in intervals
        assert "60m" in intervals

    def test_task_display_name(self):
        task = self.manager.create_task("M", KlineInterval.DAY,
                                         contract="M2609")
        assert "M" in task.display_name
        assert "M2609" in task.display_name
        assert "1d" in task.display_name


# ====================================================================
#  history / data_store
# ====================================================================

from data_center.history.data_store import DataStore


class TestDataStore:
    """数据存储测试"""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = DataStore(base_path=self.tmpdir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_load_kline(self):
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        data = KlineData(
            symbol="M", interval="1d",
            open=[1, 2, 3], high=[2, 3, 4], low=[0, 1, 2],
            close=[1.5, 2.5, 3.5], volume=[100, 200, 300],
            timestamps=dates.tolist(), source="test",
        )
        ok = self.store.save_kline(data)
        assert ok

        loaded = self.store.load_kline("M", "1d")
        assert loaded is not None
        assert loaded.close == [1.5, 2.5, 3.5]
        assert loaded.source == "cache"

    def test_save_with_contract(self):
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        data = KlineData(
            symbol="M", interval="1d",
            open=[1, 2], high=[2, 3], low=[0, 1],
            close=[1.5, 2.5], volume=[100, 200],
            timestamps=dates.tolist(), source="test", contract="M2609",
        )
        ok = self.store.save_kline(data)
        assert ok
        assert self.store.exists("M", "1d", contract="M2609")

    def test_exists(self):
        assert not self.store.exists("NONEXIST", "1d")

    def test_list_available(self):
        avail = self.store.list_available("futures")
        # 目录可能不存在
        assert isinstance(avail, list)

    def test_delete(self):
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        data = KlineData(
            symbol="M", interval="1d",
            open=[1, 2], high=[2, 3], low=[0, 1],
            close=[1.5, 2.5], volume=[100, 200],
            timestamps=dates.tolist(), source="test",
        )
        self.store.save_kline(data)
        assert self.store.exists("M", "1d")
        deleted = self.store.delete("M", "1d")
        assert deleted
        assert not self.store.exists("M", "1d")

    def test_get_storage_usage(self):
        usage = self.store.get_storage_usage()
        assert "total_files" in usage
        assert "total_size_mb" in usage
        assert "base_path" in usage


# ====================================================================
#  verification / verifier
# ====================================================================

from data_center.verification.verifier import DataVerifier, QualityReport, CrossValidationResult


class TestDataVerifier:
    """数据验证器测试"""

    def setup_method(self):
        from data_center.core.data_source import DataSourceManager
        self.source_mgr = DataSourceManager()
        self.verifier = DataVerifier(self.source_mgr)

    def test_quality_report_empty_data(self):
        data = KlineData("M", "1d", [], [], [], [], [], [], "test")
        report = self.verifier.check_quality(data)
        assert report.score == 0
        assert report.total_bars == 0

    def test_quality_report_good_data(self):
        dates = pd.date_range("2024-01-01", periods=20, freq="D")
        # 纯递增的价格，没有异常
        data = KlineData(
            symbol="M", interval="1d",
            open=[4000 + i for i in range(20)],
            high=[4010 + i for i in range(20)],
            low=[3990 + i for i in range(20)],
            close=[4005 + i for i in range(20)],
            volume=[1000 + i * 10 for i in range(20)],
            timestamps=dates.tolist(), source="test",
        )
        report = self.verifier.check_quality(data)
        assert report.score > 80
        assert report.total_bars == 20

    def test_quality_report_price_anomaly(self):
        """价格跳变应降低分数"""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        close = [100, 101, 102, 150, 103, 104, 105, 106, 107, 108]  # 第4天跳变
        data = KlineData(
            symbol="M", interval="1d",
            open=close, high=[c+1 for c in close],
            low=[c-1 for c in close], close=close,
            volume=[1000]*10, timestamps=dates.tolist(), source="test",
        )
        report = self.verifier.check_quality(data)
        # 价格跳变 >10% 应检测到
        assert report.price_anomaly_count >= 1

    def test_cross_validate_single_source(self):
        """单数据源时返回一致"""
        result = self.verifier.cross_validate("M")
        assert isinstance(result, CrossValidationResult)
        # 没有注册的数据源，应该只有 0 或 1 个源
        assert len(result.sources_available) <= 1

    def test_cross_validate_result_structure(self):
        result = CrossValidationResult(
            symbol="M", interval="1d",
            sources_available=["test1", "test2"],
            correlation=0.98, price_deviation_pct=1.2,
            volume_deviation_pct=0.5, is_consistent=True,
            details=["All good"],
        )
        assert result.is_consistent
        assert result.correlation == 0.98
        assert len(result.details) == 1


class TestQualityReport:
    """质量报告模型测试"""

    def test_create(self):
        report = QualityReport(
            symbol="M", source="test",
            score=95.0, total_bars=100, missing_bars=0,
            anomaly_count=0, gap_count=0, max_gap_days=0,
            price_anomaly_count=0, volume_anomaly_count=0,
            details=["数据完整"],
        )
        assert report.score == 95.0
        assert report.symbol == "M"
        assert "数据完整" in report.details
        assert report.checked_at is not None

    def test_low_score(self):
        report = QualityReport(
            symbol="M", source="test",
            score=30.0, total_bars=100, missing_bars=20,
            anomaly_count=5, gap_count=3, max_gap_days=7,
            price_anomaly_count=3, volume_anomaly_count=2,
            details=["大量缺失"],
        )
        assert report.score == 30.0


# ====================================================================
#  数据源获取器测试 (Mock 模式 - 不依赖外部连接)
# ====================================================================

class TestFetcherImports:
    """验证所有获取器模块可导入"""

    def test_import_akshare(self):
        from data_center.fetchers.akshare_fetcher import AKShareFetcher
        assert AKShareFetcher.name == "akshare"

    def test_import_tdx(self):
        from data_center.fetchers.tdx_fetcher import TDXFetcher
        assert TDXFetcher.name == "tdx"

    def test_import_yfinance(self):
        from data_center.fetchers.yfinance_fetcher import YFinanceFetcher
        assert YFinanceFetcher.name == "yfinance"

    def test_import_ctp(self):
        from data_center.fetchers.ctp_fetcher import CTPFetcher
        f = CTPFetcher()
        df = f.ticks_to_bars(pd.DataFrame(), 60)
        assert df.empty

    def test_import_alpha_vantage(self):
        from data_center.fetchers.alpha_vantage_fetcher import AlphaVantageFetcher
        assert AlphaVantageFetcher.name == "alpha_vantage"

    def test_import_eia_cftc(self):
        from data_center.fetchers.eia_cftc_fetcher import EIAFetcher, CFTCFetcher
        assert EIAFetcher.name == "eia"
        assert CFTCFetcher.name == "cftc"

    def test_import_fmp(self):
        from data_center.fetchers.fmp_fetcher import FMPFetcher
        assert FMPFetcher.name == "fmp"

    def test_import_fred(self):
        from data_center.fetchers.fred_fetcher import FREDFetcher
        assert FREDFetcher.name == "fred"

    def test_import_tiingo(self):
        from data_center.fetchers.tiingo_fetcher import TiingoFetcher
        assert TiingoFetcher.name == "tiingo"

    def test_import_options(self):
        from data_center.fetchers.options_fetcher import OptionsFetcher
        assert OptionsFetcher.name == "options"

    def test_import_unified(self):
        from data_center.fetchers.unified_fetcher import UnifiedFetcher
        assert UnifiedFetcher.name == "unified"


class TestCTPFetcher:
    """CTP Tick→Bar 转换测试"""

    def test_ticks_to_bars_empty(self):
        from data_center.fetchers.ctp_fetcher import CTPFetcher
        df = CTPFetcher.ticks_to_bars(pd.DataFrame(), 60)
        assert df.empty

    def test_ticks_to_bars_basic(self):
        from data_center.fetchers.ctp_fetcher import CTPFetcher
        ticks = pd.DataFrame({
            "datetime": pd.date_range("2024-01-01 09:30:00", periods=10, freq="10s"),
            "last_price": [100 + i * 0.5 for i in range(10)],
            "volume": [10] * 10,
        })
        bars = CTPFetcher.ticks_to_bars(ticks, bar_seconds=30)
        assert not bars.empty
        assert "open" in bars.columns
        assert "high" in bars.columns
        assert "low" in bars.columns
        assert "close" in bars.columns
        assert "volume" in bars.columns

    def test_ticks_to_bars_ohlc_logic(self):
        from data_center.fetchers.ctp_fetcher import CTPFetcher
        ticks = pd.DataFrame({
            "datetime": pd.date_range("2024-01-01 09:30:00", periods=6, freq="10s"),
            "last_price": [100, 102, 101, 103, 99, 101],
            "volume": [10, 15, 8, 12, 20, 5],
        })
        bars = CTPFetcher.ticks_to_bars(ticks, bar_seconds=30)
        # 验证输出结构
        assert not bars.empty
        assert "open" in bars.columns
        assert "high" in bars.columns
        assert "low" in bars.columns
        assert "close" in bars.columns
        assert "volume" in bars.columns
        # open 应为 bar 内的第一个 tick price
        assert bars["open"].iloc[0] > 0
        # 总成交量应等于所有 tick 成交量之和
        assert bars["volume"].sum() == 10 + 15 + 8 + 12 + 20 + 5


# ====================================================================
#  Data Center API 路由测试
# ====================================================================

class TestDataCenterAPIRoutes:
    """验证 API 路由注册"""

    def test_router_loaded(self):
        from data_center.api import router
        assert router is not None
        assert len(router.routes) >= 15  # 至少有15+路由

    def test_router_has_expected_endpoints(self):
        from data_center.api import router
        paths = [r.path for r in router.routes]
        assert "/api/v1/data-center/sources" in paths
        assert "/api/v1/data-center/sources/health" in paths
        assert "/api/v1/data-center/contracts/{symbol}" in paths
        assert "/api/v1/data-center/contracts/{symbol}/main" in paths
        assert "/api/v1/data-center/exchanges" in paths
        assert "/api/v1/data-center/download/history" in paths
        assert "/api/v1/data-center/storage" in paths
        assert "/api/v1/data-center/sync/status" in paths
