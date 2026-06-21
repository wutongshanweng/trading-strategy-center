"""中文财经新闻情绪分析 — 关键词词典法 (替换原英文词袋)。

不依赖 ML/外部模型, 用利多/利空中文关键词计分, 适配中文财经快讯。
"""

from __future__ import annotations

from typing import Dict, List

# 利多词 (出现→正向)
POSITIVE_WORDS: List[str] = [
    "突破", "大涨", "上涨", "涨停", "走高", "回升", "反弹", "增长", "增持", "利好",
    "扩张", "超预期", "提振", "走强", "新高", "需求旺盛", "去库存", "降准", "降息",
    "刺激", "复苏", "回暖", "改善", "提价", "上调", "看多", "做多", "买入",
]

# 利空词 (出现→负向)
NEGATIVE_WORDS: List[str] = [
    "大跌", "下跌", "跌停", "走低", "回落", "下挫", "下滑", "减少", "减持", "利空",
    "收缩", "不及预期", "施压", "走弱", "新低", "需求疲软", "累库", "加息", "制裁",
    "衰退", "恶化", "降价", "下调", "看空", "做空", "卖出", "抛售", "停产", "过剩",
]


class NewsSentimentAnalyzer:
    """中文财经新闻情绪分析器 — 词典法。"""

    def __init__(self,
                 positive_words: List[str] | None = None,
                 negative_words: List[str] | None = None):
        self.positive_words = positive_words or POSITIVE_WORDS
        self.negative_words = negative_words or NEGATIVE_WORDS

    def analyze(self, text: str) -> Dict:
        """返回 {score: [-1,1], sentiment, label, confidence, hits}。"""
        if not text or not isinstance(text, str) or not text.strip():
            return {"score": 0.0, "sentiment": "neutral", "label": "🟡",
                    "confidence": 0.0, "hits": []}
        hits_pos = [w for w in self.positive_words if w in text]
        hits_neg = [w for w in self.negative_words if w in text]
        pos, neg = len(hits_pos), len(hits_neg)
        total = pos + neg
        if total == 0:
            return {"score": 0.0, "sentiment": "neutral", "label": "🟡",
                    "confidence": 0.0, "hits": []}
        score = (pos - neg) / total
        if score > 0.15:
            sentiment, label = "bullish", "🟢"
        elif score < -0.15:
            sentiment, label = "bearish", "🔴"
        else:
            sentiment, label = "neutral", "🟡"
        confidence = min(1.0, total / 5.0)
        return {
            "score": round(score, 3), "sentiment": sentiment, "label": label,
            "confidence": round(confidence, 3), "hits": hits_pos + hits_neg,
        }
