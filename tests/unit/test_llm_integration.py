"""Tests for LLM Integration module — multi-provider support."""

from __future__ import annotations

import json
import pytest
from unittest.mock import patch, MagicMock

from core.llm.providers.base import BaseProvider, ProviderResponse
from core.llm.providers.openai_provider import OpenAIProvider
from core.llm.providers.anthropic_provider import AnthropicProvider
from core.llm.providers.ollama_provider import OllamaProvider
from core.llm.providers.registry import ProviderRegistry
from core.llm.llm_client import LLMClient, get_registry
from core.llm.comparator import ModelComparator, ComparisonResult


# ---------------------------------------------------------------------------
# ProviderResponse
# ---------------------------------------------------------------------------

class TestProviderResponse:
    def test_ok_when_no_error(self):
        r = ProviderResponse(content="hello", model="m", provider="p")
        assert r.ok is True

    def test_not_ok_when_error(self):
        r = ProviderResponse(content="", model="m", provider="p", error="fail")
        assert r.ok is False


# ---------------------------------------------------------------------------
# OpenAIProvider (covers DeepSeek, Groq, Together, etc.)
# ---------------------------------------------------------------------------

class TestOpenAIProvider:
    @patch("core.llm.providers.openai_provider.requests.post")
    def test_chat_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "model": "gpt-4o",
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        mock_post.return_value = mock_resp

        p = OpenAIProvider(api_key="sk-test", model="gpt-4o")
        resp = p.chat([{"role": "user", "content": "Hi"}])

        assert resp.ok
        assert resp.content == "Hello!"
        assert resp.provider == "openai"
        assert resp.usage["prompt_tokens"] == 10

    @patch("core.llm.providers.openai_provider.requests.post")
    def test_chat_error(self, mock_post):
        mock_post.side_effect = Exception("Connection refused")

        p = OpenAIProvider(api_key="sk-test", model="gpt-4o")
        resp = p.chat([{"role": "user", "content": "Hi"}])

        assert not resp.ok
        assert "Connection refused" in resp.error

    @patch("core.llm.providers.openai_provider.requests.post")
    def test_complete(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Result text"}}]
        }
        mock_post.return_value = mock_resp

        p = OpenAIProvider(api_key="sk-test", model="gpt-4o")
        result = p.complete("Analyze this", system="You are an analyst")
        assert result == "Result text"

    def test_deepseek_type_uses_openai_class(self):
        """DeepSeek/Groq/Together etc. are all OpenAIProvider."""
        from core.llm.providers.registry import _PROVIDER_CLASSES
        assert _PROVIDER_CLASSES["deepseek"] is OpenAIProvider
        assert _PROVIDER_CLASSES["groq"] is OpenAIProvider
        assert _PROVIDER_CLASSES["together"] is OpenAIProvider


# ---------------------------------------------------------------------------
# AnthropicProvider
# ---------------------------------------------------------------------------

class TestAnthropicProvider:
    @patch("core.llm.providers.anthropic_provider.requests.post")
    def test_chat_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "model": "claude-sonnet-4-20250514",
            "content": [{"type": "text", "text": "Claude says hi"}],
            "usage": {"input_tokens": 20, "output_tokens": 10},
        }
        mock_post.return_value = mock_resp

        p = AnthropicProvider(api_key="sk-ant-test", model="claude-sonnet-4-20250514")
        resp = p.chat([
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hi"},
        ])

        assert resp.ok
        assert resp.content == "Claude says hi"
        assert resp.provider == "anthropic"
        assert resp.usage["prompt_tokens"] == 20
        assert resp.usage["completion_tokens"] == 10

    @patch("core.llm.providers.anthropic_provider.requests.post")
    def test_chat_extracts_system(self, mock_post):
        """System message is extracted and sent as top-level param."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "content": [{"type": "text", "text": "OK"}],
        }
        mock_post.return_value = mock_resp

        p = AnthropicProvider(api_key="sk-ant-test")
        p.chat([
            {"role": "system", "content": "Be concise"},
            {"role": "user", "content": "Hi"},
        ])

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["system"] == "Be concise"

    @patch("core.llm.providers.anthropic_provider.requests.post")
    def test_chat_error(self, mock_post):
        mock_post.side_effect = Exception("Auth failed")

        p = AnthropicProvider(api_key="bad")
        resp = p.chat([{"role": "user", "content": "Hi"}])
        assert not resp.ok
        assert "Auth failed" in resp.error


# ---------------------------------------------------------------------------
# OllamaProvider
# ---------------------------------------------------------------------------

class TestOllamaProvider:
    @patch("core.llm.providers.ollama_provider.requests.post")
    def test_chat_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "model": "llama3",
            "message": {"content": "Local model response"},
            "prompt_eval_count": 10,
            "eval_count": 5,
        }
        mock_post.return_value = mock_resp

        p = OllamaProvider(model="llama3")
        resp = p.chat([{"role": "user", "content": "Hi"}])

        assert resp.ok
        assert resp.content == "Local model response"
        assert resp.provider == "ollama"


# ---------------------------------------------------------------------------
# ProviderRegistry
# ---------------------------------------------------------------------------

class TestProviderRegistry:
    def test_register_programmatic(self):
        reg = ProviderRegistry()
        reg.register("test-openai", "openai", api_key="sk-test", model="gpt-4o")
        providers = reg.list_providers()
        assert len(providers) == 1
        assert providers[0]["name"] == "test-openai"
        assert providers[0]["type"] == "openai"

    def test_get_provider(self):
        reg = ProviderRegistry()
        reg.register("test", "openai", api_key="sk-test", model="gpt-4o")
        p = reg.get("test")
        assert isinstance(p, OpenAIProvider)

    def test_set_active(self):
        reg = ProviderRegistry()
        reg.register("a", "openai", api_key="sk-a")
        reg.register("b", "anthropic", api_key="sk-b")
        reg.set_active("b")
        assert reg.active_provider == "b"

    def test_get_unknown_raises(self):
        reg = ProviderRegistry()
        with pytest.raises(KeyError):
            reg.get("nonexistent")

    def test_list_available(self):
        reg = ProviderRegistry()
        reg.register("has-key", "openai", api_key="sk-test")
        reg.register("no-key", "openai", api_key="")
        reg.register("ollama", "ollama")
        available = reg.list_available()
        assert "has-key" in available
        assert "ollama" in available
        assert "no-key" not in available

    def test_unknown_type_raises(self):
        reg = ProviderRegistry()
        reg.register("bad", "unknown_type", api_key="sk-test")
        with pytest.raises(ValueError, match="Unknown provider type"):
            reg.get("bad")

    @patch("core.llm.providers.registry.ProviderRegistry.load_config")
    def test_load_yaml(self, mock_load):
        """load_config is called when config_path is provided."""
        mock_load.return_value = None
        reg = ProviderRegistry(config_path="dummy.yaml")
        mock_load.assert_called_once_with("dummy.yaml")


# ---------------------------------------------------------------------------
# LLMClient
# ---------------------------------------------------------------------------

class TestLLMClient:
    @patch("core.llm.providers.openai_provider.requests.post")
    def test_complete(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Answer"}}]
        }
        mock_post.return_value = mock_resp

        client = LLMClient()
        # Register a provider for testing
        client.registry.register("test", "openai", api_key="sk-test", model="gpt-4o")
        client.switch("test")

        result = client.complete("What is VaR?")
        assert result == "Answer"

    @patch("core.llm.providers.openai_provider.requests.post")
    def test_compare(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Response from model"}}],
            "usage": {"completion_tokens": 10},
        }
        mock_post.return_value = mock_resp

        client = LLMClient()
        client.registry.register("model-a", "openai", api_key="sk-a")
        client.registry.register("model-b", "openai", api_key="sk-b")

        results = client.compare("Explain momentum", providers=["model-a", "model-b"])
        assert "model-a" in results
        assert "model-b" in results
        assert results["model-a"].ok
        assert results["model-b"].ok

    def test_switch(self):
        client = LLMClient()
        client.registry.register("a", "openai", api_key="sk-a")
        client.registry.register("b", "anthropic", api_key="sk-b")
        client.switch("b")
        assert client.provider_name == "b"


# ---------------------------------------------------------------------------
# ModelComparator / ComparisonResult
# ---------------------------------------------------------------------------

class TestComparisonResult:
    def test_summary(self):
        r = ComparisonResult(
            prompt="test prompt",
            results={
                "a": ProviderResponse(content="hello", model="m", provider="a", usage={"completion_tokens": 10}),
                "b": ProviderResponse(content="", model="m", provider="b", error="fail"),
            },
            timings={"a": 0.5, "b": 0.1},
        )
        s = r.summary()
        assert s["total_models"] == 2
        assert s["successful"] == 1
        assert s["failed"] == 1

    def test_to_markdown(self):
        r = ComparisonResult(
            prompt="test",
            results={
                "a": ProviderResponse(content="result", model="m", provider="a"),
            },
            timings={"a": 1.2},
        )
        md = r.to_markdown()
        assert "模型对比" in md
        assert "model-a" not in md  # name is "a"
        assert "✅" in md

    def test_best_by_tokens(self):
        r = ComparisonResult(
            prompt="test",
            results={
                "a": ProviderResponse(content="", model="m", provider="a", usage={"completion_tokens": 50}),
                "b": ProviderResponse(content="", model="m", provider="b", usage={"completion_tokens": 100}),
            },
        )
        assert r.best_by_tokens == "b"

    def test_successful_and_failed(self):
        r = ComparisonResult(
            prompt="test",
            results={
                "ok": ProviderResponse(content="hi", model="m", provider="ok"),
                "fail": ProviderResponse(content="", model="m", provider="fail", error="err"),
            },
        )
        assert len(r.successful) == 1
        assert len(r.failed) == 1


class TestModelComparator:
    @patch("core.llm.providers.openai_provider.requests.post")
    def test_compare(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {"completion_tokens": 5},
        }
        mock_post.return_value = mock_resp

        comp = ModelComparator()
        comp.client.registry.register("m1", "openai", api_key="sk-1")
        comp.client.registry.register("m2", "openai", api_key="sk-2")

        result = comp.compare("What is Sharpe ratio?", providers=["m1", "m2"])
        assert isinstance(result, ComparisonResult)
        assert len(result.results) == 2
        assert all(r.ok for r in result.results.values())


# ---------------------------------------------------------------------------
# Import test
# ---------------------------------------------------------------------------

class TestModuleImport:
    def test_import_all(self):
        from core.llm import (
            LLMClient, ModelComparator, ComparisonResult,
            BaseProvider, ProviderResponse,
            OpenAIProvider, AnthropicProvider, OllamaProvider,
            ProviderRegistry,
            get_provider, get_active_provider, switch_provider,
        )
        assert all(cls is not None for cls in [
            LLMClient, ModelComparator, ComparisonResult,
            BaseProvider, ProviderResponse,
            OpenAIProvider, AnthropicProvider, OllamaProvider,
            ProviderRegistry,
        ])

    def test_import_deepseek_compat(self):
        """Legacy DeepSeekClient still importable."""
        from core.llm import DeepSeekClient
        assert DeepSeekClient is not None
