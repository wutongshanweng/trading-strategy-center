"""东方财富个股公告/股吧舆情采集器 (参考 ai_quant_trade, Apache-2.0)。

抓取个股公告新闻 (无需 key, requests + JSONP 解析)。
与 CLS/东财全球快讯互补 —— 这里是个股层面的公告/舆情。
全部容错 + 超时, 失败不抛异常。
"""

from __future__ import annotations

import concurrent.futures
import json
from datetime import datetime
from typing import Dict, List

import requests
from loguru import logger

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://data.eastmoney.com/",
}


class EastmoneyGubaFetcher:
    """东财个股公告采集器。"""

    def _fetch_announcements(self, stock_code: str, page_size: int) -> List[Dict]:
        url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
        params = {
            "cb": "jQuery", "sr": "-1", "page_size": page_size, "page_index": 1,
            "ann_type": "A", "client_source": "web", "stock_list": stock_code,
            "f_node": "0", "s_node": "0",
        }
        r = requests.get(url, params=params, headers=_HEADERS, timeout=10)
        text = r.text
        if text.startswith("jQuery"):
            text = text[text.index("(") + 1: text.rindex(")")]
        data = json.loads(text)
        items = data.get("data", {}).get("list", [])
        rows: List[Dict] = []
        for item in items:
            codes = item.get("codes", [{}])
            cols = item.get("columns", [{}])
            rows.append({
                "title": item.get("title", ""),
                "timestamp": item.get("notice_date", ""),
                "stock_code": codes[0].get("stock_code", "") if codes else "",
                "stock_name": codes[0].get("short_name", "") if codes else "",
                "ann_type": cols[0].get("column_name", "") if cols else "",
                "source": "东财公告",
            })
        return rows

    def fetch_announcements(self, stock_code: str = "601318",
                            page_size: int = 20, timeout: float = 12.0) -> List[Dict]:
        """抓取个股公告 (带超时容错)。"""
        ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            rows = ex.submit(self._fetch_announcements, stock_code, page_size).result(timeout=timeout)
            logger.info(f"[guba] fetched {len(rows)} announcements for {stock_code}")
            return rows
        except concurrent.futures.TimeoutError:
            logger.warning(f"[guba] {stock_code} timed out after {timeout}s")
            return []
        except Exception as e:
            logger.warning(f"[guba] {stock_code} failed: {type(e).__name__}: {e}")
            return []
        finally:
            ex.shutdown(wait=False)
