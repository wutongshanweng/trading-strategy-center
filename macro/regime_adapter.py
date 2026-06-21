"""宏观→市态/品种联动分析 + 远期趋势展望 (规则引擎, 非 ML)。

输入: 宏观指标变化 + 新闻情绪 → 输出: 市态判断 + 品种影响 + 趋势展望文本。
"""

from __future__ import annotations

from typing import Dict, List

from core.config.watchlist import MACRO_PRODUCT_LINKAGE, linkage_for_product
from data_center.knowledge.contract_knowledge import ContractKnowledgeBase

_KB = ContractKnowledgeBase()


def _name_cn(product: str) -> str:
    c = _KB.get_contract(product)
    return c.name_cn if c else product


class RegimeAdapter:
    """宏观联动 + 市态 + 展望。"""

    def __init__(self, aggregator=None):
        self._agg = aggregator

    def _get_agg(self):
        if self._agg is None:
            from macro.aggregator import MacroAggregator
            self._agg = MacroAggregator()
        return self._agg

    def linkage(self, news_items: List[Dict] | None = None) -> Dict:
        """联动分析: 市态 + 新闻影响品种 + 宏观↔品种关联度。"""
        agg = self._get_agg()
        dash = agg.dashboard()["indicators"]
        by_code = {d["code"]: d for d in dash}

        # --- 市态判断 (基于 PMI/M2/PPI 组合) ---
        market_state, state_reason = self._judge_regime(by_code)

        # --- 宏观→品种关联度表 (取有数据指标的关联) ---
        linkages: List[Dict] = []
        for indicator, mapping in MACRO_PRODUCT_LINKAGE.items():
            ind = by_code.get(indicator)
            if not ind or not ind.get("available"):
                continue
            for product, corr in sorted(mapping.items(), key=lambda kv: -abs(kv[1]))[:3]:
                linkages.append({
                    "indicator": indicator, "product": product,
                    "product_cn": _name_cn(product), "corr": corr,
                    "trend": ind.get("trend", "→"),
                })

        # --- 新闻影响品种 (从已标签新闻聚合情绪) ---
        news_impact: List[Dict] = []
        if news_items:
            agg_map: Dict[str, Dict] = {}
            for n in news_items:
                for p in n.get("products", []):
                    a = agg_map.setdefault(p, {"score": 0.0, "count": 0, "titles": []})
                    a["score"] += n.get("sentiment_score", 0.0)
                    a["count"] += 1
                    if len(a["titles"]) < 2 and n.get("title"):
                        a["titles"].append(n["title"])
            for p, a in sorted(agg_map.items(), key=lambda kv: -kv[1]["count"])[:6]:
                avg = a["score"] / a["count"] if a["count"] else 0.0
                news_impact.append({
                    "product": p, "product_cn": _name_cn(p),
                    "avg_sentiment": round(avg, 3),
                    "label": "🟢" if avg > 0.15 else "🔴" if avg < -0.15 else "🟡",
                    "count": a["count"], "titles": a["titles"],
                })

        return {
            "market_state": market_state, "state_reason": state_reason,
            "news_impact": news_impact, "linkages": linkages,
        }

    def _judge_regime(self, by_code: Dict[str, Dict]) -> tuple[str, str]:
        pmi = by_code.get("PMI", {})
        m2 = by_code.get("M2", {})
        reasons = []
        score = 0
        if pmi.get("available"):
            v = pmi.get("value")
            if v is not None and v >= 50:
                score += 1
                reasons.append(f"PMI {v} 处扩张区间")
            elif v is not None:
                score -= 1
                reasons.append(f"PMI {v} 处收缩区间")
            if pmi.get("trend") == "↑":
                score += 1
                reasons.append("PMI 回升")
        if m2.get("available") and m2.get("trend") == "↑":
            score += 1
            reasons.append("M2 增速回升, 流动性充裕")
        if score >= 2:
            return "震荡偏强", " + ".join(reasons) or "宏观偏暖"
        if score <= -1:
            return "震荡偏弱", " + ".join(reasons) or "宏观偏冷"
        return "震荡", " + ".join(reasons) or "宏观中性"

    def outlook(self) -> Dict:
        """远期趋势展望: 连续 N 期方向 → 模板化文本。"""
        agg = self._get_agg()
        cards: List[Dict] = []
        for code in ("PMI", "M2", "CPI", "PPI"):
            cd = agg.consecutive_direction(code, n=3)
            if cd["periods"] < 2:
                continue
            dir_cn = {"up": "回升", "down": "回落"}.get(cd["direction"], "持平")
            # 找受该指标正向影响最大的品种
            mapping = MACRO_PRODUCT_LINKAGE.get(code, {})
            top = sorted(mapping.items(), key=lambda kv: -kv[1])[:2] if mapping else []
            prod_txt = "、".join(f"{_name_cn(p)}" for p, _ in top) or "工业品"
            if cd["direction"] == "up":
                expect = f"{prod_txt} 需求预期改善, 中枢有望上移"
            elif cd["direction"] == "down":
                expect = f"{prod_txt} 承压, 关注下行风险"
            else:
                expect = f"{prod_txt} 维持区间震荡"
            cards.append({
                "indicator": code, "direction": cd["direction"],
                "periods": cd["periods"], "latest": cd["latest"],
                "text": f"{code} 连续 {cd['periods']} 期{dir_cn} (最新 {cd['latest']}) → {expect}",
            })
        if not cards:
            cards.append({"indicator": "—", "direction": "flat", "periods": 0,
                          "latest": None, "text": "宏观指标无明显连续趋势, 维持中性观望。"})
        return {"outlook": cards}
