"""
期权知识库 — 标的期权市场特征 + 策略描述层 (知识库升级方案 期权部分)。

定位: 描述性知识层。期权的 Greeks/IV/PCR/MaxPain 计算能力已存在
(options/greeks, options/volatility, options/analysis, data_center/options_analytics),
本模块只补"每个标的的期权市场特征"和"策略适用场景"的结构化知识, 供 agent 量化引用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class OptionsProductInfo:
    """每个标的的期权市场特征。"""
    underlying: str                    # 标的代码 '510050'/'IO'/'M'
    underlying_type: str               # 'ETF'/'指数'/'商品'
    exchange: str
    option_category: str               # '金融期权'/'商品期权'
    exercise_style: str                # '欧式'/'美式'
    contract_unit: str = ""            # 合约单位描述
    strike_interval: str = ""          # 行权价间距描述
    iv_range: Tuple[float, float] = (0.0, 0.0)   # IV 常见区间 (min%, max%)
    liquidity: str = "中"              # 流动性 极高/高/中/低
    chars: List[str] = field(default_factory=list)            # 波动/特有现象
    strategy_preferences: List[str] = field(default_factory=list)  # 常用策略
    related_futures: List[str] = field(default_factory=list)  # 商品期权关联期货


@dataclass
class OptionsStrategyInfo:
    """期权策略知识 (描述层, 与 options/strategies 的计算类配对)。"""
    name: str
    chinese_name: str
    setup: str                         # 适用场景
    components: List[str]              # 构成腿
    market_view: str                   # '大涨'/'小涨'/'震荡'/'小跌'/'大跌'
    iv_env: str                        # '低IV'/'高IV'/'IV上升'/'IV下降'
    max_profit: str
    max_loss: str
    greeks_profile: Dict[str, str] = field(default_factory=dict)


class OptionsKnowledgeBase:
    """期权标的特征 + 策略知识库。"""

    def __init__(self) -> None:
        self._products: Dict[str, OptionsProductInfo] = self._build_products()
        self._strategies: Dict[str, OptionsStrategyInfo] = self._build_strategies()

    def _build_products(self) -> Dict[str, OptionsProductInfo]:
        p: Dict[str, OptionsProductInfo] = {}
        p["510050"] = OptionsProductInfo(
            "510050", "ETF", "上交所", "金融期权", "欧式",
            contract_unit="10000份", strike_interval="按价位分档",
            iv_range=(12.0, 35.0), liquidity="极高",
            chars=["到期日效应明显", "周度/月度合约齐全", "大盘风向标"],
            strategy_preferences=["卖跨式赚时间价值", "备兑开仓", "保护性认沽"],
        )
        p["510300"] = OptionsProductInfo(
            "510300", "ETF", "上交所", "金融期权", "欧式",
            iv_range=(13.0, 36.0), liquidity="极高",
            chars=["与沪深300高度相关", "机构对冲常用"],
            strategy_preferences=["领口策略", "备兑开仓"],
        )
        p["IO"] = OptionsProductInfo(
            "IO", "指数", "中金所", "金融期权", "欧式",
            contract_unit="点×100元", iv_range=(13.0, 40.0), liquidity="高",
            chars=["沪深300股指期权", "升贴水转换时IV剧烈波动", "现金交割"],
            strategy_preferences=["波动率交易", "日历价差"],
        )
        p["HO"] = OptionsProductInfo(
            "HO", "指数", "中金所", "金融期权", "欧式",
            iv_range=(13.0, 42.0), liquidity="中",
            chars=["上证50股指期权", "流动性弱于IO"],
            strategy_preferences=["方向性买权"],
        )
        p["M"] = OptionsProductInfo(
            "M", "商品", "大商所", "商品期权", "美式",
            contract_unit="10吨", iv_range=(15.0, 45.0), liquidity="高",
            chars=["豆粕期权", "美式提前行权风险", "USDA报告前IV抬升", "随期货涨跌停联动"],
            strategy_preferences=["事件前买跨式", "卖宽跨赚波动率回落"],
            related_futures=["M"],
        )
        p["RB"] = OptionsProductInfo(
            "RB", "商品", "上期所", "商品期权", "美式",
            contract_unit="10吨", iv_range=(18.0, 50.0), liquidity="中",
            chars=["螺纹钢期权", "美式行权", "黑色系情绪放大器"],
            strategy_preferences=["趋势行情买方", "震荡卖方"],
            related_futures=["RB"],
        )
        p["SR"] = OptionsProductInfo(
            "SR", "商品", "郑商所", "商品期权", "美式",
            contract_unit="10吨", iv_range=(14.0, 40.0), liquidity="中",
            chars=["白糖期权", "美式行权", "季节性供需驱动IV"],
            strategy_preferences=["季节性方向交易"],
            related_futures=["SR"],
        )
        p["CU"] = OptionsProductInfo(
            "CU", "商品", "上期所", "商品期权", "欧式",
            contract_unit="5吨", iv_range=(12.0, 35.0), liquidity="中",
            chars=["铜期权", "欧式行权", "跟随LME与宏观"],
            strategy_preferences=["宏观事件波动率交易"],
            related_futures=["CU"],
        )
        return p

    def _build_strategies(self) -> Dict[str, OptionsStrategyInfo]:
        s: Dict[str, OptionsStrategyInfo] = {}
        s["covered_call"] = OptionsStrategyInfo(
            "covered_call", "备兑开仓", "持有标的多头, 预期小涨或震荡",
            ["long underlying", "short OTM call"], "小涨/震荡", "高IV(赚高权利金)",
            "权利金+(行权价-成本)", "标的下跌亏损-权利金",
            {"delta": "正(0.3~0.5)", "gamma": "负", "vega": "负", "theta": "正"})
        s["protective_put"] = OptionsStrategyInfo(
            "protective_put", "保护性认沽", "持有标的, 担心下跌买保险",
            ["long underlying", "long OTM put"], "看涨但要保护", "低IV(保险便宜)",
            "标的上涨收益-权利金", "权利金(下方有保护)",
            {"delta": "正", "gamma": "正", "vega": "正", "theta": "负"})
        s["long_straddle"] = OptionsStrategyInfo(
            "long_straddle", "买入跨式", "预期大波动但方向不明 (事件前)",
            ["long ATM call", "long ATM put"], "大涨或大跌", "低IV/IV上升",
            "理论无限", "双边权利金",
            {"delta": "约0", "gamma": "正", "vega": "正(强)", "theta": "负(强)"})
        s["short_strangle"] = OptionsStrategyInfo(
            "short_strangle", "卖出宽跨式", "预期震荡, 赚波动率回落+时间价值",
            ["short OTM call", "short OTM put"], "震荡", "高IV/IV下降",
            "双边权利金", "理论无限(需保证金)",
            {"delta": "约0", "gamma": "负", "vega": "负(强)", "theta": "正(强)"})
        s["bull_call_spread"] = OptionsStrategyInfo(
            "bull_call_spread", "牛市看涨价差", "温和看涨, 降低成本",
            ["long ATM call", "short OTM call"], "小涨", "中性",
            "价差-净权利金", "净权利金",
            {"delta": "正", "gamma": "中性", "vega": "中性", "theta": "中性"})
        s["calendar_spread"] = OptionsStrategyInfo(
            "calendar_spread", "日历价差", "近月时间价值衰减快于远月",
            ["short near-month", "long far-month"], "震荡", "近高远低期限结构",
            "受限", "净权利金",
            {"delta": "约0", "gamma": "近负远正", "vega": "正", "theta": "正"})
        return s

    # ---- 查询 ----
    def get_product(self, underlying: str) -> Optional[OptionsProductInfo]:
        return self._products.get(underlying.upper())

    def list_products(self) -> List[OptionsProductInfo]:
        return list(self._products.values())

    def get_strategy(self, name: str) -> Optional[OptionsStrategyInfo]:
        return self._strategies.get(name)

    def list_strategies(self) -> List[OptionsStrategyInfo]:
        return list(self._strategies.values())

    def strategies_for_view(self, market_view: str) -> List[OptionsStrategyInfo]:
        """按市场判断推荐策略 (大涨/小涨/震荡/小跌/大跌)。"""
        return [s for s in self._strategies.values() if market_view in s.market_view]


_kb: Optional[OptionsKnowledgeBase] = None


def get_options_knowledge() -> OptionsKnowledgeBase:
    global _kb
    if _kb is None:
        _kb = OptionsKnowledgeBase()
    return _kb
