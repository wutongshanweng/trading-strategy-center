"""news.fetchers — 新闻数据源采集器。"""

from .cls import CLSNewsFetcher
from .eastmoney_guba import EastmoneyGubaFetcher

__all__ = ["CLSNewsFetcher", "EastmoneyGubaFetcher"]
