"""Feishu (Lark) notification channel."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class FeishuChannel:
    """Send alerts via Feishu/Lark webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, title: str, content: str) -> bool:
        try:
            import requests
            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {"tag": "plain_text", "content": title}
                    },
                    "elements": [
                        {"tag": "div", "text": {"tag": "lark_md", "content": content}}
                    ],
                },
            }
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.warning("Feishu send failed: %s", e)
            return False
