"""新闻宏观仪表盘 API — 新闻 + 宏观 + 日历 + 联动 + 展望。

设计为一个 /dashboard 聚合接口返回全部数据, 前端一次请求渲染整页。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
from loguru import logger

router = APIRouter(prefix="/api/v1/macro-news", tags=["macro-news"])


@router.get("/news")
async def get_news(limit: int = Query(80, le=200), product: Optional[str] = None):
    """新闻列表 (可按品种过滤)。"""
    from news.pipeline import get_pipeline
    return get_pipeline().get_cached(limit=limit, product=product)


@router.post("/news/refresh")
async def refresh_news(limit: int = Query(80, le=200)):
    """强制刷新新闻缓存（绕过30min间隔）。"""
    from news.pipeline import get_pipeline
    items = get_pipeline().refresh(limit=limit)
    return {"refreshed": len(items), "updated_at": datetime.now().isoformat()}


@router.get("/news/detail")
async def get_news_detail(url: str = Query(..., description="新闻文章链接")):
    """按需抓取新闻文章完整正文 (如《新闻联播》要闻N条的全部条目)。"""
    from news.fetchers.cls import fetch_article_content
    content = fetch_article_content(url)
    return {"url": url, "content": content,
            "available": content is not None}


@router.get("/macro")
async def get_macro_dashboard():
    """宏观指标看板。"""
    from macro.aggregator import MacroAggregator
    return MacroAggregator().dashboard()


@router.get("/guba")
async def get_guba(stock_code: str = Query("601318", description="股票代码 如 601318"),
                   limit: int = Query(20, le=50)):
    """东财个股公告/舆情 (含中文情绪标签)。"""
    from news.fetchers import EastmoneyGubaFetcher
    from news.sentiment import NewsSentimentAnalyzer
    rows = EastmoneyGubaFetcher().fetch_announcements(stock_code, page_size=limit)
    senti = NewsSentimentAnalyzer()
    for r in rows:
        s = senti.analyze(r.get("title", ""))
        r["sentiment"] = s["sentiment"]
        r["label"] = s["label"]
    return {"stock_code": stock_code, "count": len(rows), "items": rows}


@router.get("/calendar")
async def get_calendar(days: int = Query(14, le=60)):
    """宏观事件日历。"""
    from news.calendar import MacroCalendar
    return {"days": days, "events": MacroCalendar().upcoming(days)}


@router.get("/linkage")
async def get_linkage():
    """联动分析: 市态 + 新闻影响品种 + 关联度。"""
    from macro.regime_adapter import RegimeAdapter
    from news.pipeline import get_pipeline
    news = get_pipeline().get_cached(limit=80).get("items", [])
    return RegimeAdapter().linkage(news_items=news)


@router.get("/outlook")
async def get_outlook():
    """远期趋势展望。"""
    from macro.regime_adapter import RegimeAdapter
    return RegimeAdapter().outlook()


@router.get("/dashboard")
async def get_dashboard():
    """全量聚合: 新闻 + 宏观 + 日历 + 联动 + 展望。"""
    from macro.aggregator import MacroAggregator
    from macro.regime_adapter import RegimeAdapter
    from news.calendar import MacroCalendar
    from news.pipeline import get_pipeline

    out = {"news": {"items": [], "updated_at": None},
           "macro": {"indicators": []}, "calendar": {"events": []},
           "linkage": {}, "outlook": {"outlook": []}, "errors": []}
    try:
        news = get_pipeline().get_cached(limit=80)
        out["news"] = news
    except Exception as e:
        logger.warning(f"[dashboard] news failed: {e}")
        out["errors"].append(f"news: {e}")
    try:
        out["macro"] = MacroAggregator().dashboard()
    except Exception as e:
        logger.warning(f"[dashboard] macro failed: {e}")
        out["errors"].append(f"macro: {e}")
    try:
        out["calendar"] = {"events": MacroCalendar().upcoming(14)}
    except Exception as e:
        out["errors"].append(f"calendar: {e}")
    try:
        out["linkage"] = RegimeAdapter().linkage(news_items=out["news"].get("items", []))
    except Exception as e:
        logger.warning(f"[dashboard] linkage failed: {e}")
        out["errors"].append(f"linkage: {e}")
    try:
        out["outlook"] = RegimeAdapter().outlook()
    except Exception as e:
        out["errors"].append(f"outlook: {e}")
    return out
