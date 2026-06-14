"""LLM-powered market analyzer: interpret market data and generate insights."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import numpy as np

from .deepseek_client import DeepSeekClient

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """Use DeepSeek to analyze market data and generate trading insights."""

    def __init__(self, client: Optional[DeepSeekClient] = None):
        self.client = client or DeepSeekClient()

    def _summarize_data(self, data: Dict[str, Any]) -> str:
        """Create a concise text summary of market data for LLM consumption."""
        lines = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                lines.append(f"- {key}: {value:.4f}" if isinstance(value, float) else f"- {key}: {value}")
            elif isinstance(value, list) and len(value) > 0:
                arr = np.array(value)
                lines.append(f"- {key}: mean={arr.mean():.4f}, std={arr.std():.4f}, last={arr[-1]:.4f}, len={len(arr)}")
            elif isinstance(value, dict):
                lines.append(f"- {key}: {json.dumps(value, ensure_ascii=False)}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def analyze_regime(
        self,
        returns: List[float],
        volatility: float,
        trend_strength: float,
        regime_labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze current market regime using LLM reasoning."""
        arr = np.array(returns)
        summary = (
            f"- 近期收益率: mean={arr.mean():.4f}, std={arr.std():.4f}\n"
            f"- 当前波动率: {volatility:.4f}\n"
            f"- 趋势强度: {trend_strength:.4f}\n"
            f"- 收益率偏度: {float(np.mean(((arr - arr.mean()) / (arr.std() + 1e-8)) ** 3)):.4f}\n"
            f"- 正收益率占比: {(arr > 0).mean():.2%}"
        )
        if regime_labels:
            summary += f"\n- 当前状态机标签: {regime_labels[-1]}"

        system = (
            "你是一个市场状态分析专家。基于量化指标判断当前市场状态。\n"
            "请用JSON格式回复:\n"
            '{"regime": "trending_up|trending_down|range_bound|high_volatility|crisis", '
            '"confidence": 0.0-1.0, "description": "状态描述", '
            '"suggested_strategies": ["适合的策略类型"], '
            '"risk_level": "low|medium|high|extreme", '
            '"key_observations": ["关键观察"]}')
        response = self.client.complete(
            f"## 市场量化指标\n{summary}",
            system=system,
        )

        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            return {"error": "Could not parse response", "raw": response}
        except json.JSONDecodeError as e:
            return {"error": str(e), "raw": response}

    def generate_trading_plan(
        self,
        market_summary: Dict[str, Any],
        current_positions: List[Dict[str, Any]],
        risk_budget: float,
    ) -> Dict[str, Any]:
        """Generate a trading plan based on market analysis and current state."""
        system = (
            "你是一个资深的交易策略师。基于市场分析和当前持仓，制定交易计划。\n"
            "请用JSON格式回复:\n"
            '{"plan": [{"action": "buy|sell|hold|close", "symbol": "品种", '
            '"reason": "原因", "size_pct": 建议仓位百分比, '
            '"stop_loss": 止损价, "take_profit": 止盈价}], '
            '"overall_bias": "bullish|bearish|neutral", '
            '"risk_assessment": "风险评估", '
            '"key_levels": {"support": 支撑位, "resistance": 阻力位}}')
        prompt = (
            f"## 市场分析\n{json.dumps(market_summary, indent=2, ensure_ascii=False)}\n\n"
            f"## 当前持仓\n{json.dumps(current_positions, indent=2, ensure_ascii=False)}\n\n"
            f"## 风险预算\n{risk_budget:.2%}"
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

    def interpret_backtest(self, metrics: Dict[str, float], strategy_name: str = "") -> str:
        """Interpret backtest results and provide narrative analysis."""
        system = (
            "你是一个回测结果分析专家。解读回测指标，给出专业评价和改进建议。"
            "回答要包含: 总体评价、优势、劣势、改进建议。用中文回答。"
        )
        prompt = (
            f"## 策略名: {strategy_name}\n\n"
            f"## 回测指标\n{json.dumps(metrics, indent=2)}"
        )
        return self.client.complete(prompt, system=system)

    def cross_asset_analysis(
        self,
        correlations: Dict[str, float],
        sector_performance: Dict[str, float],
    ) -> Dict[str, Any]:
        """Analyze cross-asset relationships and sector rotation."""
        system = (
            "你是一个跨市场分析专家。分析资产相关性和板块轮动。\n"
            "请用JSON格式回复:\n"
            '{"rotation_phase": "early|mid|late|reversal", '
            '"leading_sectors": ["领涨板块"], '
            '"lagging_sectors": ["落后板块"], '
            '"correlation_insights": ["相关性洞察"], '
            '"actionable_recommendations": ["可操作建议"]}')
        prompt = (
            f"## 资产相关性\n{json.dumps(correlations, indent=2)}\n\n"
            f"## 板块表现\n{json.dumps(sector_performance, indent=2)}"
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
