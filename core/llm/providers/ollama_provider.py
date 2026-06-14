"""Ollama provider — local models via Ollama API."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import requests

from .base import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Provider using Ollama's API for local models.

    API docs: https://github.com/ollama/ollama/blob/main/docs/api.md
    """

    provider_name = "ollama"

    def __init__(
        self,
        api_base: str = "http://localhost:11434",
        model: str = "llama3",
        timeout: int = 120,
    ):
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.timeout = timeout

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> ProviderResponse:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            resp = requests.post(
                f"{self.api_base}/api/chat",
                json=payload,
                timeout=kwargs.get("timeout", self.timeout),
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            return ProviderResponse(
                content=content,
                model=data.get("model", self.model),
                provider=self.provider_name,
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                },
                raw=data,
            )
        except Exception as e:
            logger.error("Ollama request failed: %s", e)
            return ProviderResponse(content="", model=self.model, provider=self.provider_name, error=str(e))

    def stream_chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 4096, **kwargs):
        """Stream from Ollama."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        try:
            with requests.post(
                f"{self.api_base}/api/chat",
                json=payload,
                stream=True,
                timeout=kwargs.get("timeout", 120),
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line.decode("utf-8"))
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error("Ollama streaming failed: %s", e)
            yield f"\n[Error] {e}"
