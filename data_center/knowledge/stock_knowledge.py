"""
股票知识库 — 申万行业板块 + 行业↔期货联动映射。

定位 (知识库升级方案 §四):
- 期货夜盘 → 次日 A 股哪个板块受益 (铁矿涨 → 钢铁板块)
- A 股板块暴涨 → 期货端套利机会 (光伏暴涨 → 纯碱/白银)
- 宏观数据 → 影响哪些行业 (PMI 超预期 → 周期股+黑色系共振)

是描述性知识层 (静态结构化), 信号计算复用既有 cross_market.py / oifactors.py。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SectorInfo:
    """申万一级行业板块知识。"""
    code: str                          # 申万行业代码 如 '801040'
    name: str                          # 行业名 如 '钢铁'
    index_code: str                    # 对应行业指数 如 '801040.SI'
    chars: List[str] = field(default_factory=list)            # 波动特点
    related_futures: List[str] = field(default_factory=list)  # 关联期货品种
    macro_sensitivity: Dict[str, float] = field(default_factory=dict)
    seasonality: List[Dict] = field(default_factory=list)
    leading_stocks: List[str] = field(default_factory=list)   # 板块龙头股


@dataclass
class StockFuturesRelation:
    """股票行业 ↔ 期货联动关系。"""
    sector: str                        # 行业名
    futures_symbols: List[str]         # 关联期货代码
    correlation: float                 # 历史相关性 (经验值, 实测由 cross_market 回填)
    lead_lag: str                      # '期货领先' / '股票领先' / '同步'
    logic: str                         # 联动逻辑描述


class StockKnowledgeBase:
    """A 股行业板块知识库 + 行业-期货联动映射。"""

    def __init__(self) -> None:
        self._sectors: Dict[str, SectorInfo] = self._build_sectors()
        self._relations: List[StockFuturesRelation] = self._build_relations()

    def _build_sectors(self) -> Dict[str, SectorInfo]:
        s: Dict[str, SectorInfo] = {}
        s["钢铁"] = SectorInfo(
            "801040", "钢铁", "801040.SI",
            chars=["强周期", "滞后期货1-3天", "受地产/基建投资驱动"],
            related_futures=["RB", "HC", "I", "J", "JM"],
            macro_sensitivity={"PMI": 0.8, "房地产投资": 0.85, "社融": 0.6},
            seasonality=[{"month": 3, "direction": "涨", "strength": 0.6, "reason": "金三银四"}],
            leading_stocks=["600019.SH", "000709.SZ", "600022.SH"],
        )
        s["有色金属"] = SectorInfo(
            "801050", "有色金属", "801050.SI",
            chars=["强周期", "与外盘联动", "对美元/全球需求敏感"],
            related_futures=["CU", "AL", "ZN", "NI", "AU", "AG"],
            macro_sensitivity={"PMI": 0.8, "美元指数": 0.85, "全球制造业PMI": 0.8},
            seasonality=[{"month": 4, "direction": "涨", "strength": 0.5, "reason": "消费旺季"}],
            leading_stocks=["601899.SH", "603993.SH", "600362.SH"],
        )
        s["化工"] = SectorInfo(
            "801030", "基础化工", "801030.SI",
            chars=["与原油/煤炭成本联动", "细分品种多"],
            related_futures=["MA", "TA", "L", "PP", "SA", "FG", "EG"],
            macro_sensitivity={"PMI": 0.7, "原油": 0.75},
            leading_stocks=["600309.SH", "000301.SZ"],
        )
        s["煤炭"] = SectorInfo(
            "801950", "煤炭", "801950.SI",
            chars=["高股息", "受动力煤/焦煤价格驱动", "冬季旺季"],
            related_futures=["ZC", "JM", "J"],
            macro_sensitivity={"工业增加值": 0.7, "PMI": 0.6},
            seasonality=[{"month": 11, "direction": "涨", "strength": 0.6, "reason": "冬储旺季"}],
            leading_stocks=["601088.SH", "601225.SH"],
        )
        s["农业"] = SectorInfo(
            "801010", "农林牧渔", "801010.SI",
            chars=["养殖周期主导", "受猪价/饲料成本影响"],
            related_futures=["M", "Y", "C", "RM", "JD", "LH"],
            macro_sensitivity={"CPI": 0.7, "生猪存栏": 0.8},
            leading_stocks=["000876.SZ", "300498.SZ"],
        )
        s["石油石化"] = SectorInfo(
            "801960", "石油石化", "801960.SI",
            chars=["与原油价格强相关", "高股息蓝筹"],
            related_futures=["SC", "FU", "BU"],
            macro_sensitivity={"原油": 0.9, "美元指数": 0.5},
            leading_stocks=["601857.SH", "600028.SH"],
        )
        s["建材"] = SectorInfo(
            "801710", "建筑材料", "801710.SI",
            chars=["地产链", "玻璃/水泥受地产竣工驱动"],
            related_futures=["FG", "SA", "RB"],
            macro_sensitivity={"房地产投资": 0.8, "竣工面积": 0.75},
            leading_stocks=["600585.SH", "000786.SZ"],
        )
        return s

    def _build_relations(self) -> List[StockFuturesRelation]:
        return [
            StockFuturesRelation("钢铁", ["RB", "HC", "I", "J"], 0.80, "期货领先",
                "黑色期货夜盘走势 → 次日钢铁板块开盘方向; 钢铁股通常滞后期货1-3天"),
            StockFuturesRelation("有色金属", ["CU", "AL", "NI"], 0.85, "期货领先",
                "沪铜/沪铝夜盘跟随LME → 次日有色板块; 外盘是核心驱动"),
            StockFuturesRelation("煤炭", ["ZC", "JM", "J"], 0.70, "同步",
                "动力煤/焦煤价格 ↔ 煤炭股, 受电力需求与产地政策共同驱动"),
            StockFuturesRelation("化工", ["MA", "TA", "L", "PP"], 0.65, "期货领先",
                "化工期货反映成本与供需 → 化工股盈利预期"),
            StockFuturesRelation("农业", ["M", "Y", "JD", "LH"], 0.60, "期货领先",
                "豆粕/生猪期货 → 养殖与种植股成本/利润预期"),
            StockFuturesRelation("石油石化", ["SC", "FU"], 0.75, "同步",
                "原油价格 ↔ 石化股, 中石油/中石化与油价高度相关"),
            StockFuturesRelation("建材", ["FG", "SA"], 0.70, "期货领先",
                "玻璃/纯碱期货 → 地产竣工链建材股"),
        ]

    # ---- 查询接口 ----------------------------------------------------------
    def get_sector(self, name: str) -> Optional[SectorInfo]:
        return self._sectors.get(name)

    def list_sectors(self) -> List[SectorInfo]:
        return list(self._sectors.values())

    def relations_for_sector(self, sector: str) -> List[StockFuturesRelation]:
        return [r for r in self._relations if r.sector == sector]

    def sectors_for_futures(self, futures_symbol: str) -> List[str]:
        """某期货品种关联的股票行业 (期货 → 股票方向)。"""
        fs = futures_symbol.upper()
        return [s.name for s in self._sectors.values() if fs in s.related_futures]

    def all_relations(self) -> List[StockFuturesRelation]:
        return list(self._relations)


_kb: Optional[StockKnowledgeBase] = None


def get_stock_knowledge() -> StockKnowledgeBase:
    global _kb
    if _kb is None:
        _kb = StockKnowledgeBase()
    return _kb
