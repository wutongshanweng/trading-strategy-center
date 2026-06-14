"""OpenAI-compatible provider — works for OpenAI, DeepSeek, Groq, Together, Moonshot, etc."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import requests

from .base import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """Provider using OpenAI-compatible /chat/completions API.

    Works with: OpenAI, DeepSeek, Groq, Together, Moonshot, Qwen, Zhipu, etc.
    All of these expose the same chat/completions endpoint format.
    """

    provider_name = "openai"

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-4",
        timeout: int = 60,
    ):
        self.api_key = api_key
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
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            resp = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=kwargs.get("timeout", self.timeout),
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return ProviderResponse(
                content=choice["message"]["content"],
                model=data.get("model", self.model),
                provider=self.provider_name,
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                },
                raw=data,
            )
        except Exception as e:
            logger.error("OpenAI-provider request failed: %s", e)
            return ProviderResponse(content="", model=self.model, provider=self.provider_name, error=str(e))

    def stream_chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 4096, **kwargs):
        """Stream tokens from OpenAI-compatible endpoint."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        try:
            with requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=kwargs.get("timeout", 120),
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    line_str = line.decode("utf-8")
                    if not line_str.startswith("data: "):
                        continue
                    data_str = line_str[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
        except Exception as e:
            logger.error("Streaming failed: %s", e)
            yield f"\n[Error] {e}"
