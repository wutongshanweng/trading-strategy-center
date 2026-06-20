"""
LLM 策略建议器 — 让 LLM 理解策略库现状并给出可执行建议。

把「策略目录 + 市场状态」打包成 prompt 交给 LLM:
  - 推荐匹配当前市态的策略
  - 解释某策略为何有效/失效
  - 据自然语言描述生成策略代码草稿

无 LLM 配置时优雅降级: 用 catalog 本地规则给出基础建议 (不报错)。

用法:
    from core.llm.strategy_advisor import LLMStrategyAdvisor
    advisor = LLMStrategyAdvisor()
    print(advisor.ask("螺纹钢目前适合用什么策略?", context={"regime": "trending"}))
"""

from __future__ import annotations

from typing import Dict, Optional

from loguru import logger


class LLMStrategyAdvisor:
    """LLM 驱动的策略建议器 (带本地降级)。"""

    def __init__(self, catalog=None, llm_client=None, model: str = "auto"):
        if catalog is None:
            from signals.catalog import get_catalog
            catalog = get_catalog()
        self.catalog = catalog
        self.llm_client = llm_client
        self.model = model

    def _ensure_client(self):
        """惰性获取 LLMClient; 失败返回 None (触发降级)。"""
        if self.llm_client is not None:
            return self.llm_client
        try:
            from core.llm.llm_client import LLMClient
            self.llm_client = LLMClient()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"LLM 未配置, 使用本地降级建议: {e}")
            self.llm_client = None
        return self.llm_client

    def ask(self, question: str, context: Optional[Dict] = None) -> str:
        """向 LLM 查询策略建议 (无 LLM 或调用失败时本地降级)。"""
        prompt = self._build_prompt(question, context)
        client = self._ensure_client()
        if client is None:
            return self._local_fallback(question, context)
        try:
            resp = client.complete(
                prompt,
                system="你是量化交易策略顾问, 基于给定的策略库和市场状态给出简洁、可执行的中文建议。")
            if self._is_error(resp):
                logger.warning(f"LLM 返回错误, 降级: {resp[:80]}")
                return self._local_fallback(question, context)
            return resp
        except Exception as e:  # noqa: BLE001
            logger.warning(f"LLM 调用失败, 降级: {e}")
            return self._local_fallback(question, context)

    def _build_prompt(self, question: str, context: Optional[Dict]) -> str:
        grouped = self.catalog.list_by_type()
        return (f"当前策略库概览:\n{self._format_catalog_for_llm(grouped)}\n\n"
                f"市场上下文: {context or '未提供'}\n\n查询要求: {question}\n\n"
                f"请基于上述策略库, 推荐 1-3 个最匹配的策略并简述理由。")

    def _format_catalog_for_llm(self, grouped: Dict) -> str:
        lines = []
        for stype, strats in grouped.items():
            lines.append(f"[{stype}] ({len(strats)}个)")
            for s in strats[:3]:
                lines.append(
                    f"  - {s.chinese_name}({s.name}): 夏普={s.sharpe:.2f} "
                    f"胜率={s.win_rate:.0%} 适合={[r.value for r in s.regime_fit]}")
            if len(strats) > 3:
                lines.append(f"  ... 还有 {len(strats)-3} 个")
        return "\n".join(lines)

    def _local_fallback(self, question: str, context: Optional[Dict]) -> str:
        """无 LLM 时的本地规则建议: 按 context 的市态查目录。"""
        regime = (context or {}).get("regime")
        results = self.catalog.query(regime=regime, top_k=3, active_only=True)
        if not results:
            results = self.catalog.query(top_k=3, active_only=True)
        if not results:
            return "[本地建议] 策略库为空。"
        lines = [f"[本地建议] (LLM 未配置, 基于策略目录规则)"]
        if regime:
            lines.append(f"针对市态「{regime}」推荐:")
        for s in results:
            lines.append(f"  · {s.chinese_name}({s.name}) — {s.description}")
        return "\n".join(lines)

    def generate_strategy(self, description: str) -> Dict:
        """据自然语言描述生成策略代码草稿 (无 LLM 时返回模板)。"""
        client = self._ensure_client()
        prompt = (f"根据以下描述生成一个策略类的 Python 代码。\n描述: {description}\n\n"
                  f"要求: 继承 signals.base.BaseStrategy; 用 @register 装饰器; "
                  f"包含完整 compute(self, df, symbol='') 方法返回 Signal 或 None; "
                  f"添加中文注释。只返回代码, 不返回解释。")
        if client is None:
            return {"code": self._code_template(description), "description": description,
                    "source": "template"}
        try:
            code = client.complete(prompt, system="你是 Python 量化策略代码生成器。")
            if self._is_error(code):
                logger.warning(f"LLM 代码生成返回错误, 返回模板: {code[:80]}")
                return {"code": self._code_template(description), "description": description,
                        "source": "template"}
            return {"code": code, "description": description, "source": "llm"}
        except Exception as e:  # noqa: BLE001
            logger.warning(f"LLM 代码生成失败, 返回模板: {e}")
            return {"code": self._code_template(description), "description": description,
                    "source": "template"}

    @staticmethod
    def _is_error(resp: str) -> bool:
        """LLMClient.complete 失败时返回 '[Error] ...' 字符串而非抛异常。"""
        return not resp or resp.lstrip().startswith("[Error]")

    @staticmethod
    def _code_template(description: str) -> str:
        return f'''import pandas as pd
from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register


@register
class CustomStrategy(BaseStrategy):
    """{description}"""
    name = "custom_strategy"
    description = "{description}"
    timeframes = ["1d"]
    params = {{}}

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        # TODO: 实现策略逻辑
        return None
'''
