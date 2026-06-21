"""多 agent 交易决策委员会 — 单测。

合成合法 OHLC, 不触网/不触库。验证各 agent 产出 + 主席裁决归一化。
"""

import numpy as np
import pandas as pd
import pytest


def _synth(n=250, seed=11):
    np.random.seed(seed)
    t = np.arange(n)
    base = 3000 + 250 * np.sin(t / 18) + t * 1.5 + np.random.normal(0, 12, n)
    o = base + np.random.normal(0, 5, n)
    c = base + np.random.normal(0, 5, n)
    hi = np.maximum(o, c) + abs(np.random.normal(8, 4, n))
    lo = np.minimum(o, c) - abs(np.random.normal(8, 4, n))
    v = abs(np.random.normal(1e4, 3e3, n))
    return pd.DataFrame({"open": o, "high": hi, "low": lo, "close": c, "volume": v},
                        index=pd.date_range("2024-01-01", periods=n, freq="D"))


class TestCommittee:
    def test_deliberate_structure(self):
        from signals.agents import get_committee
        v = get_committee().deliberate(_synth(), "RB2510", "RB")
        assert v["direction"] in ("BUY", "SELL", "WATCH")
        assert "net_score" in v and -1 <= v["net_score"] <= 1
        assert 1 <= v["star_rating"] <= 5
        assert 0 <= v["confidence"] <= 1
        assert isinstance(v["agents"], list) and len(v["agents"]) >= 1

    def test_each_agent_emits_opinion(self):
        from signals.agents import get_committee
        v = get_committee().deliberate(_synth(), "RB2510", "RB")
        names = {a["name"] for a in v["agents"]}
        # 技术/因子/ML/缠论/宏观 至少多数到位
        assert "technical" in names
        for a in v["agents"]:
            assert a["direction"] in ("BUY", "SELL", "HOLD", "WATCH", "N/A")
            assert 0 <= a["confidence"] <= 1
            assert a["reason"]

    def test_macro_agent_uses_news(self):
        from signals.agents import get_committee
        news = [{"products": ["RB"], "sentiment_score": 0.8, "title": "螺纹大涨"},
                {"products": ["RB"], "sentiment_score": 0.6, "title": "需求回升"}]
        v = get_committee().deliberate(_synth(), "RB2510", "RB", news_items=news)
        macro = next((a for a in v["agents"] if a["name"] == "macro"), None)
        assert macro is not None
        assert macro["detail"]["n_news"] == 2
        assert macro["direction"] == "BUY"  # 正情绪 → 看多

    def test_agreement_and_weights(self):
        from signals.agents import AGENT_WEIGHTS
        # 权重和接近 1
        assert abs(sum(AGENT_WEIGHTS.values()) - 1.0) < 0.01
