"""LLM-powered strategy generator: generate, optimize, and evolve trading strategies."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .deepseek_client import DeepSeekClient

logger = logging.getLogger(__name__)


class StrategyGenerator:
    """Use DeepSeek to generate, review, and optimize trading strategies."""

    def __init__(self, client: Optional[DeepSeekClient] = None):
        self.client = client or DeepSeekClient()

    def generate_strategy(self, description: str, constraints: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate a complete trading strategy from natural language description.

        Args:
            description: Natural language description of the strategy.
            constraints: Optional constraints (e.g. {"max_holding_days": 5, "instruments": ["futures"]}).

        Returns:
            Dict with keys: name, code, params, rationale, risk_notes.
        """
        constraint_text = ""
        if constraints:
            constraint_text = f"\n\n## 约束条件\n{json.dumps(constraints, indent=2, ensure_ascii=False)}"

        system = (
            "你是一个专业的量化交易策略开发者。根据描述生成完整的交易策略。\n"
            "请用JSON格式回复，包含以下字段:\n"
            '{"name": "策略名", "code": "完整Python代码", '
            '"params": {"param1": value1, ...}, '
            '"description": "策略描述", '
            '"rationale": "策略逻辑依据", '
            '"risk_notes": "风险提示", '
            '"categories": ["trend", "momentum", ...], '
            '"timeframe": "推荐周期", '
            '"min_data_bars": 最少需要的K线数}')
        prompt = f"## 策略需求\n{description}{constraint_text}"
        response = self.client.complete(prompt, system=system)

        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            return {"error": "Could not parse response", "raw": response}
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse strategy JSON: %s", e)
            return {"error": str(e), "raw": response}

    def optimize_strategy(
        self,
        strategy_code: str,
        backtest_metrics: Dict[str, float],
        optimization_target: str = "sharpe_ratio",
    ) -> Dict[str, Any]:
        """Suggest parameter optimizations based on backtest results."""
        system = (
            "你是一个量化策略优化专家。基于回测结果，给出参数调整建议。\n"
            "请用JSON格式回复:\n"
            '{"suggested_params": {"param1": new_value, ...}, '
            '"reasoning": "调整原因", '
            '"expected_improvement": "预期改善", '
            '"warnings": ["可能的风险"]}')
        prompt = (
            f"## 策略代码\n```python\n{strategy_code}\n```\n\n"
            f"## 回测指标\n{json.dumps(backtest_metrics, indent=2)}\n\n"
            f"## 优化目标\n最大化 {optimization_target}"
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

    def generate_ensemble(
        self,
        strategy_descriptions: List[str],
        portfolio_constraints: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Generate an ensemble strategy that combines multiple signals."""
        system = (
            "你是一个投资组合策略专家。设计一个集成策略来组合多个交易信号。\n"
            "请用JSON格式回复:\n"
            '{"ensemble_method": "weighted_voting|stacking|regime_switching", '
            '"weights": {"strategy1": w1, ...}, '
            '"combination_rules": "...", '
            '"risk_management": "...", '
            '"rebalance_frequency": "..."}')
        desc_text = "\n".join(f"{i+1}. {d}" for i, d in enumerate(strategy_descriptions))
        constraint_text = ""
        if portfolio_constraints:
            constraint_text = f"\n\n## 组合约束\n{json.dumps(portfolio_constraints, indent=2, ensure_ascii=False)}"

        prompt = f"## 待组合的策略\n{desc_text}{constraint_text}"
        response = self.client.complete(prompt, system=system)

        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            return {"error": "Could not parse response", "raw": response}
        except json.JSONDecodeError as e:
            return {"error": str(e), "raw": response}

    def explain_signal(
        self,
        signal: Dict[str, Any],
        market_context: Dict[str, Any],
    ) -> str:
        """Generate a human-readable explanation of a trading signal."""
        system = (
            "你是一个交易信号解读专家。用简洁专业的中文解释交易信号的含义和依据。"
            "控制在3-5句话。"
        )
        prompt = (
            f"## 交易信号\n{json.dumps(signal, indent=2, ensure_ascii=False)}\n\n"
            f"## 市场背景\n{json.dumps(market_context, indent=2, ensure_ascii=False)}"
        )
        return self.client.complete(prompt, system=system)
