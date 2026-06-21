"""新闻宏观仪表盘 — 新增模块单测 (纯逻辑, 不触网/不触库)。"""

from news.sentiment import NewsSentimentAnalyzer
from news.calendar import MacroCalendar
from news.pipeline import _tag_products
from core.config.watchlist import (linkage_for_product, WATCHLIST_PRODUCTS,
                                   MACRO_PRODUCT_LINKAGE, DEFAULT_MAIN_CONTRACT)


class TestSentiment:
    def setup_method(self):
        self.s = NewsSentimentAnalyzer()

    def test_bullish(self):
        r = self.s.analyze("螺纹钢突破前高, 需求旺盛超预期")
        assert r["sentiment"] == "bullish"
        assert r["label"] == "🟢"
        assert r["score"] > 0

    def test_bearish(self):
        r = self.s.analyze("铁矿石大跌, 需求疲软累库")
        assert r["sentiment"] == "bearish"
        assert r["label"] == "🔴"
        assert r["score"] < 0

    def test_neutral_no_keywords(self):
        r = self.s.analyze("今日开盘价格平稳运行")
        assert r["sentiment"] == "neutral"
        assert r["confidence"] == 0.0

    def test_empty(self):
        r = self.s.analyze("")
        assert r["score"] == 0.0
        assert r["sentiment"] == "neutral"

    def test_mixed_more_positive(self):
        r = self.s.analyze("虽有回落但整体大涨突破上行")
        assert r["score"] > 0


class TestCalendar:
    def test_upcoming_returns_sorted(self):
        evs = MacroCalendar().upcoming(30)
        assert isinstance(evs, list)
        dates = [e["date"] for e in evs]
        assert dates == sorted(dates)

    def test_event_fields(self):
        evs = MacroCalendar().upcoming(40)
        for e in evs:
            assert {"date", "country", "event", "importance", "affects"} <= set(e)

    def test_window_bounds(self):
        evs = MacroCalendar().upcoming(7)
        evs_long = MacroCalendar().upcoming(60)
        assert len(evs) <= len(evs_long)


class TestProductTagging:
    def test_tag_rebar(self):
        assert "RB" in _tag_products("螺纹钢现货价格企稳回升")

    def test_tag_multi(self):
        tags = _tag_products("美联储暗示加息, 黄金白银承压")
        assert "AU" in tags and "AG" in tags

    def test_tag_none(self):
        assert _tag_products("某地天气晴好适合出行") == []

    def test_tag_dedup(self):
        tags = _tag_products("钢材螺纹钢双双走强")  # 多关键词命中 RB
        assert tags.count("RB") == 1


class TestWatchlistConfig:
    def test_watchlist_nonempty(self):
        assert len(WATCHLIST_PRODUCTS) >= 10

    def test_every_product_has_main_contract(self):
        for p in WATCHLIST_PRODUCTS:
            assert p in DEFAULT_MAIN_CONTRACT

    def test_linkage_reverse_lookup(self):
        link = linkage_for_product("RB")
        assert "PMI" in link
        assert link["PMI"] == MACRO_PRODUCT_LINKAGE["PMI"]["RB"]

    def test_linkage_unknown_product(self):
        assert linkage_for_product("ZZZ") == {}
