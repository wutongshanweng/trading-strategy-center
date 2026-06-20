"""
全波动率曲面建模 — 跨到期日的 IV 曲面插值与分析。

在已有单切片 SVI (options/volatility/svi_surface) 基础上扩展:
  1. 多到期日切片注册
  2. 任意 (K, T) 点 IV 查询 (双线性插值)
  3. 偏度 / 曲率 / 期限结构分析
  4. 曲面网格输出 (可视化)

用法:
    surface = VolSurface()
    surface.set_forward(100.0)
    surface.add_slice(T=0.1, strikes=[...], ivs=[...])
    surface.add_slice(T=0.3, strikes=[...], ivs=[...])
    surface.build()
    iv = surface.get_iv(strike=100, T=0.25)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import interpolate
from loguru import logger


@dataclass
class SurfaceSlice:
    """单个到期日的 IV 切片。"""
    T: float                          # 到期时间 (年)
    strikes: np.ndarray
    ivs: np.ndarray
    moneyness: np.ndarray             # log(K/F)
    svi_params: Optional[List[float]] = None


class VolSurface:
    """全波动率曲面 — 多到期日注册 + (K,T) 查询 + 特征提取。"""

    def __init__(self):
        self.slices: Dict[float, SurfaceSlice] = {}
        self._forward_price: Optional[float] = None
        self._interpolator: Optional[Any] = None

    def set_forward(self, F: float):
        """设置标的远期价格。"""
        self._forward_price = F

    def add_slice(
        self,
        T: float,
        strikes,
        ivs,
        svi_params: Optional[List[float]] = None,
    ):
        """添加一个到期日切片。"""
        strikes = np.asarray(strikes, dtype=float)
        ivs = np.asarray(ivs, dtype=float)
        moneyness = (np.log(strikes / self._forward_price)
                     if self._forward_price else strikes)
        self.slices[T] = SurfaceSlice(
            T=T, strikes=strikes, ivs=ivs, moneyness=moneyness, svi_params=svi_params)

    def build(self):
        """构建全曲面插值器 (strike × T 双线性)。"""
        if len(self.slices) < 2:
            logger.warning("Need at least 2 slices for surface interpolation")
            return
        points, values = [], []
        for s in self.slices.values():
            for k, iv in zip(s.strikes, s.ivs):
                points.append([s.T, k])
                values.append(iv)
        points, values = np.array(points), np.array(values)
        if len(points) >= 4:
            self._interpolator = interpolate.LinearNDInterpolator(points, values)
            logger.info(f"Surface built: {len(self.slices)} slices, {len(points)} points")

    def get_iv(self, strike: float, T: float) -> Optional[float]:
        """查询任意 (strike, T) 点的 IV (插值顺序与 build 一致: (T, strike))。"""
        if self._interpolator is None:
            return None
        result = self._interpolator(T, strike)
        val = float(result) if result is not None else float("nan")
        if np.isnan(val):
            # 超出凸包时回退到最近切片的最近行权价
            s = self._nearest_slice(T)
            if s is None:
                return None
            idx = int(np.argmin(np.abs(s.strikes - strike)))
            return float(s.ivs[idx])
        return val

    def get_skew(self, T: float) -> float:
        """偏度: 最高 strike IV - 最低 strike IV (正=put更贵/恐惧)。"""
        s = self._nearest_slice(T)
        if s is None or len(s.ivs) < 2:
            return 0.0
        return float(s.ivs[-1] - s.ivs[0])

    def get_curvature(self, T: float) -> float:
        """曲率: 中间 IV 与两端 IV 均值之差 (微笑凸度)。"""
        s = self._nearest_slice(T)
        if s is None or len(s.ivs) < 3:
            return 0.0
        mid = s.ivs[len(s.ivs) // 2]
        ends = (s.ivs[0] + s.ivs[-1]) / 2
        return float(mid - ends)

    def get_term_structure(self, strike: Optional[float] = None) -> List[Tuple[float, float]]:
        """期限结构: [(T1, IV1), (T2, IV2), ...]。"""
        if strike is None:
            strike = self._forward_price or 0
        out = []
        for T in sorted(self.slices.keys()):
            iv = self.get_iv(strike, T)
            if iv is not None:
                out.append((T, iv))
        return out

    def _nearest_slice(self, T: float) -> Optional[SurfaceSlice]:
        if not self.slices:
            return None
        return self.slices[min(self.slices.keys(), key=lambda x: abs(x - T))]

    def surface_to_grid(
        self, n_strikes: int = 20, n_ttm: int = 10,
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
        """输出曲面网格 (T_grid, K_grid, IV_grid), 用于可视化。"""
        if self._interpolator is None:
            return None, None, None
        all_T = sorted(self.slices.keys())
        all_K = np.linspace(
            min(s.strikes.min() for s in self.slices.values()),
            max(s.strikes.max() for s in self.slices.values()), n_strikes)
        T_grid, K_grid = np.meshgrid(np.linspace(all_T[0], all_T[-1], n_ttm), all_K)
        IV_grid = self._interpolator(T_grid, K_grid)
        return T_grid, K_grid, IV_grid


def build_surface_from_data(
    option_chain: Dict[float, Tuple[np.ndarray, np.ndarray]],
    forward: float,
) -> VolSurface:
    """从期权链 {T: (strikes, ivs)} 构建曲面。"""
    surface = VolSurface()
    surface.set_forward(forward)
    for T, (strikes, ivs) in option_chain.items():
        surface.add_slice(T, strikes, ivs)
    surface.build()
    return surface
