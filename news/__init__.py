"""news — 财经新闻采集 / 中文情绪 / 宏观事件日历。"""

from news.calendar import MacroCalendar
from news.pipeline import NewsPipeline, get_pipeline
from news.sentiment import NewsSentimentAnalyzer

__all__ = ["MacroCalendar", "NewsPipeline", "get_pipeline", "NewsSentimentAnalyzer"]
