"""Provider registry — manages multiple LLM providers from YAML config."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .base import BaseProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)

# Provider type → class mapping
_PROVIDER_CLASSES: Dict[str, type] = {
    "openai": OpenAIProvider,
    "deepseek": OpenAIProvider,      # DeepSeek uses OpenAI-compatible API
    "groq": OpenAIProvider,          # Groq uses OpenAI-compatible API
    "together": OpenAIProvider,      # Together uses OpenAI-compatible API
    "moonshot": OpenAIProvider,      # Moonshot uses OpenAI-compatible API
    "qwen": OpenAIProvider,          # Qwen/DashScope uses OpenAI-compatible API
    "zhipu": OpenAIProvider,         # GLM uses OpenAI-compatible API
    "openrouter": OpenAIProvider,    # OpenRouter uses OpenAI-compatible API
    "anthropic": AnthropicProvider,
    "claude": AnthropicProvider,
    "ollama": OllamaProvider,
}

# Default base URLs for known providers
_DEFAULT_BASES: Dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com",
    "groq": "https://api.groq.com/openai/v1",
    "together": "https://api.together.xyz/v1",
    "moonshot": "https://api.moonshot.cn/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
    "openrouter": "https://openrouter.ai/api/v1",
    "anthropic": "https://api.anthropic.com",
    "ollama": "http://localhost:11434",
}


class ProviderRegistry:
    """Manages multiple LLM providers loaded from a YAML config file.

    Example YAML config (config/models.yaml):

    ```yaml
    active_provider: deepseek-chat

    providers:
      deepseek-chat:
        type: deepseek
        api_key: ${DEEPSEEK_API_KEY}
        model: deepseek-chat
        description: DeepSeek Chat - 性价比最高

      deepseek-reasoner:
        type: deepseek
        api_key: ${DEEPSEEK_API_KEY}
        model: deepseek-reasoner
        description: DeepSeek Reasoner - 推理能力强

      gpt-4o:
        type: openai
        api_key: ${OPENAI_API_KEY}
        model: gpt-4o
        description: GPT-4o - 最强综合能力

      claude-sonnet:
        type: anthropic
        api_key: ${ANTHROPIC_API_KEY}
        model: claude-sonnet-4-20250514
        description: Claude Sonnet - 代码能力强

      groq-llama:
        type: groq
        api_key: ${GROQ_API_KEY}
        model: llama-3.3-70b-versatile
        description: Groq Llama - 速度极快

      local-ollama:
        type: ollama
        model: llama3
        description: 本地 Ollama
    ```
    """

    def __init__(self, config_path: Optional[str] = None):
        self._providers: Dict[str, Dict[str, Any]] = {}
        self._instances: Dict[str, BaseProvider] = {}
        self._active: Optional[str] = None

        if config_path:
            self.load_config(config_path)

    def load_config(self, path: str) -> None:
        """Load provider definitions from YAML config."""
        config_path = Path(path)
        if not config_path.exists():
            logger.warning("Config file not found: %s", path)
            return

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        self._providers = config.get("providers", {})
        self._active = config.get("active_provider")

        # Resolve environment variables in api_key fields
        for name, prov_config in self._providers.items():
            api_key = prov_config.get("api_key", "")
            if isinstance(api_key, str) and api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                resolved = os.environ.get(env_var, "")
                prov_config["api_key"] = resolved
                if not resolved:
                    logger.debug("Env var %s not set for provider %s", env_var, name)

        logger.info("Loaded %d providers from %s (active: %s)", len(self._providers), path, self._active)

    def register(
        self,
        name: str,
        provider_type: str,
        api_key: str = "",
        api_base: str = "",
        model: str = "",
        **kwargs,
    ) -> None:
        """Register a provider programmatically (without YAML)."""
        self._providers[name] = {
            "type": provider_type,
            "api_key": api_key,
            "api_base": api_base,
            "model": model,
            **kwargs,
        }

    def _build_provider(self, name: str) -> BaseProvider:
        """Instantiate a provider from its config."""
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' not registered. Available: {list(self._providers.keys())}")

        config = self._providers[name]
        provider_type = config.get("type", "openai")
        api_key = config.get("api_key", "")
        api_base = config.get("api_base", _DEFAULT_BASES.get(provider_type, ""))
        model = config.get("model", "")
        timeout = config.get("timeout", 60)

        cls = _PROVIDER_CLASSES.get(provider_type)
        if cls is None:
            raise ValueError(f"Unknown provider type: {provider_type}. Supported: {list(_PROVIDER_CLASSES.keys())}")

        # Build kwargs based on provider type
        if provider_type == "ollama":
            return cls(api_base=api_base, model=model, timeout=timeout)
        else:
            return cls(api_key=api_key, api_base=api_base, model=model, timeout=timeout)

    def get(self, name: Optional[str] = None) -> BaseProvider:
        """Get a provider instance by name. Uses active_provider if name is None."""
        name = name or self._active
        if name is None:
            raise ValueError("No provider name specified and no active_provider set in config")

        if name not in self._instances:
            self._instances[name] = self._build_provider(name)

        return self._instances[name]

    def set_active(self, name: str) -> None:
        """Set the active (default) provider."""
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' not registered")
        self._active = name
        logger.info("Active provider set to: %s", name)

    @property
    def active_provider(self) -> Optional[str]:
        return self._active

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all registered providers with their configs."""
        result = []
        for name, config in self._providers.items():
            result.append({
                "name": name,
                "type": config.get("type", "unknown"),
                "model": config.get("model", ""),
                "description": config.get("description", ""),
                "active": name == self._active,
            })
        return result

    def list_available(self) -> List[str]:
        """List provider names that have API keys configured."""
        available = []
        for name, config in self._providers.items():
            api_key = config.get("api_key", "")
            # Ollama doesn't need an API key
            if config.get("type") == "ollama" or api_key:
                available.append(name)
        return available
