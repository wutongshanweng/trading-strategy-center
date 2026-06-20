"""
策略目录系统 — 让 Agent / 前端可发现、可查询全部已注册策略。

与 signals.registry 配合:registry 存「类」,catalog 存「元数据 + 运行期表现」。
catalog 在 build_from_registry() 时自动从 registry 采集所有 @register 策略,
按 name 前缀推断 strategy_type,给出默认市态适配,中文名走内置映射(缺则回退英文)。

运行期表现 (sharpe/win_rate/...) 由锦标赛/监控通过 update_performance() 回填
(见 core.feedback_loop)。

用法:
    from signals.catalog import get_catalog
    catalog = get_catalog()                       # 单例, 首次自动 build
    catalog.query(regime="trending", top_k=5)     # 查适合趋势市的
    catalog.best_for("RB2510")                    # 查某品种最优
    catalog.list_by_type()                        # 按类型分组
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger


class StrategyType(Enum):
    TREND = "trend"
    MOMENTUM = "momentum"
    BREAKOUT = "breakout"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    REVERSAL = "reversal"
    FILTER = "filter"
    LAYER = "layer"
    OTHER = "other"


class RegimeFit(Enum):
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"
    CRASH = "crash"
    RECOVERY = "recovery"
    ALL = "all"


# name 前缀 → 策略类型
_PREFIX_TYPE = {
    "trend_": StrategyType.TREND,
    "momentum_": StrategyType.MOMENTUM,
    "breakout_": StrategyType.BREAKOUT,
    "meanrev_": StrategyType.MEAN_REVERSION,
    "reversal_": StrategyType.REVERSAL,
    "arb_": StrategyType.ARBITRAGE,
    "carry_": StrategyType.ARBITRAGE,
    "seasonality_": StrategyType.ARBITRAGE,
    "filter_": StrategyType.FILTER,
}

# 类型 → 默认适合市态
_TYPE_REGIME = {
    StrategyType.TREND: [RegimeFit.TRENDING],
    StrategyType.MOMENTUM: [RegimeFit.TRENDING, RegimeFit.VOLATILE],
    StrategyType.BREAKOUT: [RegimeFit.TRENDING, RegimeFit.VOLATILE],
    StrategyType.MEAN_REVERSION: [RegimeFit.RANGING],
    StrategyType.REVERSAL: [RegimeFit.RANGING, RegimeFit.VOLATILE],
    StrategyType.ARBITRAGE: [RegimeFit.ALL],
    StrategyType.FILTER: [RegimeFit.ALL],
    StrategyType.LAYER: [RegimeFit.ALL],
    StrategyType.OTHER: [RegimeFit.ALL],
}

# 中文名映射 (缺失则用 description / name 回退)
_CN_NAMES = {
    "trend_ma_cross": "双均线趋势", "trend_macd": "MACD趋势", "trend_adx": "ADX趋势",
    "trend_ichimoku": "一目均衡", "trend_supertrend": "超级趋势", "trend_kama": "考夫曼自适应均线",
    "trend_keltner_breakout": "肯特纳通道突破", "trend_parabolic_sar": "抛物线SAR",
    "trend_vortex": "涡流指标", "trend_aroon": "阿隆趋势", "trend_ttm_squeeze": "TTM挤压",
    "trend_dmi": "动向指标DMI", "trend_ema_ribbon": "EMA缎带", "trend_chandelier_exit": "吊灯止损",
    "trend_multi_timeframe": "多周期趋势",
    "momentum_roc": "变动率动量", "momentum_cci": "CCI动量", "momentum_obv": "OBV量能动量",
    "momentum_time_series": "时序动量", "momentum_vol_adjusted": "波动调整动量",
    "momentum_tsi": "真实强弱TSI", "momentum_cmf": "蔡金资金流", "momentum_force_index": "强力指数",
    "momentum_acceleration": "动量加速度",
    "breakout_donchian": "唐奇安突破", "breakout_volatility": "波动率突破", "breakout_volume": "放量突破",
    "breakout_dual_thrust": "Dual Thrust", "breakout_r_breaker": "R-Breaker",
    "breakout_nr7": "NR7窄幅突破", "breakout_inside_bar": "内包线突破", "breakout_new_high_low": "新高新低突破",
    "meanrev_bollinger": "布林回归", "meanrev_zscore": "Z-Score回归", "meanrev_ou": "OU过程回归",
    "meanrev_williams_r": "威廉指标回归", "meanrev_stoch_rsi": "随机RSI回归",
    "meanrev_range": "区间回归", "meanrev_overnight": "隔夜回归",
    "reversal_rsi": "RSI反转", "reversal_kdj": "KDJ反转", "reversal_bollinger": "布林反转",
    "arb_pairs_zscore": "配对Z-Score套利", "arb_ratio_spread": "比值价差套利", "arb_basis": "基差套利",
    "carry_roll_yield": "展期收益", "carry_term_structure_slope": "期限结构斜率",
    "seasonality_monthly": "月度季节性", "seasonality_day_of_week": "星期季节性",
    "filter_volatility": "波动率过滤", "filter_trend_strength": "趋势强度过滤", "filter_regime": "市态过滤",
}


@dataclass
class StrategyMeta:
    """策略元数据 — 供目录检索。"""
    name: str
    strategy_type: StrategyType
    chinese_name: str
    description: str
    regime_fit: List[RegimeFit]
    timeframes: List[str] = field(default_factory=lambda: ["1d"])
    params: Dict = field(default_factory=dict)
    # 运行期字段
    sharpe: float = 0.0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    total_trades: int = 0
    is_active: bool = True
    last_used: str = ""
    symbol_performance: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "name": self.name, "strategy_type": self.strategy_type.value,
            "chinese_name": self.chinese_name, "description": self.description,
            "regime_fit": [r.value for r in self.regime_fit],
            "timeframes": self.timeframes, "sharpe": round(self.sharpe, 4),
            "win_rate": round(self.win_rate, 4), "max_drawdown": round(self.max_drawdown, 4),
            "total_trades": self.total_trades, "is_active": self.is_active,
            "last_used": self.last_used,
        }


def _infer_type(name: str) -> StrategyType:
    for prefix, t in _PREFIX_TYPE.items():
        if name.startswith(prefix):
            return t
    return StrategyType.OTHER


class StrategyCatalog:
    """策略目录 — 元数据检索 + 运行期表现追踪。"""

    def __init__(self, store_path: Optional[str] = None):
        self._strategies: Dict[str, StrategyMeta] = {}
        # 运行期表现持久化路径 (默认 data/strategy_performance.json)
        self.store_path = Path(
            store_path or os.path.join("data", "strategy_performance.json"))

    def register(self, meta: StrategyMeta):
        self._strategies[meta.name] = meta

    def build_from_registry(self) -> int:
        """从 signals.registry 自动采集所有已注册策略, 返回采集数量。"""
        from signals.registry import get_all_strategies
        # 确保策略包已自动加载 (触发 @register)
        try:
            import signals.strategies  # noqa: F401
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"策略包加载异常: {exc}")
        count = 0
        for name, cls in get_all_strategies().items():
            stype = _infer_type(name)
            self.register(StrategyMeta(
                name=name, strategy_type=stype,
                chinese_name=_CN_NAMES.get(name, getattr(cls, "description", "") or name),
                description=getattr(cls, "description", ""),
                regime_fit=list(_TYPE_REGIME.get(stype, [RegimeFit.ALL])),
                timeframes=list(getattr(cls, "timeframes", ["1d"])),
                params=dict(getattr(cls, "params", {})),
            ))
            count += 1
        logger.info(f"策略目录已构建: {count} 个策略")
        self.load()  # 构建后自动恢复已持久化的运行期表现
        return count

    def query(
        self,
        regime: Optional[str] = None,
        strategy_type: Optional[str] = None,
        symbol: Optional[str] = None,
        top_k: int = 10,
        min_sharpe: float = -99,
        active_only: bool = True,
    ) -> List[StrategyMeta]:
        """按市态 / 类型 / 品种查询, 按夏普降序返回 top_k。"""
        results = list(self._strategies.values())
        if active_only:
            results = [s for s in results if s.is_active]
        if regime:
            rl = regime.lower()
            results = [s for s in results
                       if any(r.value == rl for r in s.regime_fit) or RegimeFit.ALL in s.regime_fit]
        if strategy_type:
            results = [s for s in results if s.strategy_type.value == strategy_type]
        if symbol:
            results = [s for s in results if symbol in s.symbol_performance]
        results = [s for s in results if s.sharpe >= min_sharpe]
        results.sort(key=lambda s: s.sharpe, reverse=True)
        return results[:top_k]

    def best_for(self, symbol: str, top_k: int = 3) -> List[StrategyMeta]:
        """某品种上表现最好的策略。"""
        scored = [(s.symbol_performance[symbol], s) for s in self._strategies.values()
                  if symbol in s.symbol_performance]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:top_k]]

    def list_by_type(self) -> Dict[str, List[StrategyMeta]]:
        """按类型分组列出。"""
        out: Dict[str, List[StrategyMeta]] = {}
        for s in self._strategies.values():
            out.setdefault(s.strategy_type.value, []).append(s)
        return out

    def get(self, name: str) -> Optional[StrategyMeta]:
        return self._strategies.get(name)

    def all(self) -> List[StrategyMeta]:
        return list(self._strategies.values())

    def update_performance(
        self, name: str, sharpe: float = None, win_rate: float = None,
        max_drawdown: float = None, total_trades: int = None,
        symbol: str = None, is_active: bool = None,
    ):
        """更新策略表现 (由监控 / 锦标赛回调)。"""
        s = self._strategies.get(name)
        if s is None:
            return
        if sharpe is not None:
            s.sharpe = sharpe
        if win_rate is not None:
            s.win_rate = win_rate
        if max_drawdown is not None:
            s.max_drawdown = max_drawdown
        if total_trades is not None:
            s.total_trades = total_trades
        if is_active is not None:
            s.is_active = is_active
        if symbol is not None and sharpe is not None:
            s.symbol_performance[symbol] = sharpe
        s.last_used = str(pd.Timestamp.now())
        self.save()

    # ───────── 运行期表现持久化 (#4) ─────────

    def save(self) -> None:
        """持久化运行期表现到 JSON (仅表现字段, 元数据每次从 registry 重建)。"""
        try:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                name: {
                    "sharpe": s.sharpe, "win_rate": s.win_rate,
                    "max_drawdown": s.max_drawdown, "total_trades": s.total_trades,
                    "is_active": s.is_active, "last_used": s.last_used,
                    "symbol_performance": s.symbol_performance,
                }
                for name, s in self._strategies.items()
                if s.total_trades or s.sharpe or not s.is_active
            }
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"策略表现持久化失败: {e}")

    def load(self) -> None:
        """从 JSON 恢复运行期表现 (覆盖到当前已注册策略上)。"""
        if not self.store_path.exists():
            return
        try:
            with open(self.store_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"策略表现读取失败: {e}")
            return
        for name, perf in data.items():
            s = self._strategies.get(name)
            if s is None:
                continue
            s.sharpe = perf.get("sharpe", 0.0)
            s.win_rate = perf.get("win_rate", 0.0)
            s.max_drawdown = perf.get("max_drawdown", 0.0)
            s.total_trades = perf.get("total_trades", 0)
            s.is_active = perf.get("is_active", True)
            s.last_used = perf.get("last_used", "")
            s.symbol_performance = perf.get("symbol_performance", {})


_catalog: Optional[StrategyCatalog] = None


def get_catalog() -> StrategyCatalog:
    """获取全局策略目录单例 (首次调用自动从 registry 构建)。"""
    global _catalog
    if _catalog is None:
        _catalog = StrategyCatalog()
        _catalog.build_from_registry()
    return _catalog

