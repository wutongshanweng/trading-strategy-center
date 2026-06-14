"""DeepSeek API client — OpenAI-compatible interface for DeepSeek models."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Generator

import requests

from core.config.settings import get_settings

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """Client for DeepSeek API (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.deepseek_api_key
        self.api_base = (api_base or settings.deepseek_api_base).rstrip("/")
        self.model = model or settings.deepseek_model
        self.max_tokens = max_tokens
        self.temperature = temperature

        if not self.api_key:
            logger.warning("DeepSeek API key not configured. Set DEEPSEEK_API_KEY in .env")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Send a chat completion request."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": stream,
        }

        try:
            resp = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error("DeepSeek API request failed: %s", e)
            return {"error": str(e)}

    def complete(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """Simple completion: send prompt, return text response."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        result = self.chat(messages, **kwargs)
        if "error" in result:
            return f"[Error] {result['error']}"
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return f"[Unexpected response] {json.dumps(result, ensure_ascii=False)}"

    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Generator[str, None, None]:
        """Stream chat response token by token."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": True,
        }

        try:
            with requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=120,
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")
                        if line_str.startswith("data: "):
                            data_str = line_str[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except requests.exceptions.RequestException as e:
            logger.error("DeepSeek streaming failed: %s", e)
            yield f"\n[Error] {e}"

    def analyze_market_data(self, data_summary: str, question: str) -> str:
        """Use DeepSeek to analyze market data and answer questions."""
        system = (
            "你是一个专业的量化交易分析师。基于提供的市场数据，给出专业分析和建议。"
            "回答要简洁、专业，包含具体的数字和指标。"
        )
        prompt = f"## 市场数据摘要\n{data_summary}\n\n## 问题\n{question}"
        return self.complete(prompt, system=system)

    def generate_strategy_code(self, description: str, language: str = "python") -> str:
        """Generate trading strategy code from natural language description."""
        system = (
            "你是一个专业的量化策略开发者。根据用户的描述生成高质量的交易策略代码。"
            "代码要遵循最佳实践，包含注释和错误处理。"
            f"使用 {language} 语言。"
        )
        prompt = f"请根据以下描述生成交易策略代码：\n\n{description}"
        return self.complete(prompt, system=system)

    def review_code(self, code: str, focus: str = "correctness") -> str:
        """Review code and provide feedback."""
        system = (
            "你是一个资深的代码审查专家。审查提供的代码，找出bug、性能问题、"
            "代码质量问题，并给出改进建议。审查重点: " + focus
        )
        prompt = f"```python\n{code}\n```"
        return self.complete(prompt, system=system)

    def optimize_parameters(self, strategy_desc: str, metrics: Dict[str, float]) -> str:
        """Suggest parameter optimizations based on backtest metrics."""
        system = (
            "你是一个量化策略优化专家。基于回测指标，给出参数调整建议。"
            "建议要具体，包含参数名和推荐值。"
        )
        prompt = (
            f"## 策略描述\n{strategy_desc}\n\n"
            f"## 回测指标\n{json.dumps(metrics, indent=2)}\n\n"
            "请给出参数优化建议。"
        )
        return self.complete(prompt, system=system)
