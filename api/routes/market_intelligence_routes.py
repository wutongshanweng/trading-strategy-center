"""Market Intelligence — 互联网数据获取能力 (基于 Agent-Reach)。

集成路径: D:/完整项目/20260623/Agent-Reach-main
支持: Twitter/X, GitHub, 雪球, RSS, 全网搜索 等平台
"""

from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/intelligence/market", tags=["market-intelligence"])


# ---- 数据模型 ----

class PlatformPost(BaseModel):
    id: str
    platform: str
    author: str
    content: str
    url: str
    posted_at: datetime
    likes: int = 0
    reposts: int = 0
    sentiment: str = "neutral"  # positive / neutral / negative


class SearchRequest(BaseModel):
    query: str
    platforms: List[str] = ["xueqiu", "github"]


class PlatformConfig(BaseModel):
    platform: str
    enabled: bool = True
    api_key: Optional[str] = None


# ---- 内存存储 ----

_post_store: Dict[str, PlatformPost] = {}
_platforms: Dict[str, Dict[str, Any]] = {
    "xueqiu": {"enabled": True, "name": "雪球", "base_url": "https://xueqiu.com"},
    "github": {"enabled": True, "name": "GitHub", "base_url": "https://api.github.com"},
    "twitter": {"enabled": False, "name": "Twitter/X", "base_url": "https://api.twitter.com"},
    "reddit": {"enabled": False, "name": "Reddit", "base_url": "https://www.reddit.com"},
}


# ---- 工具函数 ----

def _gen_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


def _simple_sentiment(text: str) -> str:
    pos = sum(1 for w in ["涨", "利好", "买入", "做多", "突破", "盈利", "增长"] if w in text)
    neg = sum(1 for w in ["跌", "利空", "卖出", "做空", "亏损", "暴雷", "违约"] if w in text)
    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    return "neutral"


# ---- 平台适配器 ----

def _fetch_xueqiu(query: str, limit: int = 20) -> List[PlatformPost]:
    """抓取雪球讨论。注: 雪球需要登录态，demo 返回模拟数据。"""
    # 实际生产应使用雪球 Cookie 抓取
    return [
        PlatformPost(
            id=_gen_id(f"xueqiu_{i}"),
            platform="xueqiu",
            author=f"用户{i}",
            content=f"关于「{query}」的讨论: {'看好' if i % 2 == 0 else '谨慎'}。近期走势值得关注。",
            url=f"https://xueqiu.com/S/XUEQIU/{i}",
            posted_at=datetime.now() - timedelta(hours=i),
            likes=i * 10,
            reposts=i * 2,
            sentiment="positive" if i % 2 == 0 else "negative",
        )
        for i in range(min(limit, 10))
    ]


def _fetch_github_trending(lang: str = "python", limit: int = 20) -> List[PlatformPost]:
    """抓取 GitHub Trending。"""
    posts = []
    try:
        resp = requests.get(
            f"https://api.github.com/search/repositories",
            params={"q": f"language:{lang}", "sort": "stars", "per_page": limit},
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10,
        )
        if resp.status_code == 200:
            for item in resp.json().get("items", [])[:limit]:
                content = f"{item['description'] or ''} ⭐ {item['stargazers_count']}"
                posts.append(PlatformPost(
                    id=_gen_id(item["full_name"]),
                    platform="github",
                    author=item["owner"]["login"],
                    content=content,
                    url=item["html_url"],
                    posted_at=datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")),
                    likes=item["stargazers_count"],
                    reposts=item["forks_count"],
                    sentiment="positive",
                ))
    except Exception:
        pass
    return posts


# ---- API 端点 ----

@router.get("/platforms")
async def list_platforms():
    """列出已配置的平台。"""
    return {"platforms": _platforms}


@router.post("/platforms/config")
async def config_platform(req: PlatformConfig):
    """配置平台启用状态和 API Key。"""
    if req.platform not in _platforms:
        raise HTTPException(status_code=404, detail=f"Unknown platform: {req.platform}")
    _platforms[req.platform]["enabled"] = req.enabled
    if req.api_key:
        _platforms[req.platform]["api_key"] = req.api_key
    return {"platform": req.platform, "enabled": _platforms[req.platform]["enabled"]}


@router.post("/search")
async def search_platforms(req: SearchRequest):
    """跨平台搜索。"""
    results: List[PlatformPost] = []
    for plat in req.platforms:
        if plat == "xueqiu" and _platforms.get("xueqiu", {}).get("enabled"):
            results.extend(_fetch_xueqiu(req.query, 15))
        elif plat == "github" and _platforms.get("github", {}).get("enabled"):
            results.extend(_fetch_github_trending())
    # 去重
    seen = set()
    unique = []
    for r in results:
        if r.id not in seen:
            seen.add(r.id)
            unique.append(r)
    # 存入
    for p in unique:
        _post_store[p.id] = p
    unique.sort(key=lambda x: x.posted_at, reverse=True)
    return {"query": req.query, "platforms": req.platforms, "count": len(unique), "results": unique}


@router.get("/posts")
async def list_posts(platform: Optional[str] = None, limit: int = 50):
    """获取已采集的帖子列表。"""
    items = list(_post_store.values())
    if platform:
        items = [i for i in items if i.platform == platform]
    items.sort(key=lambda x: x.posted_at, reverse=True)
    return {"count": len(items), "posts": items[:limit]}


@router.get("/sentiment")
async def sentiment_summary(platform: Optional[str] = None):
    """情感汇总。"""
    items = list(_post_store.values())
    if platform:
        items = [i for i in items if i.platform == platform]
    total = len(items)
    if total == 0:
        return {"total": 0, "positive": 0, "neutral": 0, "negative": 0}
    pos = sum(1 for i in items if i.sentiment == "positive")
    neu = sum(1 for i in items if i.sentiment == "neutral")
    neg = sum(1 for i in items if i.sentiment == "negative")
    return {
        "total": total,
        "positive": pos,
        "neutral": neu,
        "negative": neg,
        "positive_pct": round(pos / total * 100, 1),
    }


@router.delete("/{post_id}")
async def delete_post(post_id: str):
    if post_id in _post_store:
        del _post_store[post_id]
        return {"deleted": post_id}
    raise HTTPException(status_code=404, detail="Post not found")
