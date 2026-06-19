"""
合约知识库 — 中国期货市场品种完整信息。
包含: 交易所 / 合约乘数 / 最小变动 / 交易时间 /
      保证金比例 / 手续费(开仓/平仓/平今) / 涨跌停 / 交割月份
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ContractDetail:
    """合约品种详细信息"""
    symbol: str
    exchange: str
    exchange_cn: str
    name_cn: str
    name_en: str
    contract_multiplier: int
    min_tick: float
    trading_hours: str
    night_trading: str
    margin_rate: float
    commission_open: float           # 开仓手续费 (元/手 或 比例)
    commission_close: float          # 平仓手续费
    commission_close_today: float    # 平今手续费
    commission_type: str            # "fixed" 固定金额 / "ratio" 比例
    price_limit_pct: float          # 涨跌停板 %
    delivery_months: List[int]      # 交割月份
    category: str                   # 分类
    listed_year: int = 2000
    is_commodity: bool = True
    is_agricultural: bool = False
    is_metal: bool = False
    is_energy: bool = False
    is_chemical: bool = False
    is_financial: bool = False

    # 🆕 结构化知识层 — 供评分引擎/agent 量化引用 (全部默认空, 渐进填充)
    macro_sensitivity: Dict[str, float] = field(default_factory=dict)
    # 宏观敏感度 {"PMI":0.8,"美元指数":0.9}; 决定宏观信号对该品种的权重
    seasonality: List[Dict] = field(default_factory=list)
    # 季节性 [{"month":9,"direction":"涨","strength":0.6,"reason":"金九银十"}]
    data_releases: List[str] = field(default_factory=list)
    # 关注的数据发布 ["每周四钢联数据","每月USDA报告"]
    key_indicators: Dict[str, str] = field(default_factory=dict)
    # 核心基本面指标 {"库存":"港口库存+钢厂库存","开工率":"高炉开工率"}
    related_products: List[str] = field(default_factory=list)
    # 强关联品种 ["HC","I"] (卷螺/螺矿)

    @property
    def exchange_display(self) -> str:
        exchange_names = {
            "SHFE": "上海期货交易所",
            "DCE": "大连商品交易所",
            "CZCE": "郑州商品交易所",
            "CFFEX": "中国金融期货交易所",
            "INE": "上海国际能源交易中心",
            "GFEX": "广州期货交易所",
        }
        return exchange_names.get(self.exchange, self.exchange)


class ContractKnowledgeBase:
    """
    中国期货市场合约知识库。
    
    覆盖 6 大交易所 70+ 品种:
    - SHFE (上期所): 铜铝锌铅镍锡金银螺纹钢等
    - DCE (大商所): 豆粕豆油玉米铁矿石焦炭等
    - CZCE (郑商所): 白糖棉花PTA甲醇纯碱等
    - CFFEX (中金所): IF/IH/IC/IM/T/TF/TS
    - INE (能源中心): 原油/20号胶/低硫燃油/国际铜
    - GFEX (广期所): 工业硅/碳酸锂
    
    包含: 手续费、保证金、交易时间、合约规则
    """

    def __init__(self):
        self._contracts: Dict[str, ContractDetail] = self._build_database()

    def _build_database(self) -> Dict[str, ContractDetail]:
        """构建完整的合约知识库"""
        contracts = {}

        # ==================== 上海期货交易所 (SHFE) ====================
        contracts["CU"] = ContractDetail("CU", "SHFE", "上海期货交易所",
            "沪铜", "Copper", 5, 10, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-01:00", 0.12, 0.00005, 0.00005, 0.0001, "ratio", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "金属", is_metal=True)
        
        contracts["AL"] = ContractDetail("AL", "SHFE", "上海期货交易所",
            "沪铝", "Aluminum", 5, 5, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-01:00", 0.12, 3.0, 3.0, 3.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "金属", is_metal=True)
        
        contracts["ZN"] = ContractDetail("ZN", "SHFE", "上海期货交易所",
            "沪锌", "Zinc", 5, 5, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-01:00", 0.12, 3.0, 3.0, 0.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "金属", is_metal=True)
        
        contracts["PB"] = ContractDetail("PB", "SHFE", "上海期货交易所",
            "沪铅", "Lead", 5, 5, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-01:00", 0.12, 3.0, 3.0, 0.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "金属", is_metal=True)
        
        contracts["NI"] = ContractDetail("NI", "SHFE", "上海期货交易所",
            "沪镍", "Nickel", 1, 10, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-01:00", 0.15, 3.0, 3.0, 0.0, "fixed", 0.10,
            [1,2,3,4,5,6,7,8,9,10,11,12], "金属", is_metal=True)
        
        contracts["SN"] = ContractDetail("SN", "SHFE", "上海期货交易所",
            "沪锡", "Tin", 1, 10, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-01:00", 0.14, 3.0, 3.0, 0.0, "fixed", 0.10,
            [1,2,3,4,5,6,7,8,9,10,11,12], "金属", is_metal=True)
        
        contracts["AU"] = ContractDetail("AU", "SHFE", "上海期货交易所",
            "黄金", "Gold", 1000, 0.02, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-02:30", 0.12, 10.0, 10.0, 0.0, "fixed", 0.06,
            [1,2,3,4,5,6,7,8,9,10,11,12], "贵金属", is_metal=True)
        
        contracts["AG"] = ContractDetail("AG", "SHFE", "上海期货交易所",
            "白银", "Silver", 15, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-02:30", 0.12, 0.00001, 0.00001, 0.00001, "ratio", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "贵金属", is_metal=True)
        
        contracts["RB"] = ContractDetail("RB", "SHFE", "上海期货交易所",
            "螺纹钢", "Rebar", 10, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 0.00001, 0.00001, 0.00002, "ratio", 0.06,
            [1,2,3,4,5,6,7,8,9,10,11,12], "钢铁")
        
        contracts["HC"] = ContractDetail("HC", "SHFE", "上海期货交易所",
            "热轧卷板", "Hot Coil", 10, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 0.00001, 0.00001, 0.00003, "ratio", 0.06,
            [1,2,3,4,5,6,7,8,9,10,11,12], "钢铁")
        
        contracts["RU"] = ContractDetail("RU", "SHFE", "上海期货交易所",
            "天然橡胶", "Rubber", 10, 5, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 3.0, 3.0, 0.0, "fixed", 0.07,
            [1,3,4,5,6,7,8,9,10,11], "化工", is_chemical=True)
        
        contracts["BU"] = ContractDetail("BU", "SHFE", "上海期货交易所",
            "石油沥青", "Bitumen", 10, 2, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.15, 0.00001, 0.00001, 0.00001, "ratio", 0.08,
            [1,2,3,4,5,6,7,8,9,10,11,12], "能源", is_energy=True)
        
        contracts["SP"] = ContractDetail("SP", "SHFE", "上海期货交易所",
            "纸浆", "Pulp", 10, 2, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 0.00005, 0.00005, 0.00005, "ratio", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "造纸")
        
        contracts["SS"] = ContractDetail("SS", "SHFE", "上海期货交易所",
            "不锈钢", "Stainless", 5, 5, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-01:00", 0.12, 2.0, 2.0, 0.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "钢铁")
        
        # ==================== 大连商品交易所 (DCE) ====================
        contracts["M"] = ContractDetail("M", "DCE", "大连商品交易所",
            "豆粕", "Soybean Meal", 10, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 1.5, 1.5, 1.5, "fixed", 0.06,
            [1,3,5,7,8,9,11,12], "农产品", is_agricultural=True)
        
        contracts["Y"] = ContractDetail("Y", "DCE", "大连商品交易所",
            "豆油", "Soybean Oil", 10, 2, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.10, 2.5, 2.5, 1.25, "fixed", 0.06,
            [1,3,5,7,8,9,11,12], "农产品", is_agricultural=True)
        
        contracts["P"] = ContractDetail("P", "DCE", "大连商品交易所",
            "棕榈油", "Palm Oil", 10, 2, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 2.5, 2.5, 1.25, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "农产品", is_agricultural=True)
        
        contracts["A"] = ContractDetail("A", "DCE", "大连商品交易所",
            "豆一", "Soybean No.1", 10, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 2.0, 2.0, 2.0, "fixed", 0.06,
            [1,3,5,7,9,11], "农产品", is_agricultural=True)
        
        contracts["C"] = ContractDetail("C", "DCE", "大连商品交易所",
            "玉米", "Corn", 10, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 1.2, 1.2, 1.2, "fixed", 0.06,
            [1,3,5,7,9,11], "农产品", is_agricultural=True)
        
        contracts["I"] = ContractDetail("I", "DCE", "大连商品交易所",
            "铁矿石", "Iron Ore", 100, 0.5, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.16, 0.0001, 0.0001, 0.0001, "ratio", 0.10,
            [1,2,3,4,5,6,7,8,9,10,11,12], "钢铁")
        
        contracts["J"] = ContractDetail("J", "DCE", "大连商品交易所",
            "焦炭", "Coke", 100, 0.5, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.20, 0.0001, 0.0001, 0.00014, "ratio", 0.08,
            [1,2,3,4,5,6,7,8,9,10,11,12], "能源", is_energy=True)
        
        contracts["JM"] = ContractDetail("JM", "DCE", "大连商品交易所",
            "焦煤", "Coking Coal", 60, 0.5, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.20, 0.0001, 0.0001, 0.00014, "ratio", 0.08,
            [1,2,3,4,5,6,7,8,9,10,11,12], "能源", is_energy=True)
        
        contracts["L"] = ContractDetail("L", "DCE", "大连商品交易所",
            "LLDPE", "LLDPE", 5, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 1.0, 1.0, 1.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "化工", is_chemical=True)
        
        contracts["PP"] = ContractDetail("PP", "DCE", "大连商品交易所",
            "聚丙烯", "PP", 5, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 1.0, 1.0, 1.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "化工", is_chemical=True)
        
        contracts["V"] = ContractDetail("V", "DCE", "大连商品交易所",
            "PVC", "PVC", 5, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 1.0, 1.0, 1.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "化工", is_chemical=True)
        
        contracts["EG"] = ContractDetail("EG", "DCE", "大连商品交易所",
            "乙二醇", "EG", 10, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 3.0, 3.0, 1.5, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "化工", is_chemical=True)
        
        contracts["PG"] = ContractDetail("PG", "DCE", "大连商品交易所",
            "液化石油气", "LPG", 20, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 6.0, 6.0, 6.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "能源", is_energy=True)
        
        contracts["LH"] = ContractDetail("LH", "DCE", "大连商品交易所",
            "生猪", "Live Hog", 16, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "无夜盘", 0.15, 0.0002, 0.0002, 0.0004, "ratio", 0.08,
            [1,3,5,7,9,11], "农产品", is_agricultural=True)
        
        contracts["JD"] = ContractDetail("JD", "DCE", "大连商品交易所",
            "鸡蛋", "Egg", 5, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "无夜盘", 0.12, 0.00015, 0.00015, 0.00015, "ratio", 0.06,
            [1,2,3,4,5,6,7,8,9,10,11,12], "农产品", is_agricultural=True)
        
        # ==================== 郑州商品交易所 (CZCE) ====================
        contracts["SR"] = ContractDetail("SR", "CZCE", "郑州商品交易所",
            "白糖", "Sugar", 10, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.10, 3.0, 3.0, 0.0, "fixed", 0.06,
            [1,3,5,7,9,11], "农产品", is_agricultural=True)
        
        contracts["CF"] = ContractDetail("CF", "CZCE", "郑州商品交易所",
            "棉花", "Cotton", 5, 5, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.10, 4.3, 4.3, 0.0, "fixed", 0.06,
            [1,3,5,7,9,11], "农产品", is_agricultural=True)
        
        contracts["TA"] = ContractDetail("TA", "CZCE", "郑州商品交易所",
            "PTA", "PTA", 5, 2, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.10, 3.0, 3.0, 0.0, "fixed", 0.06,
            [1,2,3,4,5,6,7,8,9,10,11,12], "化工", is_chemical=True)
        
        contracts["MA"] = ContractDetail("MA", "CZCE", "郑州商品交易所",
            "甲醇", "Methanol", 10, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.10, 2.0, 2.0, 6.0, "fixed", 0.06,
            [1,2,3,4,5,6,7,8,9,10,11,12], "化工", is_chemical=True)
        
        contracts["FG"] = ContractDetail("FG", "CZCE", "郑州商品交易所",
            "玻璃", "Glass", 20, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 6.0, 6.0, 6.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "建材")
        
        contracts["RM"] = ContractDetail("RM", "CZCE", "郑州商品交易所",
            "菜籽粕", "Rapeseed Meal", 10, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.10, 1.5, 1.5, 1.5, "fixed", 0.06,
            [1,3,5,7,9,11], "农产品", is_agricultural=True)
        
        contracts["OI"] = ContractDetail("OI", "CZCE", "郑州商品交易所",
            "菜籽油", "Rapeseed Oil", 10, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.10, 2.0, 2.0, 2.0, "fixed", 0.06,
            [1,3,5,7,9,11], "农产品", is_agricultural=True)
        
        contracts["ZC"] = ContractDetail("ZC", "CZCE", "郑州商品交易所",
            "动力煤", "Thermal Coal", 100, 0.2, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.15, 0.0004, 0.0004, 0.0004, "ratio", 0.10,
            [1,2,3,4,5,6,7,8,9,10,11,12], "能源", is_energy=True)
        
        contracts["SA"] = ContractDetail("SA", "CZCE", "郑州商品交易所",
            "纯碱", "Soda Ash", 20, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 3.5, 3.5, 0.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "化工", is_chemical=True)
        
        contracts["UR"] = ContractDetail("UR", "CZCE", "郑州商品交易所",
            "尿素", "Urea", 20, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "无夜盘", 0.12, 5.0, 5.0, 5.0, "fixed", 0.06,
            [1,2,3,4,5,6,7,8,9,10,11,12], "化工", is_chemical=True)
        
        contracts["AP"] = ContractDetail("AP", "CZCE", "郑州商品交易所",
            "苹果", "Apple", 10, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "无夜盘", 0.12, 5.0, 5.0, 20.0, "fixed", 0.06,
            [1,3,4,5,10,11,12], "农产品", is_agricultural=True)
        
        contracts["PK"] = ContractDetail("PK", "CZCE", "郑州商品交易所",
            "花生", "Peanut", 5, 2, "9:00-10:15/10:30-11:30/13:30-15:00",
            "无夜盘", 0.12, 4.0, 4.0, 4.0, "fixed", 0.07,
            [1,3,4,10,11,12], "农产品", is_agricultural=True)
        
        contracts["CJ"] = ContractDetail("CJ", "CZCE", "郑州商品交易所",
            "红枣", "Jujube", 5, 5, "9:00-10:15/10:30-11:30/13:30-15:00",
            "无夜盘", 0.12, 3.0, 3.0, 3.0, "fixed", 0.05,
            [1,3,5,7,9,12], "农产品", is_agricultural=True)
        
        contracts["SF"] = ContractDetail("SF", "CZCE", "郑州商品交易所",
            "硅铁", "Si-Fe", 5, 2, "9:00-10:15/10:30-11:30/13:30-15:00",
            "无夜盘", 0.12, 3.0, 3.0, 0.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "钢铁")
        
        contracts["SM"] = ContractDetail("SM", "CZCE", "郑州商品交易所",
            "锰硅", "Mn-Si", 5, 2, "9:00-10:15/10:30-11:30/13:30-15:00",
            "无夜盘", 0.12, 3.0, 3.0, 0.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "钢铁")
        
        # ==================== 中国金融期货交易所 (CFFEX) ====================
        contracts["IF"] = ContractDetail("IF", "CFFEX", "中国金融期货交易所",
            "沪深300指数", "CSI 300 Index", 300, 0.2,
            "9:30-11:30/13:00-15:00", "无夜盘", 0.12,
            0.000023, 0.000023, 0.000345, "ratio", 0.10,
            [1,2,3,4,5,6,7,8,9,10,11,12], "金融",
            is_financial=True, is_commodity=False)
        
        contracts["IH"] = ContractDetail("IH", "CFFEX", "中国金融期货交易所",
            "上证50指数", "SSE 50 Index", 300, 0.2,
            "9:30-11:30/13:00-15:00", "无夜盘", 0.12,
            0.000023, 0.000023, 0.000345, "ratio", 0.10,
            [1,2,3,4,5,6,7,8,9,10,11,12], "金融",
            is_financial=True, is_commodity=False)
        
        contracts["IC"] = ContractDetail("IC", "CFFEX", "中国金融期货交易所",
            "中证500指数", "CSI 500 Index", 200, 0.2,
            "9:30-11:30/13:00-15:00", "无夜盘", 0.12,
            0.000023, 0.000023, 0.000345, "ratio", 0.10,
            [1,2,3,4,5,6,7,8,9,10,11,12], "金融",
            is_financial=True, is_commodity=False)
        
        contracts["IM"] = ContractDetail("IM", "CFFEX", "中国金融期货交易所",
            "中证1000指数", "CSI 1000 Index", 200, 0.2,
            "9:30-11:30/13:00-15:00", "无夜盘", 0.12,
            0.000023, 0.000023, 0.000345, "ratio", 0.10,
            [1,2,3,4,5,6,7,8,9,10,11,12], "金融",
            is_financial=True, is_commodity=False)
        
        contracts["T"] = ContractDetail("T", "CFFEX", "中国金融期货交易所",
            "10年期国债", "10Y Treasury", 10000, 0.005,
            "9:30-11:30/13:00-15:15", "无夜盘", 0.02,
            3.0, 3.0, 3.0, "fixed", 0.02,
            [3,6,9,12], "金融", is_financial=True, is_commodity=False)
        
        contracts["TF"] = ContractDetail("TF", "CFFEX", "中国金融期货交易所",
            "5年期国债", "5Y Treasury", 10000, 0.005,
            "9:30-11:30/13:00-15:15", "无夜盘", 0.012,
            3.0, 3.0, 3.0, "fixed", 0.012,
            [3,6,9,12], "金融", is_financial=True, is_commodity=False)
        
        # ==================== 上海国际能源交易中心 (INE) ====================
        contracts["SC"] = ContractDetail("SC", "INE", "上海国际能源交易中心",
            "原油", "Crude Oil", 1000, 0.1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-02:30", 0.15, 20.0, 20.0, 0.0, "fixed", 0.08,
            [1,2,3,4,5,6,7,8,9,10,11,12], "能源", is_energy=True)
        
        contracts["NR"] = ContractDetail("NR", "INE", "上海国际能源交易中心",
            "20号胶", "Rubber 20", 10, 5, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 3.0, 3.0, 0.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "化工", is_chemical=True)
        
        contracts["LU"] = ContractDetail("LU", "INE", "上海国际能源交易中心",
            "低硫燃料油", "LSFO", 10, 1, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.15, 0.00001, 0.00001, 0.00001, "ratio", 0.08,
            [1,2,3,4,5,6,7,8,9,10,11,12], "能源", is_energy=True)
        
        contracts["BC"] = ContractDetail("BC", "INE", "上海国际能源交易中心",
            "国际铜", "Copper(BC)", 5, 10, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-01:00", 0.12, 0.00001, 0.00001, 0.0, "ratio", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "金属", is_metal=True)
        
        # ==================== 广州期货交易所 (GFEX) ====================
        contracts["SI"] = ContractDetail("SI", "GFEX", "广州期货交易所",
            "工业硅", "Si", 5, 5, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 5.0, 5.0, 5.0, "fixed", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "金属", is_metal=True)
        
        contracts["LC"] = ContractDetail("LC", "GFEX", "广州期货交易所",
            "碳酸锂", "Li Carbonate", 1, 50, "9:00-10:15/10:30-11:30/13:30-15:00",
            "21:00-23:00", 0.12, 0.00008, 0.00008, 0.0, "ratio", 0.07,
            [1,2,3,4,5,6,7,8,9,10,11,12], "金属", is_metal=True)

        self._enrich_knowledge(contracts)
        return contracts

    @staticmethod
    def _enrich_knowledge(contracts: Dict[str, "ContractDetail"]) -> None:
        """为代表性品种填充结构化知识 (宏观敏感度/季节性/核心指标/关联)。
        渐进填充: 未覆盖的品种字段保持空, agent 可按需补充。"""
        enrich = {
            "RB": {
                "macro_sensitivity": {"PMI": 0.8, "社融": 0.6, "房地产投资": 0.85, "美元指数": 0.3},
                "seasonality": [
                    {"month": 3, "direction": "涨", "strength": 0.7, "reason": "金三银四开工旺季"},
                    {"month": 9, "direction": "涨", "strength": 0.6, "reason": "金九银十需求回升"},
                ],
                "data_releases": ["每周四Mysteel钢联数据", "每月制造业PMI", "每月房地产投资数据"],
                "key_indicators": {"库存": "钢厂库存+社会库存", "开工率": "高炉开工率",
                                   "利润": "螺纹钢生产利润", "需求": "表观消费量"},
                "related_products": ["HC", "I", "J", "JM"],
            },
            "HC": {
                "macro_sensitivity": {"PMI": 0.8, "制造业投资": 0.75, "美元指数": 0.3},
                "seasonality": [{"month": 3, "direction": "涨", "strength": 0.6, "reason": "制造业旺季"}],
                "data_releases": ["每周四Mysteel钢联数据", "每月制造业PMI"],
                "key_indicators": {"库存": "热卷社库", "需求": "制造业/汽车产量"},
                "related_products": ["RB", "I"],
            },
            "I": {
                "macro_sensitivity": {"PMI": 0.75, "房地产投资": 0.8, "美元指数": 0.4},
                "seasonality": [{"month": 9, "direction": "涨", "strength": 0.5, "reason": "补库旺季"}],
                "data_releases": ["每周港口铁矿石库存", "澳巴发运数据"],
                "key_indicators": {"库存": "45港铁矿石库存", "供应": "澳巴发运量", "需求": "铁水产量"},
                "related_products": ["RB", "HC", "J"],
            },
            "CU": {
                "macro_sensitivity": {"PMI": 0.85, "美元指数": 0.9, "社融": 0.5, "全球制造业PMI": 0.8},
                "seasonality": [{"month": 4, "direction": "涨", "strength": 0.5, "reason": "传统消费旺季"}],
                "data_releases": ["LME库存日报", "每月SMM社会库存", "美联储议息"],
                "key_indicators": {"库存": "LME+上期所+保税区库存", "升贴水": "现货升贴水",
                                   "加工费": "铜精矿TC/RC"},
                "related_products": ["AL", "ZN", "NI"],
            },
            "AU": {
                "macro_sensitivity": {"美元指数": 0.9, "美债实际利率": 0.95, "VIX": 0.6, "通胀预期": 0.7},
                "seasonality": [{"month": 1, "direction": "涨", "strength": 0.4, "reason": "避险+印度购金"}],
                "data_releases": ["美联储议息", "美国CPI", "非农就业", "美债收益率"],
                "key_indicators": {"驱动": "实际利率(名义利率-通胀)", "避险": "地缘风险/VIX",
                                   "持仓": "SPDR黄金ETF持仓"},
                "related_products": ["AG"],
            },
            "M": {
                "macro_sensitivity": {"美元指数": 0.5, "厄尔尼诺": 0.6, "生猪存栏": 0.7},
                "seasonality": [
                    {"month": 7, "direction": "涨", "strength": 0.6, "reason": "美豆天气炒作"},
                    {"month": 11, "direction": "跌", "strength": 0.5, "reason": "南美丰产预期"},
                ],
                "data_releases": ["每月USDA供需报告", "每周出口销售", "南美天气"],
                "key_indicators": {"供应": "美豆/巴西大豆产量", "需求": "生猪存栏+压榨利润",
                                   "库存": "港口大豆库存"},
                "related_products": ["Y", "RM", "OI"],
            },
        }
        for sym, kn in enrich.items():
            c = contracts.get(sym)
            if c is None:
                continue
            c.macro_sensitivity = kn.get("macro_sensitivity", {})
            c.seasonality = kn.get("seasonality", [])
            c.data_releases = kn.get("data_releases", [])
            c.key_indicators = kn.get("key_indicators", {})
            c.related_products = kn.get("related_products", [])

    def get_contract(self, symbol: str) -> Optional[ContractDetail]:
        """获取合约品种信息"""
        return self._contracts.get(symbol.upper())

    def list_all_symbols(self) -> List[str]:
        """列出所有支持的品种代码"""
        return sorted(self._contracts.keys())

    def list_by_exchange(self, exchange: str) -> List[ContractDetail]:
        """按交易所列出品种"""
        return [c for c in self._contracts.values() if c.exchange == exchange.upper()]

    def list_by_category(self, category: str) -> List[ContractDetail]:
        """按分类列出品种"""
        return [c for c in self._contracts.values() if c.category == category]

    def search(self, keyword: str) -> List[ContractDetail]:
        """搜索品种 (支持中文名/代码/交易所)"""
        kw = keyword.upper()
        results = []
        for c in self._contracts.values():
            if (kw in c.symbol or kw in c.name_cn or kw in c.name_en.upper()
                or kw in c.exchange or kw in c.category):
                results.append(c)
        return results

    def get_exchange_summary(self, exchange: str) -> Dict:
        """获取交易所汇总信息"""
        contracts = self.list_by_exchange(exchange)
        return {
            "exchange": exchange,
            "exchange_cn": contracts[0].exchange_cn if contracts else exchange,
            "total_contracts": len(contracts),
            "categories": list(set(c.category for c in contracts)),
            "contracts": [c.symbol for c in contracts],
        }

    def get_all_exchanges(self) -> List[Dict]:
        """获取所有交易所汇总"""
        exchanges = {}
        for c in self._contracts.values():
            if c.exchange not in exchanges:
                exchanges[c.exchange] = set()
            exchanges[c.exchange].add(c.symbol)
        return [
            {"exchange": ex, "exchange_cn": self._contracts[list(syms)[0]].exchange_cn,
             "count": len(syms), "symbols": sorted(syms)}
            for ex, syms in exchanges.items()
        ]
