"""LLM Integration: Multi-provider LLM support (OpenAI, Anthropic, DeepSeek, Ollama, etc.)."""

from .providers.base import BaseProvider, ProviderResponse
from .providers.registry import ProviderRegistry
from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.ollama_provider import OllamaProvider
from .llm_client import LLMClient, get_provider, get_active_provider, switch_provider
from .comparator import ModelComparator, ComparisonResult

# Legacy compatibility
from .deepseek_client import DeepSeekClient

__all__ = [
    # Core
    "LLMClient",
    "ModelComparator",
    "ComparisonResult",
    # Provider classes
    "BaseProvider",
    "ProviderResponse",
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "ProviderRegistry",
    # Helper functions
    "get_provider",
    "get_active_provider",
    "switch_provider",
    # Legacy
    "DeepSeekClient",
]
