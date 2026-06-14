"""Abstract base class for all LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProviderResponse:
    """Unified response from any provider."""
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)  # prompt_tokens, completion_tokens
    raw: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:
        if self.error:
            return f"ProviderResponse(error={self.error!r})"
        return f"ProviderResponse(model={self.model!r}, content={self.content[:60]!r}...)"


class BaseProvider(ABC):
    """Abstract base for all LLM providers.

    Each provider implements `chat()` and `complete()` using its own API protocol.
    """

    provider_name: str = "base"

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> ProviderResponse:
        """Send a chat completion request.

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": "..."}.
            temperature: Sampling temperature.
            max_tokens: Max tokens in response.
        """
        ...

    def complete(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """Simple completion: send prompt, return text response."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = self.chat(messages, **kwargs)
        if not resp.ok:
            return f"[Error] {resp.error}"
        return resp.content

    def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """Stream response. Override in subclass if supported."""
        resp = self.chat(messages, stream=True, **kwargs)
        yield resp.content if resp.ok else f"[Error] {resp.error}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} provider={self.provider_name}>"
