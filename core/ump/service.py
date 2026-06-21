"""UMP 服务 — 训练/持久化/预测 (从真实 kline 训练裁判, 供下单前否决)。

模型 pickle 到 data/ump_models/<strategy>.pkl。DuckDB 单进程锁 → 在 API 进程内调用。
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

from core.config.watchlist import DEFAULT_MAIN_CONTRACT
from core.ump.judges import UMPManager, trade_features
from core.ump.training import build_training_set, FEATURE_COLS

_MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "ump_models"


def _load_kline(contract: str, timeframe: str = "D1", limit: int = 800) -> pd.DataFrame:
    from data_center.storage.duckdb_store import get_store
    store = get_store()
    sid = store.query("SELECT symbol_id FROM symbols WHERE code = ?", [contract.upper()])
    if sid is None or sid.empty:
        return pd.DataFrame()
    symbol_id = int(sid.iloc[0]["symbol_id"])
    df = store.query(
        """SELECT datetime, open, high, low, close, volume FROM kline
           WHERE symbol_id=? AND timeframe=? ORDER BY datetime DESC LIMIT ?""",
        [symbol_id, timeframe, limit],
    )
    if df is None or df.empty:
        return pd.DataFrame()
    return df.sort_values("datetime").reset_index(drop=True).set_index("datetime")


class UMPService:
    """UMP 训练/预测服务。"""

    def __init__(self):
        self._cache: Dict[str, UMPManager] = {}

    def _model_path(self, strategy: str) -> Path:
        return _MODEL_DIR / f"{strategy}.pkl"

    def train(self, strategy: str, contracts: Optional[List[str]] = None) -> Dict:
        """对某策略, 汇总多合约的逐笔交易训练 UMP 裁判。"""
        contracts = contracts or [DEFAULT_MAIN_CONTRACT.get(p, f"{p}2510")
                                  for p in ("RB", "CU", "M", "TA")]
        frames = []
        for c in contracts:
            df = _load_kline(c)
            if df.empty or len(df) < 80:
                continue
            ts = build_training_set(strategy, df)
            if ts is not None:
                frames.append(ts)
        if not frames:
            return {"trained": False, "reason": "无足够交易样本"}
        all_trades = pd.concat(frames, ignore_index=True)
        mgr = UMPManager().fit(all_trades, FEATURE_COLS, "pnl")
        if not mgr._fitted:
            return {"trained": False, "reason": f"样本不足 ({len(all_trades)} 笔)"}
        _MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with open(self._model_path(strategy), "wb") as f:
            pickle.dump(mgr, f)
        self._cache[strategy] = mgr
        win_rate = float((all_trades["pnl"] > 0).mean())
        return {"trained": True, "strategy": strategy,
                "n_trades": len(all_trades), "win_rate": round(win_rate, 3),
                "bad_clusters": len(mgr.main._bad_clusters),
                "contracts": contracts}

    def _get_manager(self, strategy: str) -> Optional[UMPManager]:
        if strategy in self._cache:
            return self._cache[strategy]
        path = self._model_path(strategy)
        if path.exists():
            try:
                with open(path, "rb") as f:
                    mgr = pickle.load(f)
                self._cache[strategy] = mgr
                return mgr
            except Exception as e:
                logger.warning(f"[ump] load {strategy} failed: {e}")
        return None

    def judge(self, strategy: str, df: pd.DataFrame, idx: Optional[int] = None) -> Dict:
        """对某策略在 df 某入场点的候选交易做否决裁定。"""
        mgr = self._get_manager(strategy)
        if mgr is None:
            return {"block": False, "reason": "该策略无 UMP 模型 (未训练), 放行",
                    "trained": False}
        if idx is None:
            idx = len(df) - 1
        feats = trade_features(df, idx, 20)
        if feats is None:
            return {"block": False, "reason": "特征不足, 放行", "trained": True}
        dec = mgr.block_decision(feats)
        dec["trained"] = True
        return dec

    def list_models(self) -> List[str]:
        if not _MODEL_DIR.exists():
            return []
        return sorted(p.stem for p in _MODEL_DIR.glob("*.pkl"))


_service: Optional[UMPService] = None


def get_ump_service() -> UMPService:
    global _service
    if _service is None:
        _service = UMPService()
    return _service
