"""关注品种列表 + 宏观↔品种联动规则 (静态配置)。

项目内此前没有集中的 watchlist 配置 (只散落在 websocket/demo 硬编码)。
此处提供单一可信源, 供信号扫描器、联动分析、模拟交易共用。
"""

from __future__ import annotations

from typing import Dict, List

# 关注的品种 (裸代码) — 信号扫描默认对这些品种全扫
WATCHLIST_PRODUCTS: List[str] = [
    "RB", "HC", "I", "CU", "AL", "ZN", "NI", "AU", "AG",
    "SC", "FU", "TA", "MA", "PP", "M", "Y", "P", "C", "CF", "SR",
]

# 主力合约号映射 (展示用; 实盘应由 MainContractResolver 动态推算)。
# 这里给一个静态近月作为默认展示, 取不到实时主力时回退。
DEFAULT_MAIN_CONTRACT: Dict[str, str] = {
    "RB": "RB2510", "HC": "HC2510", "I": "I2509", "CU": "CU2510",
    "AL": "AL2510", "ZN": "ZN2510", "NI": "NI2510", "AU": "AU2512",
    "AG": "AG2512", "SC": "SC2508", "FU": "FU2509", "TA": "TA2509",
    "MA": "MA2509", "PP": "PP2509", "M": "M2509", "Y": "Y2509",
    "P": "P2509", "C": "C2509", "CF": "CF2509", "SR": "SR2509",
}

# 宏观指标 → 品种关联度 (规则引擎, 非 ML)。
# 正值=正相关 (指标升→品种偏多), 负值=负相关。区间 [-1, 1]。
MACRO_PRODUCT_LINKAGE: Dict[str, Dict[str, float]] = {
    "PMI": {"RB": 0.62, "HC": 0.60, "I": 0.58, "CU": 0.71, "AL": 0.55,
            "ZN": 0.50, "NI": 0.48, "PP": 0.40, "TA": 0.38},
    "M2": {"RB": 0.55, "HC": 0.52, "I": 0.50, "CU": 0.45, "AU": 0.35, "AG": 0.40},
    "CPI": {"M": 0.55, "Y": 0.52, "P": 0.50, "C": 0.48, "CF": 0.45, "SR": 0.50, "AU": 0.42},
    "PPI": {"RB": 0.58, "HC": 0.56, "CU": 0.54, "TA": 0.50, "MA": 0.48, "PP": 0.46},
    "GDP": {"CU": 0.60, "RB": 0.52, "I": 0.50, "NI": 0.45, "AL": 0.44},
    "LPR1Y": {"RB": -0.40, "HC": -0.38, "I": -0.35, "AU": 0.30},  # 利率升→工业品偏空, 黄金分化
}

# 新闻关键词 → 品种标签 (用于给快讯打品种标签)
NEWS_KEYWORD_TAGS: Dict[str, List[str]] = {
    "螺纹": ["RB"], "螺纹钢": ["RB"], "钢材": ["RB", "HC"], "热卷": ["HC"],
    "铁矿": ["I"], "铁矿石": ["I"], "焦炭": ["I"], "焦煤": ["I"],
    "铜": ["CU"], "沪铜": ["CU"], "电解铜": ["CU"], "铝": ["AL"], "沪铝": ["AL"],
    "锌": ["ZN"], "镍": ["NI"], "铅": ["PB"], "锡": ["SN"],
    "黄金": ["AU"], "金价": ["AU"], "白银": ["AG"], "贵金属": ["AU", "AG"],
    "原油": ["SC"], "石油": ["SC"], "OPEC": ["SC"], "燃油": ["FU"],
    "PTA": ["TA"], "甲醇": ["MA"], "聚丙烯": ["PP"], "塑料": ["PP"],
    "豆粕": ["M"], "大豆": ["M", "Y"], "豆油": ["Y"], "棕榈": ["P"], "棕榈油": ["P"],
    "玉米": ["C"], "棉花": ["CF"], "白糖": ["SR"], "农产品": ["M", "Y", "C", "CF", "SR"],
    "美联储": ["AU", "AG", "CU"], "加息": ["AU", "AG"], "降息": ["AU", "AG", "CU"],
    "降准": ["RB", "HC", "CU"], "房地产": ["RB", "HC", "I"], "基建": ["RB", "HC", "CU"],
}


def linkage_for_product(product: str) -> Dict[str, float]:
    """反查某品种受哪些宏观指标影响及关联度。"""
    out: Dict[str, float] = {}
    for indicator, mapping in MACRO_PRODUCT_LINKAGE.items():
        if product.upper() in mapping:
            out[indicator] = mapping[product.upper()]
    return out
