"""warehouse API 辅助函数 + 期权知识库 — 单测。"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import math

from data_center.api.warehouse import _norm_stock_code, _clean_json
from data_center.knowledge.options_knowledge import get_options_knowledge


def test_norm_stock_code():
    assert _norm_stock_code("600019") == "600019.SH"
    assert _norm_stock_code("600019.SH") == "600019.SH"
    assert _norm_stock_code("000001") == "000001.SZ"
    assert _norm_stock_code("300750") == "300750.SZ"
    assert _norm_stock_code(" 600019.sh ") == "600019.SH"
    assert _norm_stock_code("688981") == "688981.SH"  # 科创板 6 开头


def test_clean_json_strips_nan_inf():
    out = _clean_json({"a": float("nan"), "b": 1.5, "c": [float("inf"), 2.0], "d": {"e": float("-inf")}})
    assert out["a"] is None
    assert out["b"] == 1.5
    assert out["c"] == [None, 2.0]
    assert out["d"]["e"] is None


def test_options_knowledge():
    kb = get_options_knowledge()
    assert kb.get_product("M").exercise_style == "美式"        # 商品期权美式
    assert kb.get_product("510050").exercise_style == "欧式"   # ETF 期权欧式
    assert "M" in kb.get_product("M").related_futures
    views = kb.strategies_for_view("震荡")
    assert any(s.name == "short_strangle" for s in views)
