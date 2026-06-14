"""Generic LLMClient — multi-provider LLM client with auto-discovery."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .providers.base import BaseProvider, ProviderResponse
from .providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)

# Default config path
_DEFAULT_CONFIG = Path(__file__).parent.parent.parent / "config" / "models.yaml"

# Singleton registry
_registry: Optional[ProviderRegistry] = None


def get_registry(config_path: Optional[str] = None) -> ProviderRegistry:
    """Get or initialize the global provider registry."""
    global _registry
    if _registry is None:
        path = config_path or str(_DEFAULT_CONFIG)
        _registry = ProviderRegistry(path)
    return _registry


def get_provider(name: Optional[str] = None) -> BaseProvider:
    """Get a provider instance by name (uses active_provider if None)."""
    return get_registry().get(name)


def get_active_provider() -> BaseProvider:
    """Get the currently active provider."""
    return get_registry().get()


def switch_provider(name: str) -> BaseProvider:
    """Switch active provider and return it."""
    registry = get_registry()
    registry.set_active(name)
    return registry.get(name)


class LLMClient:
    """Generic multi-provider LLM client.

    Usage:
        # Simple — uses active provider from models.yaml
        client = LLMClient()
        response = client.complete("分析一下铜的走势")

        # Specific provider
        client = LLMClient(provider="gpt-4o")
        response = client.complete("分析一下铜的走势")

        # Compare multiple providers
        results = client.compare(
            "什么是均值回归策略？",
            providers=["deepseek-chat", "gpt-4o", "claude-sonnet"]
        )
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        config_path: Optional[str] = None,
    ):
        self.registry = get_registry(config_path)
        self.provider_name = provider
        self._provider: Optional[BaseProvider] = None

    @property
    def provider(self) -> BaseProvider:
        """Lazy-load the provider instance."""
        if self._provider is None:
            self._provider = self.registry.get(self.provider_name)
        return self._provider

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        provider: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Send chat request, optionally using a specific provider."""
        p = self.registry.get(provider) if provider else self.provider
        return p.chat(messages, temperature=temperature, max_tokens=max_tokens, **kwargs)

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Simple completion."""
        p = self.registry.get(provider) if provider else self.provider
        return p.complete(prompt, system=system, **kwargs)

    def compare(
        self,
        prompt: str,
        providers: Optional[List[str]] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, ProviderResponse]:
        """Compare responses from multiple providers.

        Args:
            prompt: The prompt to send.
            providers: List of provider names to compare. Uses all available if None.
            system: Optional system prompt.
            temperature: Sampling temperature.

        Returns:
            Dict mapping provider name → ProviderResponse.
        """
        if providers is None:
            providers = self.registry.list_available()

        results: Dict[str, ProviderResponse] = {}
        for name in providers:
            try:
                p = self.registry.get(name)
                resp = p.chat(
                    [{"role": "user", "content": prompt}] if not system
                    else [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                    temperature=temperature,
                )
                results[name] = resp
            except Exception as e:
                results[name] = ProviderResponse(
                    content="", model="", provider=name, error=str(e)
                )
        return results

    def stream(self, prompt: str, provider: Optional[str] = None, system: Optional[str] = None, **kwargs):
        """Stream response tokens."""
        p = self.registry.get(provider) if provider else self.provider
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        yield from p.stream_chat(messages, **kwargs)

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all configured providers."""
        return self.registry.list_providers()

    def switch(self, name: str) -> None:
        """Switch to a different provider."""
        self._provider = None
        self.provider_name = name
        self.registry.set_active(name)
