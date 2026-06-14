"""Unit tests for the data layer (core/data/)."""

import numpy as np
import pandas as pd
import pytest

from core.data.data_quality import DataQualityGuard, DataQualityReport
from core.data.cache_manager import CacheManager


class TestDataQualityGuard:
    """Test the 6 data quality checks."""

    @pytest.fixture
    def guard(self) -> DataQualityGuard:
        return DataQualityGuard()

    @pytest.fixture
    def good_df(self) -> pd.DataFrame:
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=100, freq="B")
        return pd.DataFrame({
            "open": np.random.randn(100) + 100,
            "high": np.random.randn(100) + 101,
            "low": np.random.randn(100) + 99,
            "close": np.random.randn(100) + 100,
            "volume": np.random.randint(1000, 10000, 100).astype(float),
        }, index=dates)

    def test_quality_pass_on_good_data(self, guard, good_df):
        report = guard.check(good_df)
        assert isinstance(report, DataQualityReport)
        assert report.passed is True
        assert report.score >= 0.5

    def test_schema_missing_column(self, guard, good_df):
        bad = good_df.drop(columns=["volume"])
        report = guard.check(bad)
        assert report.score < 1.0
        assert "Missing columns" in str(report.errors)

    def test_price_negative(self, guard, good_df):
        good_df.loc[good_df.index[0], "close"] = -9999
        report = guard.check(good_df)
        assert isinstance(report, DataQualityReport)

    def test_duplicate_index(self, guard, good_df):
        dup = pd.concat([good_df, good_df.iloc[[0]]])
        report = guard.check(dup)
        assert isinstance(report, DataQualityReport)

    def test_auto_repair_null_values(self, good_df):
        good_df.loc[good_df.index[5:8], "close"] = np.nan
        repaired = DataQualityGuard.auto_repair(good_df)
        assert repaired["close"].iloc[5:8].isna().sum() < 3

    def test_quality_report_properties(self):
        report = DataQualityReport("RB", "1d")
        report.checks = {"schema": True, "range": True}
        assert report.passed is True
        assert report.score == 1.0

    def test_quality_report_failure(self):
        report = DataQualityReport("RB", "1d")
        report.checks = {"schema": False, "range": True}
        report.errors.append("Missing columns")
        assert report.passed is False
        assert report.score == 0.5


class TestLRUCache:
    """Test the in-memory LRU cache."""

    @pytest.fixture
    def cache(self):
        from core.data.cache_manager import LRUCache
        return LRUCache(maxsize=5, ttl=60)

    def test_set_and_get(self, cache):
        df = pd.DataFrame({"a": [1, 2, 3]})
        cache.set("test_key", df)
        result = cache.get("test_key")
        assert result is not None
        pd.testing.assert_frame_equal(result, df)

    def test_miss_returns_none(self, cache):
        result = cache.get("nonexistent")
        assert result is None

    def test_clear(self, cache):
        cache.set("a", pd.DataFrame({"x": [1]}))
        cache.clear()
        assert cache.get("a") is None

    def test_lru_eviction(self, cache):
        for i in range(10):
            cache.set(f"key_{i}", pd.DataFrame({"v": [i]}))
        # Only last 5 should remain
        assert cache.size == 5
        assert cache.get("key_0") is None  # evicted
        assert cache.get("key_9") is not None  # kept

    def test_ttl_expiry(self, cache):
        import time
        cache.set("fast", pd.DataFrame({"x": [1]}), ttl=0.1)
        assert cache.get("fast") is not None
        time.sleep(0.15)
        assert cache.get("fast") is None


class TestCacheManager:
    """Test CacheManager (memory-only, no Redis)."""

    @pytest.fixture
    def cache(self):
        return CacheManager(redis_url=None)

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        df = pd.DataFrame({"a": [1, 2, 3]})
        await cache.set("test_key", df)
        result = await cache.get("test_key")
        assert result is not None
        pd.testing.assert_frame_equal(result, df)

    @pytest.mark.asyncio
    async def test_miss_returns_none(self, cache):
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        await cache.set("a", pd.DataFrame({"x": [1]}))
        await cache.clear()
        result = await cache.get("a")
        assert result is None

    def test_size_property(self, cache):
        info = cache.size
        assert "lru" in info
        assert "redis_connected" in info
        assert info["redis_connected"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
