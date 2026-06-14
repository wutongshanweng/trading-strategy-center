"""
交易所信息模块 — 中国期货交易所基本信息。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ExchangeInfo:
    """交易所信息"""
    code: str
    name_cn: str
    name_en: str
    city: str
    website: str
    futures_count: int = 0


# 中国期货交易所列表
EXCHANGES: Dict[str, ExchangeInfo] = {
    "SHFE": ExchangeInfo("SHFE", "上海期货交易所", "Shanghai Futures Exchange",
                         "上海", "https://www.shfe.com.cn", 16),
    "DCE": ExchangeInfo("DCE", "大连商品交易所", "Dalian Commodity Exchange",
                        "大连", "https://www.dce.com.cn", 21),
    "CZCE": ExchangeInfo("CZCE", "郑州商品交易所", "Zhengzhou Commodity Exchange",
                         "郑州", "http://www.czce.com.cn", 23),
    "CFFEX": ExchangeInfo("CFFEX", "中国金融期货交易所", "China Financial Futures Exchange",
                          "上海", "http://www.cffex.com.cn", 10),
    "INE": ExchangeInfo("INE", "上海国际能源交易中心", "Shanghai International Energy Exchange",
                        "上海", "https://www.ine.cn", 4),
    "GFEX": ExchangeInfo("GFEX", "广州期货交易所", "Guangzhou Futures Exchange",
                         "广州", "https://www.gfex.com.cn", 2),
}


def get_exchange(code: str) -> ExchangeInfo:
    return EXCHANGES.get(code.upper())


def list_exchanges() -> List[ExchangeInfo]:
    return list(EXCHANGES.values())
