"""
主力合约解析器 — 识别当前主力合约、合约号解析。

核心功能:
1. 主力合约识别 (基于成交量/持仓量)
2. 合约号解析 (品种代码 + 年份 + 月份 → 具体合约号)
   例如: M2609 → 豆粕 2026年9月合约
3. 主力合约切换日期记录
4. 合约月份规则 (各品种交割月份不同)
"""

from __future__ import annotations

import re
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple


class MainContractResolver:
    """
    主力合约解析器。
    
    支持合约号格式:
    - 简写: M01, RB05, CU12 (品种代码 + 月份，年份自动推断)
    - 全称: M2609, RB2505, CU2512 (品种代码 + 年份 + 月份)
    
    主力合约规则:
    - 1/5/9月: 大多数商品期货 (M, RB, CU, I, P, Y 等)
    - 1/3/5/7/9/11月: 农产品多个月份
    - 3/6/9/12月: 国债期货
    - 连续月份: 金融期货、部分化工品
    """

    def __init__(self):
        # 各品种的主力合约月份规则
        # {品种: [可能的交割月份]}
        self._delivery_rules = {
            # 上期所 - 多数连续月份
            "CU": list(range(1, 13)), "AL": list(range(1, 13)),
            "ZN": list(range(1, 13)), "PB": list(range(1, 13)),
            "NI": list(range(1, 13)), "SN": list(range(1, 13)),
            "AU": list(range(1, 13)), "AG": list(range(1, 13)),
            "RB": list(range(1, 13)), "HC": list(range(1, 13)),
            "SS": list(range(1, 13)), "BU": list(range(1, 13)),
            "SP": list(range(1, 13)), "RU": [1,3,4,5,6,7,8,9,10,11],
            # 大商所
            "M": [1,3,5,7,8,9,11,12], "Y": [1,3,5,7,8,9,11,12],
            "P": list(range(1, 13)), "A": [1,3,5,7,9,11],
            "C": [1,3,5,7,9,11], "I": list(range(1, 13)),
            "J": list(range(1, 13)), "JM": list(range(1, 13)),
            "L": list(range(1, 13)), "PP": list(range(1, 13)),
            "V": list(range(1, 13)), "EG": list(range(1, 13)),
            "PG": list(range(1, 13)), "LH": [1,3,5,7,9,11],
            "JD": list(range(1, 13)),
            # 郑商所
            "SR": [1,3,5,7,9,11], "CF": [1,3,5,7,9,11],
            "TA": list(range(1, 13)), "MA": list(range(1, 13)),
            "FG": list(range(1, 13)), "RM": [1,3,5,7,9,11],
            "OI": [1,3,5,7,9,11], "ZC": list(range(1, 13)),
            "SA": list(range(1, 13)), "UR": list(range(1, 13)),
            "AP": [1,3,4,5,10,11,12], "PK": [1,3,4,10,11,12],
            "CJ": [1,3,5,7,9,12], "SF": list(range(1, 13)),
            "SM": list(range(1, 13)),
            # 中金所
            "IF": list(range(1, 13)), "IH": list(range(1, 13)),
            "IC": list(range(1, 13)), "IM": list(range(1, 13)),
            "T": [3,6,9,12], "TF": [3,6,9,12],
            # 能源中心
            "SC": list(range(1, 13)), "NR": list(range(1, 13)),
            "LU": list(range(1, 13)), "BC": list(range(1, 13)),
            # 广期所
            "SI": list(range(1, 13)), "LC": list(range(1, 13)),
        }

    def parse_contract_code(self, code: str) -> Dict:
        """
        解析合约号。
        
        Args:
            code: 合约号 (如 M2609, RB05, CU2512, SC01)
        
        Returns:
            {symbol, year, month, full_code, display_name}
        """
        code = code.upper()
        
        # 匹配模式: 字母 + 2位年份(可选) + 2位月份
        # 如 M2609, RB05 (年份自动推断), CU2512
        pattern = r'^([A-Z]+)(\d{2,4})?(\d{2})$'
        match = re.match(pattern, code)
        
        if not match:
            # 纯品种代码 (没有合约号)
            return {
                "symbol": code,
                "year": None,
                "month": None,
                "full_code": code,
                "display_name": code,
                "is_main_contract": True,
            }
        
        symbol = match.group(1)
        
        # 处理年份
        year_str = match.group(2)
        month_str = match.group(3)
        month = int(month_str)
        
        now = datetime.now()
        current_year = now.year
        
        if year_str and len(year_str) == 4:
            # 完整年份: M2609 → 2026年9月
            year = int(year_str)
        elif year_str and len(year_str) == 2:
            # 2位年份: M2509 → 2025年9月
            year = 2000 + int(year_str)
        else:
            # 无年份: M09 → 推断最近的一个
            year = current_year
            # 如果月份已过，推断为下一年
            if month < now.month:
                year += 1
        
        full_code = f"{symbol}{year % 100:02d}{month:02d}"
        
        return {
            "symbol": symbol,
            "year": year,
            "month": month,
            "full_code": full_code,
            "display_name": f"{symbol}{year}{month:02d}",
            "is_main_contract": False,
        }

    def is_valid_contract_month(self, symbol: str, month: int) -> bool:
        """检查是否为有效的交割月份"""
        rules = self._delivery_rules.get(symbol.upper())
        if not rules:
            return 1 <= month <= 12
        return month in rules

    def get_main_contract_month(self, symbol: str, current_month: Optional[int] = None) -> int:
        """
        获取当前主力合约月份。
        
        主力合约判断逻辑:
        - 大多数品种: 1月/5月/9月 轮流为主力
        - 农产品: 1月/5月/9月/11月
        - 金融期货: 最近月份
        """
        if current_month is None:
            current_month = datetime.now().month
        
        # 默认主力月份: 1, 5, 9
        main_months = [1, 5, 9]
        
        rules = self._delivery_rules.get(symbol.upper())
        if rules:
            # 找到最接近的可用交割月份
            future_months = [m for m in rules if m >= current_month]
            if future_months:
                return future_months[0]
            # 如果今年没有，取来年第一个
            if rules:
                return rules[0]
        
        # 默认找最近的 1/5/9月
        for m in main_months:
            if m >= current_month:
                return m
        return main_months[0] + 12

    def get_main_contract_code(self, symbol: str) -> str:
        """
        获取当前主力合约代码。
        
        如: 2026年6月调用 → M2609 (9月主力)
        """
        now = datetime.now()
        symbol = symbol.upper()
        
        target_month = self.get_main_contract_month(symbol, now.month)
        target_year = now.year
        
        # 如果目标月份在将来，使用当前年份
        # 如果目标月份小于当前月份，需要加1年
        if target_month < now.month:
            target_year += 1
        
        # 处理跨年: 如果当前月份 > 主力月份, 主力是明年
        if target_month < now.month:
            target_year = now.year + 1
        else:
            target_year = now.year
        
        year_suffix = target_year % 100
        return f"{symbol}{year_suffix:02d}{target_month:02d}"

    def get_contract_cycle(self, symbol: str, count: int = 6) -> List[str]:
        """
        获取后续合约序列。
        
        Args:
            symbol: 品种代码
            count: 返回合约数量
        
        Returns:
            合约代码列表，如 ['M2609', 'M2611', 'M2701', ...]
        """
        symbol = symbol.upper()
        rules = self._delivery_rules.get(symbol, list(range(1, 13)))
        
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        contracts = []
        year = current_year
        month_idx = 0
        
        # 找到当前月份之后第一个可交割月份
        future_months = [m for m in rules if m > current_month] or rules
        
        while len(contracts) < count:
            for m in rules:
                if len(contracts) >= count:
                    break
                if year == current_year and m <= current_month:
                    continue
                year_suffix = year % 100
                contracts.append(f"{symbol}{year_suffix:02d}{m:02d}")
            year += 1
        
        return contracts[:count]

    def get_switch_date(self, symbol: str) -> Optional[str]:
        """
        获取主力合约切换日期（估算）。
        
        通常在交割月前1-2个月切换。
        如 M2509 的主力切换大约在 2025年7月中旬。
        """
        now = datetime.now()
        target_month = self.get_main_contract_month(symbol, now.month)
        target_year = now.year
        
        if target_month < now.month:
            target_year += 1
        
        # 切换通常在交割月前 1-2 个月
        switch_month = target_month - 2
        switch_year = target_year
        if switch_month < 1:
            switch_month += 12
            switch_year -= 1
        
        return f"{switch_year}-{switch_month:02d}-15"
