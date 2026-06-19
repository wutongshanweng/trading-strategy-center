"""
品种/合约注册表 — code <-> id 解析与自动建档。

职责:
- products 品种层: 'RB','IO','600019.SH' -> product_id
- symbols 合约层: 'RB2509','IO2509-C-3700','600019' -> symbol_id
- 首次写入行情前自动建档 (get_or_create)
- 解析合约代码 (年月/期权类型/行权价)
"""

from __future__ import annotations

import re
import threading
from typing import Optional

from ..storage.duckdb_store import DuckDBStore, get_store

# 期货合约: 品种字母 + 4位年月 (RB2509) 或 3位 (老郑商所 RB509)
_FUT_RE = re.compile(r"^([A-Za-z]{1,3})(\d{3,4})$")
# 期权合约 - 连字符格式 (DCE/股指): 标的+月份-C/P-行权价 (IO2509-C-3700, M2608-C-2500)
_OPT_RE = re.compile(r"^([A-Za-z_]+?\d{3,4})-([CP])-(\d+(?:\.\d+)?)$", re.IGNORECASE)
# 期权合约 - 无连字符格式 (CZCE 3位年月 SR609C4600 / SHFE 4位年月 CU2607C76000)
_OPT_RE2 = re.compile(r"^([A-Za-z]{1,3})(\d{3,4})([CP])(\d+(?:\.\d+)?)$", re.IGNORECASE)


class SymbolRegistry:
    """品种/合约注册与解析。"""

    def __init__(self, store: Optional[DuckDBStore] = None):
        self._store = store or get_store()
        self._lock = threading.Lock()
        self._product_cache: dict[str, int] = {}
        self._symbol_cache: dict[str, int] = {}

    # ---- 品种层 ------------------------------------------------------------

    def get_or_create_product(
        self, code: str, name: str = "", asset_type: str = "futures",
        exchange: Optional[str] = None,
    ) -> int:
        code = code.upper()
        if code in self._product_cache:
            return self._product_cache[code]
        with self._lock:
            df = self._store.query("SELECT product_id FROM products WHERE code = ?", [code])
            if not df.empty:
                pid = int(df.iloc[0]["product_id"])
            else:
                self._store.execute(
                    "INSERT INTO products (code, name, asset_type, exchange) VALUES (?,?,?,?)",
                    [code, name or code, asset_type, exchange],
                )
                pid = int(
                    self._store.query("SELECT product_id FROM products WHERE code = ?", [code])
                    .iloc[0]["product_id"]
                )
            self._product_cache[code] = pid
            return pid

    # ---- 合约层 ------------------------------------------------------------

    def parse_contract(self, code: str) -> dict:
        """解析合约代码, 返回 year/month/option_type/strike (期货/期权/股票通用)。
        期权支持两种格式: 连字符 (M2608-C-2500) 与无连字符 (SR609C4600 / CU2607C76000)。"""
        code = code.strip()
        m = _OPT_RE.match(code)
        if m:
            underlying, cp, strike = m.groups()
            ym = re.search(r"(\d{3,4})$", underlying).group(1)
            year, month = _split_yearmonth(ym)
            return {
                "option_type": "call" if cp.upper() == "C" else "put",
                "strike_price": float(strike),
                "contract_year": year, "contract_month": month,
            }
        m = _OPT_RE2.match(code)
        if m:
            _, ym, cp, strike = m.groups()
            year, month = _split_yearmonth(ym)
            return {
                "option_type": "call" if cp.upper() == "C" else "put",
                "strike_price": float(strike),
                "contract_year": year, "contract_month": month,
            }
        m = _FUT_RE.match(code)
        if m:
            _, ym = m.groups()
            year, month = _split_yearmonth(ym)
            return {"contract_year": year, "contract_month": month}
        return {}

    def get_or_create_symbol(
        self, code: str, product_code: str, asset_type: str = "futures",
        exchange: Optional[str] = None, name: str = "",
    ) -> int:
        code = code.upper()
        if code in self._symbol_cache:
            return self._symbol_cache[code]
        pid = self.get_or_create_product(product_code, asset_type=asset_type, exchange=exchange)
        with self._lock:
            df = self._store.query("SELECT symbol_id FROM symbols WHERE code = ?", [code])
            if not df.empty:
                sid = int(df.iloc[0]["symbol_id"])
            else:
                meta = self.parse_contract(code)
                self._store.execute(
                    """INSERT INTO symbols
                       (product_id, code, name, contract_year, contract_month,
                        option_type, strike_price)
                       VALUES (?,?,?,?,?,?,?)""",
                    [pid, code, name or code, meta.get("contract_year"),
                     meta.get("contract_month"), meta.get("option_type"),
                     meta.get("strike_price")],
                )
                sid = int(
                    self._store.query("SELECT symbol_id FROM symbols WHERE code = ?", [code])
                    .iloc[0]["symbol_id"]
                )
            self._symbol_cache[code] = sid
            return sid


def _split_yearmonth(ym: str) -> tuple[int, str]:
    """'2509' -> (2025,'09');  '509' -> (2025,'09') (老式郑商所3位, 按当前年代推断)。"""
    from datetime import datetime
    if len(ym) == 4:
        return 2000 + int(ym[:2]), ym[2:]
    # 3 位: 首位是年个位, 按当前十年推断 (例如 2026 -> 502 视为 2025)
    digit, mm = int(ym[0]), ym[1:]
    cur = datetime.now().year
    decade = (cur // 10) * 10
    year = decade + digit
    if year < cur - 1:  # 已过去太久, 进位到下个十年
        year += 10
    return year, mm

