"""LLM-powered code reviewer: analyze code quality, bugs, and improvements."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .deepseek_client import DeepSeekClient

logger = logging.getLogger(__name__)


class CodeReviewer:
    """Use DeepSeek to review, audit, and improve code."""

    def __init__(self, client: Optional[DeepSeekClient] = None):
        self.client = client or DeepSeekClient()

    def review(
        self,
        code: str,
        focus: str = "correctness",
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Review code and return structured feedback.

        Args:
            code: Code to review.
            focus: Review focus — "correctness", "performance", "security", "readability".
            context: Additional context about the code.

        Returns:
            Dict with: severity, issues, suggestions, summary.
        """
        context_text = f"\n\n## 上下文\n{context}" if context else ""
        system = (
            "你是一个资深的Python量化交易代码审查专家。审查代码并给出结构化反馈。\n"
            "请用JSON格式回复:\n"
            '{"severity": "critical|warning|info", '
            '"issues": [{"line": 行号, "type": "类型", "description": "描述", "fix": "修复建议"}], '
            '"suggestions": ["改进建议1", ...], '
            '"summary": "总体评价"}')
        prompt = f"## 代码\n```python\n{code}\n```\n\n## 审查重点\n{focus}{context_text}"
        response = self.client.complete(prompt, system=system)

        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            return {"error": "Could not parse response", "raw": response}
        except json.JSONDecodeError as e:
            return {"error": str(e), "raw": response}

    def audit_trading_logic(self, strategy_code: str, risk_config: Dict[str, Any]) -> Dict[str, Any]:
        """Audit trading-specific logic: risk management, position sizing, stop losses."""
        system = (
            "你是一个量化交易风控专家。审计交易策略的风控逻辑。\n"
            "关注: 止损止盈、仓位管理、资金曲线保护、极端行情处理。\n"
            "请用JSON格式回复:\n"
            '{"risk_score": 1-10, "critical_gaps": ["..."], '
            '"missing_controls": ["..."], "recommendations": ["..."]}')
        prompt = (
            f"## 策略代码\n```python\n{strategy_code}\n```\n\n"
            f"## 风控配置\n{json.dumps(risk_config, indent=2, ensure_ascii=False)}"
        )
        response = self.client.complete(prompt, system=system)

        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            return {"error": "Could not parse response", "raw": response}
        except json.JSONDecodeError as e:
            return {"error": str(e), "raw": response}

    def suggest_refactoring(self, code: str, target: str = "maintainability") -> List[Dict[str, str]]:
        """Suggest refactoring improvements."""
        system = (
            "你是一个代码重构专家。给出具体的重构建议。\n"
            "每个建议包含: target(目标代码), replacement(替换代码), reason(原因)。\n"
            "请用JSON数组格式回复。"
        )
        prompt = f"## 代码\n```python\n{code}\n```\n\n## 重构目标\n{target}"
        response = self.client.complete(prompt, system=system)

        try:
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            return [{"error": "Could not parse response", "raw": response}]
        except json.JSONDecodeError as e:
            return [{"error": str(e), "raw": response}]

    def explain_error(self, error_traceback: str, code_context: Optional[str] = None) -> str:
        """Explain an error and suggest fixes."""
        system = (
            "你是一个Python调试专家。分析错误追踪，解释错误原因，给出修复方案。"
            "回答要简洁直接。"
        )
        ctx = f"\n\n## 相关代码\n```python\n{code_context}\n```" if code_context else ""
        prompt = f"## 错误追踪\n```\n{error_traceback}\n```{ctx}"
        return self.client.complete(prompt, system=system)
