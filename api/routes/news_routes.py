"""News Aggregator — AI新闻聚合与情感评分 (基于 NewsRader)。

集成路径: D:/完整项目/20260623/NewsRader-main
"""

from __future__ import annotations

import feedparser
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/news", tags=["news"])


# ---- 数据模型 ----

class NewsItem(BaseModel):
    id: str
    source: str
    title: str
    summary: str
    url: str
    published_at: datetime
    sentiment_score: float  # 0-10, AI 评分
    sentiment_label: str    # positive / neutral / negative
    tags: List[str] = []


class NewsScoreRequest(BaseModel):
    text: str
    title: Optional[str] = None


class RSSSourceRequest(BaseModel):
    url: str
    name: str = ""


# ---- 内存存储 (生产环境应替换为 DB) ----

_news_store: Dict[str, NewsItem] = {}
_rss_sources: Dict[str, str] = {}  # name -> url


# ---- 默认财经RSS源 ----

DEFAULT_RSS_SOURCES = {
    "36Kr": "https://36kr.com/feed",
    "虎嗅": "https://www.huxiu.com/rss/0.xml",
    "少数派": "https://sspai.com/feed",
    "IT之家": "https://www.ithome.com/rss/",
    "财联社": "https://www.cls.cn/telegraph",
    "极客公园": "https://www.geekpark.net/rss",
}

# 初始化时订阅默认源
for name, url in DEFAULT_RSS_SOURCES.items():
    _rss_sources[name] = url


# ---- 简化情感评分 (生产环境应调用 LLM) ----

def _simple_sentiment(text: str) -> tuple[float, str]:
    """基于关键词的简化情感评分。生产环境应调用 LLM API。"""
    pos = sum(1 for w in ["涨", "突破", "利好", "增长", "盈利", "超预期", "买入", "看多", "牛市"] if w in text)
    neg = sum(1 for w in ["跌", "亏损", "暴雷", "利空", "减持", "卖出", "看空", "熊市", "风险", "违约"] if w in text)
    score = 5.0 + (pos - neg) * 0.5
    score = max(0.0, min(10.0, score))
    label = "positive" if score > 6 else "negative" if score < 4 else "neutral"
    return round(score, 2), label


def _gen_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


# ---- API 端点 ----

@router.get("/", response_model=List[NewsItem])
async def list_news(limit: int = 50, source: Optional[str] = None):
    """获取新闻列表，支持按来源过滤。"""
    items = list(_news_store.values())
    if source:
        items = [i for i in items if i.source == source]
    items.sort(key=lambda x: x.published_at, reverse=True)
    return items[:limit]


@router.post("/score")
async def score_news(req: NewsScoreRequest):
    """对文本进行情感评分。"""
    text = f"{req.title or ''} {req.text}"
    score, label = _simple_sentiment(text)
    return {"sentiment_score": score, "sentiment_label": label, "text_hash": _gen_id(text)}


@router.post("/rss/subscribe")
async def rss_subscribe(req: RSSSourceRequest):
    """订阅 RSS 源。"""
    _rss_sources[req.name or req.url] = req.url
    return {"subscribed": req.name or req.url, "total_sources": len(_rss_sources)}


@router.get("/rss/sources")
async def rss_sources():
    """列出所有已订阅 RSS 源。"""
    return {"sources": [{"name": k, "url": v} for k, v in _rss_sources.items()]}


@router.post("/rss/fetch")
async def rss_fetch(name: Optional[str] = None):
    """立即抓取 RSS 内容。"""
    results = []
    targets = [(name, _rss_sources[name])] if name and name in _rss_sources else _rss_sources.items()
    for src_name, url in targets:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                text = f"{entry.get('title', '')} {entry.get('summary', '')}"
                nid = _gen_id(text)
                if nid in _news_store:
                    continue
                score, label = _simple_sentiment(text)
                item = NewsItem(
                    id=nid,
                    source=src_name,
                    title=entry.get("title", ""),
                    summary=entry.get("summary", "")[:500],
                    url=entry.get("link", ""),
                    published_at=datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    if hasattr(entry, "published_parsed") and entry.published_parsed
                    else datetime.now(),
                    sentiment_score=score,
                    sentiment_label=label,
                )
                _news_store[nid] = item
                results.append(item)
        except Exception as e:
            results.append({"source": src_name, "error": str(e)})
    return {"fetched": len([r for r in results if hasattr(r, "id")]), "results": results}


@router.delete("/{news_id}")
async def delete_news(news_id: str):
    """删除单条新闻。"""
    if news_id in _news_store:
        del _news_store[news_id]
        return {"deleted": news_id}
    raise HTTPException(status_code=404, detail="News not found")


@router.get("/stats")
async def news_stats():
    """新闻统计概览。"""
    items = list(_news_store.values())
    if not items:
        return {"total": 0, "by_source": {}, "avg_sentiment": 5.0}
    by_source: Dict[str, int] = {}
    for it in items:
        by_source[it.source] = by_source.get(it.source, 0) + 1
    avg = sum(it.sentiment_score for it in items) / len(items)
    return {"total": len(items), "by_source": by_source, "avg_sentiment": round(avg, 2)}


@router.post("/bootstrap")
async def bootstrap_news():
    """启动时自动抓取所有默认RSS源。"""
    results = []
    for src_name, url in _rss_sources.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                text = f"{entry.get('title', '')} {entry.get('summary', '')}"
                nid = _gen_id(text)
                if nid in _news_store:
                    continue
                score, label = _simple_sentiment(text)
                item = NewsItem(
                    id=nid,
                    source=src_name,
                    title=entry.get("title", ""),
                    summary=entry.get("summary", "")[:500] if entry.get("summary") else "",
                    url=entry.get("link", ""),
                    published_at=datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    if hasattr(entry, "published_parsed") and entry.published_parsed
                    else datetime.now(),
                    sentiment_score=score,
                    sentiment_label=label,
                )
                _news_store[nid] = item
                results.append(item)
        except Exception:
            pass
    return {"bootstrapped": len(results), "total_stored": len(_news_store)}
