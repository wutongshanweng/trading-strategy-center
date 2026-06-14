"""LLM Strategy Factory — generate, validate, and register complete strategies from natural language."""

from __future__ import annotations

import ast
import json
import logging
import string
import textwrap
from typing import Any, Optional

from .deepseek_client import DeepSeekClient
from .strategy_generator import StrategyGenerator

logger = logging.getLogger(__name__)

# Use string.Template instead of .format() to avoid brace-escaping issues with JSON/code
_STRATEGY_TEMPLATE = string.Template(
    """
import pandas as pd
import numpy as np
from signals.base import BaseStrategy, Signal
from signals.registry import register
from datetime import datetime

@register("$name")
class $class_name(BaseStrategy):
    \"\"\"$description\"\"\"

    strategy_name = "$name"
    params = $params

    def compute(self, data: pd.DataFrame, symbol: str) -> Signal:
        $compute_body

    def get_params(self) -> dict:
        return self.params
"""
)


class StrategyFactory:
    """Use LLM to generate, validate, and register executable trading strategies."""

    def __init__(self, client: Optional[DeepSeekClient] = None):
        self.client = client or DeepSeekClient()
        self.generator = StrategyGenerator(self.client)

    def create_strategy(
        self,
        description: str,
        name: Optional[str] = None,
        params: Optional[dict] = None,
        auto_register: bool = False,
    ) -> dict:
        """Generate a complete, runnable strategy from description."""
        llm_result = self.generator.generate_strategy(description, constraints={"style": "signals.base.BaseStrategy"})

        strategy_name = name or llm_result.get("name", "llm_generated")
        class_name = f"LLM_{strategy_name.replace(' ', '_').title()}"
        params_dict = params or llm_result.get("params", {})

        compute_body = llm_result.get("code", "return Signal(...)")
        compute_body = textwrap.dedent(compute_body).strip()
        lines = compute_body.split("\n")
        indented = "\n        ".join(lines)

        code = _STRATEGY_TEMPLATE.safe_substitute(
            name=strategy_name,
            class_name=class_name,
            description=llm_result.get("description", ""),
            params=json.dumps(params_dict, indent=4),
            compute_body=indented,
        )

        validation = self._validate_code(code)

        result = {
            "name": strategy_name,
            "code": code,
            "description": llm_result.get("description", description),
            "params": params_dict,
            "rationale": llm_result.get("rationale", ""),
            "risk_notes": llm_result.get("risk_notes", ""),
            "validation": validation,
        }

        if auto_register and validation["valid"]:
            self._register_strategy(code, strategy_name)

        return result

    def create_ml_strategy(
        self,
        model_type: str,
        symbol: str,
        features: list[str],
        params: Optional[dict] = None,
    ) -> dict:
        """Create a strategy that uses an ML model for signal generation."""
        model_params = params or {}
        model_params_json = json.dumps(model_params)
        compute_body = textwrap.dedent(f"""
            # ML Strategy using {model_type}
            from ml.pipeline import MLPipeline

            pipeline = MLPipeline(params={model_params_json})
            pipeline.load_or_train(data, symbol=\"{symbol}\")

            prediction = pipeline.predict(data)

            if prediction > 0.5:
                direction = "BUY"
                score = float(prediction * 10)
            elif prediction < -0.5:
                direction = "SELL"
                score = float(prediction * 10)
            else:
                direction = "HOLD"
                score = 0.0

            confidence = min(abs(float(prediction)), 1.0)
            price = float(data['close'].iloc[-1])

            return Signal(
                strategy_name=self.strategy_name, symbol=symbol,
                direction=direction, confidence=confidence, score=score,
                price=price, timestamp=datetime.now(),
                reason=f"ML({model_type}) prediction: {{prediction:.4f}}",
                source_system="tinghai",
            )
        """).strip()
        lines = compute_body.split("\n")
        indented = "\n        ".join(lines)

        class_name = f"ML_{model_type.title()}_{symbol}"
        strategy_name = f"ml_{model_type}_{symbol.lower()}"

        code = _STRATEGY_TEMPLATE.safe_substitute(
            name=strategy_name,
            class_name=class_name,
            description=f"ML strategy using {model_type} for {symbol}",
            params=json.dumps(model_params, indent=4),
            compute_body=indented,
        )

        return {
            "name": strategy_name, "code": code,
            "description": f"ML {model_type} strategy for {symbol}",
            "params": model_params, "features": features,
            "validation": self._validate_code(code),
        }

    def create_alpha_factor_strategy(
        self, factor_names: list[str], weights: Optional[dict[str, float]] = None
    ) -> dict:
        """Create a strategy that combines multiple alpha factors."""
        w = weights or {f: 1.0 / len(factor_names) for f in factor_names}
        weights_json = json.dumps(w, indent=4)
        factor_json = json.dumps(factor_names)

        compute_body = textwrap.dedent(f"""
            from core.alpha.alpha101.factor_pipeline import FactorPipeline
            from core.alpha.alpha101.factor_registry import FactorRegistry

            pipeline = FactorPipeline(max_workers=4)
            factors = pipeline.compute_factors({factor_json}, data)
            combined = sum(factors[name] * {weights_json}[name] for name in factors)
            latest_value = combined.iloc[-1]

            if pd.isna(latest_value):
                return Signal(strategy_name=self.strategy_name, symbol=symbol, direction="HOLD",
                              confidence=0.0, score=0.0, price=float(data['close'].iloc[-1]),
                              timestamp=datetime.now(), reason="NaN factor value",
                              source_system="tinghai")

            threshold = 0.5
            if latest_value > threshold:
                direction = "BUY"
                score = float(min(latest_value * 5, 10))
            elif latest_value < -threshold:
                direction = "SELL"
                score = float(max(latest_value * 5, -10))
            else:
                direction = "HOLD"
                score = 0.0

            confidence = min(abs(float(latest_value)), 1.0)
            price = float(data['close'].iloc[-1])

            return Signal(
                strategy_name=self.strategy_name, symbol=symbol,
                direction=direction, confidence=confidence, score=score,
                price=price, timestamp=datetime.now(),
                reason=f"Alpha factors: {{latest_value:.4f}}",
                source_system="tinghai",
            )
        """).strip()
        lines = compute_body.split("\n")
        indented = "\n        ".join(lines)

        factor_key = "_".join(factor_names[:3])
        code = _STRATEGY_TEMPLATE.safe_substitute(
            name=f"alpha_combo_{factor_key}",
            class_name=f"AlphaCombo_{factor_key.title()}",
            description=f"Combined alpha factors: {', '.join(factor_names)}",
            params=json.dumps(w, indent=4),
            compute_body=indented,
        )

        return {
            "name": f"alpha_combo_{factor_key}", "code": code,
            "description": f"Alpha factor combination: {', '.join(factor_names)}",
            "factors": factor_names, "weights": w,
            "validation": self._validate_code(code),
        }

    def create_multi_timeframe_strategy(
        self, timeframes: list[str], strategies: dict[str, str]
    ) -> dict:
        """Create a strategy combining signals from multiple timeframes."""
        tf_json = json.dumps(timeframes)
        strat_json = json.dumps(strategies, indent=4)

        compute_body = textwrap.dedent(f"""
            from signals.registry import get_strategy

            timeframes = {tf_json}
            active_strategies = {strat_json}
            signals = []

            for tf in timeframes:
                resampled = data.resample(tf).agg({{
                    'open': 'first', 'high': 'max', 'low': 'min',
                    'close': 'last', 'volume': 'sum'
                }}).dropna()
                for strat_name, strat_class in active_strategies.items():
                    strategy = get_strategy(strat_class)()
                    signal = strategy.compute(resampled, symbol)
                    signal.resonance_layer = tf
                    signals.append(signal)

            buy_votes = sum(1 for s in signals if s.direction == "BUY" and s.confidence > 0.5)
            sell_votes = sum(1 for s in signals if s.direction == "SELL" and s.confidence > 0.5)
            total = buy_votes + sell_votes

            if total == 0:
                return Signal(strategy_name=self.strategy_name, symbol=symbol, direction="HOLD",
                              confidence=0.0, score=0.0, price=float(data['close'].iloc[-1]),
                              timestamp=datetime.now(), reason="No clear signal",
                              source_system="chufeng")

            direction = "BUY" if buy_votes > sell_votes else "SELL"
            confidence = max(buy_votes, sell_votes) / len(signals)

            return Signal(
                strategy_name=self.strategy_name, symbol=symbol,
                direction=direction, confidence=confidence, score=sum(s.score for s in signals if s.direction != "HOLD") / total,
                price=float(data['close'].iloc[-1]), timestamp=datetime.now(),
                reason=f"MultiTF: {{buy_votes}}B/{{sell_votes}}S from {{len(signals)}} signals",
                source_system="chufeng",
            )
        """).strip()
        lines = compute_body.split("\n")
        indented = "\n        ".join(lines)

        code = _STRATEGY_TEMPLATE.safe_substitute(
            name="multi_timeframe",
            class_name="MultiTimeframeStrategy",
            description=f"Multi-timeframe: {', '.join(timeframes)}",
            params=json.dumps({"timeframes": timeframes, "strategies": strategies}, indent=4),
            compute_body=indented,
        )

        return {"name": "multi_timeframe", "code": code, "validation": self._validate_code(code)}

    def explain_and_register(
        self, strategy_code: str, description: str, auto_register: bool = False
    ) -> str:
        """Use LLM to explain what a strategy does and optionally register it."""
        explanation = self.client.complete(
            f"解释以下交易策略的功能、逻辑和风险：\n```python\n{strategy_code}\n```",
            system="你是一个量化策略分析专家。用简洁专业的中文解释策略。",
        )
        if auto_register:
            self._register_strategy(strategy_code, "explained_strategy")
        return explanation

    # ---- internal ---------------------------------------------------------

    @staticmethod
    def _validate_code(code: str) -> dict:
        try:
            ast.parse(code)
            return {"valid": True, "errors": []}
        except SyntaxError as e:
            return {"valid": False, "errors": [f"SyntaxError: {e}"]}

    @staticmethod
    def _register_strategy(code: str, name: str) -> bool:
        try:
            exec(compile(ast.parse(code), filename=f"<{name}>", mode="exec"))
            logger.info(f"Strategy '{name}' registered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to register strategy '{name}': {e}")
            return False
