"""Anthropic Claude provider — uses Anthropic Messages API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

from .base import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """Provider using Anthropic's Messages API (Claude models).

    API docs: https://docs.anthropic.com/en/api/messages
    """

    provider_name = "anthropic"

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.anthropic.com",
        model: str = "claude-sonnet-4-20250514",
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
        """Send a chat request using Anthropic Messages API format.

        Note: Anthropic requires a `system` message as a top-level parameter,
        not inside the messages array.
        """
        # Extract system message (Anthropic puts it as top-level param)
        system_text = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                chat_messages.append({"role": msg["role"], "content": msg["content"]})

        if not chat_messages:
            return ProviderResponse(
                content="", model=self.model, provider=self.provider_name,
                error="No user messages provided"
            )

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_text:
            payload["system"] = system_text

        try:
            resp = requests.post(
                f"{self.api_base}/v1/messages",
                headers=headers,
                json=payload,
                timeout=kwargs.get("timeout", self.timeout),
            )
            resp.raise_for_status()
            data = resp.json()

            # Extract text content from Anthropic response format
            content_text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content_text += block["text"]

            usage = data.get("usage", {})
            return ProviderResponse(
                content=content_text,
                model=data.get("model", self.model),
                provider=self.provider_name,
                usage={
                    "prompt_tokens": usage.get("input_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0),
                },
                raw=data,
            )
        except Exception as e:
            logger.error("Anthropic request failed: %s", e)
            return ProviderResponse(content="", model=self.model, provider=self.provider_name, error=str(e))

    def complete(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """Simple completion with Anthropic."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = self.chat(messages, **kwargs)
        return resp.content if resp.ok else f"[Error] {resp.error}"
