"""东财股吧舆情采集器 — 单测。

mock requests, 不真实联网。验证 JSONP 解析 + 超时容错。
"""

from unittest.mock import patch, MagicMock

from news.fetchers.eastmoney_guba import EastmoneyGubaFetcher


_FAKE_JSONP = 'jQuery({"data":{"list":[' \
    '{"title":"某公司发布利好公告","notice_date":"2026-06-20",' \
    '"codes":[{"stock_code":"601318","short_name":"中国平安"}],' \
    '"columns":[{"column_name":"重大事项"}],"art_code":"AN123"}]}})'


class TestEastmoneyGuba:
    def test_parse_jsonp(self):
        fetcher = EastmoneyGubaFetcher()
        with patch("news.fetchers.eastmoney_guba.requests.get") as mock_get:
            mock_get.return_value = MagicMock(text=_FAKE_JSONP)
            rows = fetcher.fetch_announcements("601318", page_size=10)
        assert len(rows) == 1
        assert rows[0]["title"] == "某公司发布利好公告"
        assert rows[0]["stock_name"] == "中国平安"
        assert rows[0]["source"] == "东财公告"

    def test_network_failure_returns_empty(self):
        fetcher = EastmoneyGubaFetcher()
        with patch("news.fetchers.eastmoney_guba.requests.get", side_effect=Exception("net down")):
            rows = fetcher.fetch_announcements("601318")
        assert rows == []

    def test_empty_list(self):
        fetcher = EastmoneyGubaFetcher()
        with patch("news.fetchers.eastmoney_guba.requests.get") as mock_get:
            mock_get.return_value = MagicMock(text='jQuery({"data":{"list":[]}})')
            rows = fetcher.fetch_announcements("000001")
        assert rows == []
