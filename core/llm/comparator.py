"""Model comparator — run the same prompt across multiple models and compare results."""

from __future__ import annotations

import json
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .providers.base import ProviderResponse
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class ComparisonResult:
    """Result of comparing multiple models on the same prompt."""
    prompt: str
    results: Dict[str, ProviderResponse] = field(default_factory=dict)
    timings: Dict[str, float] = field(default_factory=dict)  # provider → seconds

    @property
    def successful(self) -> Dict[str, ProviderResponse]:
        return {k: v for k, v in self.results.items() if v.ok}

    @property
    def failed(self) -> Dict[str, ProviderResponse]:
        return {k: v for k, v in self.results.items() if not v.ok}

    @property
    def best_by_tokens(self) -> Optional[str]:
        """Provider that returned the most content tokens."""
        best, best_tokens = None, 0
        for name, resp in self.successful.items():
            tokens = resp.usage.get("completion_tokens", 0)
            if tokens > best_tokens:
                best, best_tokens = name, tokens
        return best

    def summary(self) -> Dict[str, Any]:
        """Generate a comparison summary."""
        return {
            "prompt": self.prompt[:100],
            "total_models": len(self.results),
            "successful": len(self.successful),
            "failed": len(self.failed),
            "timings": self.timings,
            "responses": {
                name: {
                    "model": resp.model,
                    "content_preview": resp.content[:200] + "..." if len(resp.content) > 200 else resp.content,
                    "tokens": resp.usage,
                    "time_seconds": self.timings.get(name, 0),
                    "error": resp.error,
                }
                for name, resp in self.results.items()
            },
        }

    def to_markdown(self) -> str:
        """Format comparison as a readable markdown table."""
        lines = [f"# 模型对比结果\n", f"**Prompt:** {self.prompt[:200]}\n"]
        lines.append("| 模型 | 状态 | Token数 | 耗时 | 响应预览 |")
        lines.append("|------|------|---------|------|----------|")
        for name, resp in self.results.items():
            status = "✅" if resp.ok else "❌"
            tokens = resp.usage.get("completion_tokens", "?")
            timing = f"{self.timings.get(name, 0):.2f}s"
            preview = resp.content[:80].replace("|", "\\|").replace("\n", " ") if resp.ok else resp.error[:80]
            lines.append(f"| {name} | {status} | {tokens} | {timing} | {preview} |")
        return "\n".join(lines)


class ModelComparator:
    """Compare multiple LLM models on the same prompts.

    Usage:
        comp = ModelComparator()
        result = comp.compare(
            "解释什么是Kelly准则，以及它在仓位管理中的应用",
            providers=["deepseek-chat", "gpt-4o", "claude-sonnet", "groq-llama"]
        )
        print(result.to_markdown())
    """

    def __init__(self, config_path: Optional[str] = None):
        self.client = LLMClient(config_path=config_path)

    def compare(
        self,
        prompt: str,
        providers: Optional[List[str]] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ) -> ComparisonResult:
        """Run the same prompt across multiple providers and compare."""
        if providers is None:
            providers = self.client.registry.list_available()

        result = ComparisonResult(prompt=prompt)

        for name in providers:
            start = time.time()
            try:
                resp = self.client.chat(
                    [{"role": "user", "content": prompt}] if not system
                    else [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                    temperature=temperature,
                    provider=name,
                )
                result.results[name] = resp
            except Exception as e:
                result.results[name] = ProviderResponse(
                    content="", model="", provider=name, error=str(e)
                )
            result.timings[name] = time.time() - start

        return result

    def compare_strategies(
        self,
        strategy_description: str,
        providers: Optional[List[str]] = None,
    ) -> ComparisonResult:
        """Ask multiple models to generate a trading strategy and compare."""
        system = (
            "你是一个专业的量化交易策略开发者。根据描述生成一个完整的交易策略。\n"
            "用JSON格式回复: {\"name\": \"策略名\", \"code\": \"Python代码\", "
            "\"params\": {}, \"description\": \"描述\", \"risk_notes\": \"风险\"}"
        )
        return self.compare(strategy_description, providers=providers, system=system)

    def compare_analysis(
        self,
        market_data: str,
        question: str,
        providers: Optional[List[str]] = None,
    ) -> ComparisonResult:
        """Ask multiple models to analyze the same market data."""
        system = (
            "你是一个专业的量化交易分析师。基于提供的市场数据，给出专业分析。\n"
            "回答要简洁、专业，包含具体数字和指标。"
        )
        prompt = f"## 市场数据\n{market_data}\n\n## 问题\n{question}"
        return self.compare(prompt, providers=providers, system=system)

    def compare_code_review(
        self,
        code: str,
        providers: Optional[List[str]] = None,
    ) -> ComparisonResult:
        """Ask multiple models to review the same code."""
        system = (
            "你是一个资深的Python代码审查专家。审查代码中的bug、性能问题和设计缺陷。\n"
            "用JSON格式回复: {\"issues\": [{\"line\": 行号, \"description\": \"描述\"}], "
            "\"suggestions\": [\"建议\"], \"summary\": \"总结\"}"
        )
        prompt = f"```python\n{code}\n```\n请审查以上代码。"
        return self.compare(prompt, providers=providers, system=system)
