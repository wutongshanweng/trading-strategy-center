from typing import Dict
import re


class NewsSentimentAnalyzer:
    positive_words = {"surge", "soar", "rally", "gain", "up", "rise", "bullish", "positive",
                       "growth", "profit", "strong", "outperform", "upgrade", "beat", "exceed",
                       "improve", "boom", "recovery", "expansion", "opportunity"}
    negative_words = {"drop", "fall", "decline", "down", "bearish", "negative", "loss", "weak",
                       "underperform", "downgrade", "miss", "below", "cut", "lower", "sell",
                       "crash", "plunge", "slump", "recession", "concern"}

    def analyze(self, text: str) -> Dict:
        if not text or not isinstance(text, str) or not text.strip():
            return {"score": 0.0, "sentiment": "neutral", "confidence": 0.0}
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        if not words:
            return {"score": 0.0, "sentiment": "neutral", "confidence": 0.0}
        pos = sum(1 for w in words if w in self.positive_words)
        neg = sum(1 for w in words if w in self.negative_words)
        score = max(-1.0, min(1.0, (pos - neg) / len(words)))
        sentiment = "positive" if score > 0.05 else "negative" if score < -0.05 else "neutral"
        return {"score": score, "sentiment": sentiment, "confidence": min(1.0, (pos + neg) / max(len(words) * 0.1, 1))}
