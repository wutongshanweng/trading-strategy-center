"""chan.py 专业缠论引擎适配层。

vendor/chanpy/ 是 chan.py-main (MIT) 的 vendored 核心算法簇 (Bi/Seg/ZS/BuySellPoint/...)。
本模块把项目的 pandas DataFrame 适配进去, 跑出专业级买卖点 (一/二/三买卖+背驰),
作为新信号源接入 54 策略体系。

我们原有的 analysis/chan_theory.py (简化版) 保留不动; 此为增强版。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from loguru import logger

_VENDOR = Path(__file__).resolve().parent.parent / "vendor" / "chanpy"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

# 把当前 DataFrame 暂存, 供自定义 DataAPI 读取 (chan 用 custom:module.class 动态加载)
_DF_REGISTRY: Dict[str, pd.DataFrame] = {}


def _register_df(key: str, df: pd.DataFrame) -> None:
    _DF_REGISTRY[key] = df


def get_registered_df(key: str) -> Optional[pd.DataFrame]:
    return _DF_REGISTRY.get(key)


class ChanProEngine:
    """专业缠论买卖点引擎 (基于 vendored chan.py)。"""

    def __init__(self, bs_type: str = "1,2,3a,1p,2s,3b"):
        self.bs_type = bs_type

    def compute_bsp(self, df: pd.DataFrame, symbol: str = "") -> Dict:
        """对 OHLC DataFrame 计算缠论买卖点。

        df: index 为时间, 含 open/high/low/close 列。
        返回 {bsp: [...], n_bi, n_seg, n_zs, error}。
        """
        if df is None or df.empty or len(df) < 30:
            return {"bsp": [], "n_bi": 0, "n_seg": 0, "n_zs": 0,
                    "error": "数据不足 (<30 根)"}
        try:
            from Chan import CChan
            from ChanConfig import CChanConfig
            from Common.CEnum import KL_TYPE
        except Exception as e:
            return {"bsp": [], "n_bi": 0, "n_seg": 0, "n_zs": 0,
                    "error": f"chanpy 导入失败: {e}"}

        key = f"{symbol or 'sym'}_{id(df)}"
        _register_df(key, df)
        try:
            config = CChanConfig({
                "bi_strict": True, "trigger_step": False,
                "divergence_rate": float("inf"),
                "bsp2_follow_1": False, "bsp3_follow_1": False,
                "min_zs_cnt": 0, "bs1_peak": False,
                "macd_algo": "peak", "bs_type": self.bs_type,
                "print_warning": False, "zs_algo": "normal",
            })
            chan = CChan(
                code=key, begin_time=None, end_time=None,
                data_src="custom:chan_df_api.ChanDFApi",
                lv_list=[KL_TYPE.K_DAY], config=config,
            )
            bsp_list = chan[0].bs_point_lst.getSortedBspList()  # 排序买卖点 (避免 get_bsp 弃用警告)
            kl = chan[0]
            out = []
            for bsp in bsp_list:
                out.append({
                    "time": str(bsp.klu.time),
                    "is_buy": bool(bsp.is_buy),
                    "types": [t.value for t in bsp.type],
                    "type_str": bsp.type2str(),
                    "price": float(bsp.klu.close),
                })
            return {
                "bsp": out,
                "n_bi": len(kl.bi_list), "n_seg": len(kl.seg_list),
                "n_zs": len(kl.zs_list), "error": None,
            }
        except Exception as e:
            logger.warning(f"[chanpro] compute {symbol} failed: {type(e).__name__}: {e}")
            return {"bsp": [], "n_bi": 0, "n_seg": 0, "n_zs": 0, "error": str(e)}
        finally:
            _DF_REGISTRY.pop(key, None)

    def latest_signal(self, df: pd.DataFrame, symbol: str = "") -> Dict:
        """取最近一个买卖点作为信号 (供策略层使用)。"""
        res = self.compute_bsp(df, symbol)
        if res["error"] or not res["bsp"]:
            return {"direction": "HOLD", "reason": res["error"] or "无买卖点",
                    "bsp_type": None, "n_zs": res["n_zs"]}
        last = res["bsp"][-1]
        return {
            "direction": "BUY" if last["is_buy"] else "SELL",
            "reason": f"缠论{last['type_str']}{'买点' if last['is_buy'] else '卖点'}",
            "bsp_type": last["type_str"], "time": last["time"],
            "price": last["price"], "n_zs": res["n_zs"],
            "n_bi": res["n_bi"], "n_seg": res["n_seg"],
        }


_engine: Optional[ChanProEngine] = None


def get_engine() -> ChanProEngine:
    global _engine
    if _engine is None:
        _engine = ChanProEngine()
    return _engine
