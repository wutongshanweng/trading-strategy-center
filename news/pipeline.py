"""新闻管道: 采集 → 品种标签 → 情绪分析 → JSON 缓存。

缓存到 data/news_cache.json, 进程重启保留。后台线程定时刷新。
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from loguru import logger

from core.config.watchlist import NEWS_KEYWORD_TAGS
from news.fetchers import CLSNewsFetcher
from news.sentiment import NewsSentimentAnalyzer

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_CACHE_FILE = _DATA_DIR / "news_cache.json"
_MAX_CACHE = 200


def _tag_products(text: str) -> List[str]:
    """按关键词给新闻打品种标签 (去重保序)。"""
    tags: List[str] = []
    for kw, prods in NEWS_KEYWORD_TAGS.items():
        if kw in text:
            for p in prods:
                if p not in tags:
                    tags.append(p)
    return tags


class NewsPipeline:
    """新闻采集 + 加工 + 缓存。"""

    def __init__(self):
        self._fetcher = CLSNewsFetcher()
        self._sentiment = NewsSentimentAnalyzer()
        self._lock = threading.Lock()

    def _enrich(self, raw: List[Dict]) -> List[Dict]:
        out: List[Dict] = []
        for n in raw:
            text = f"{n.get('title','')} {n.get('content','')}"
            senti = self._sentiment.analyze(text)
            out.append({
                "title": n.get("title", ""),
                "content": n.get("content", ""),
                "timestamp": n.get("timestamp", ""),
                "source": n.get("source", ""),
                "products": _tag_products(text),
                "sentiment": senti["sentiment"],
                "label": senti["label"],
                "sentiment_score": senti["score"],
            })
        return out

    def refresh(self, limit: int = 80) -> List[Dict]:
        """抓取并加工最新新闻, 写入缓存。返回加工后的列表。"""
        raw = self._fetcher.fetch(limit=limit)
        enriched = self._enrich(raw)
        with self._lock:
            _DATA_DIR.mkdir(parents=True, exist_ok=True)
            payload = {"updated_at": datetime.now().isoformat(),
                       "items": enriched[:_MAX_CACHE]}
            _CACHE_FILE.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"[news] cache refreshed: {len(enriched)} items")
        return enriched

    def get_cached(self, limit: int = 80, product: str | None = None) -> Dict:
        """读缓存; 缓存不存在则触发一次刷新。"""
        if not _CACHE_FILE.exists():
            self.refresh()
        try:
            payload = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            payload = {"updated_at": None, "items": []}
        items = payload.get("items", [])
        if product:
            items = [n for n in items if product.upper() in n.get("products", [])]
        return {"updated_at": payload.get("updated_at"),
                "count": len(items[:limit]), "items": items[:limit]}


# 模块级单例
_pipeline: NewsPipeline | None = None


def get_pipeline() -> NewsPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = NewsPipeline()
    return _pipeline
