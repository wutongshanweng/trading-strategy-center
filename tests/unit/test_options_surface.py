"""期权波动率曲面 / 期限结构套利 测试。"""

import numpy as np

from options.volatility.surface import VolSurface, build_surface_from_data
from options.strategies.term_arbitrage import TermArbitrageSignals


def _skewed_chain():
    """带偏斜的微笑切片 (put 端 IV 更高 → skew>0)。"""
    K = np.arange(80, 121, 5).astype(float)
    out = []
    for T, base in [(0.1, 0.20), (0.3, 0.22), (0.6, 0.25)]:
        # 线性偏斜: 低 strike IV 高, 高 strike IV 低
        ivs = base + 0.0010 * (100 - K)
        out.append((T, K, ivs))
    return out


class TestVolSurface:
    def _build(self):
        surface = VolSurface()
        surface.set_forward(100.0)
        for T, K, ivs in _skewed_chain():
            surface.add_slice(T, K, ivs)
        surface.build()
        return surface

    def test_basic_surface(self):
        surface = self._build()
        iv = surface.get_iv(strike=100, T=0.3)
        assert iv is not None and 0.1 < iv < 0.6  # 验收项 6

    def test_skew_curvature_are_float(self):
        surface = self._build()
        assert isinstance(surface.get_skew(0.25), float)      # 验收项 7
        assert isinstance(surface.get_curvature(0.25), float)

    def test_term_structure(self):
        surface = self._build()
        ts = surface.get_term_structure(strike=100)
        assert len(ts) >= 2

    def test_surface_grid(self):
        surface = self._build()
        T, K, IV = surface.surface_to_grid(n_strikes=10, n_ttm=5)
        # meshgrid(linspace(n_ttm), all_K(n_strikes)) → shape (n_strikes, n_ttm)
        assert IV.shape == (10, 5)
        assert T.shape == K.shape == IV.shape

    def test_build_from_data_helper(self):
        chain = {T: (K, ivs) for T, K, ivs in _skewed_chain()}
        surface = build_surface_from_data(chain, forward=100.0)
        assert surface.get_iv(95, 0.3) is not None


class TestTermArbitrageSignals:
    def test_skew_extreme_triggers(self):
        """构造强偏斜 → 触发 IV_SKEW 信号。"""
        surface = VolSurface()
        surface.set_forward(100.0)
        K = np.arange(80, 121, 5).astype(float)
        # 强偏斜: 两端 IV 差 > skew_threshold(0.15)
        ivs = 0.20 + 0.005 * (100 - K)  # 80→0.30, 120→0.10, 差 0.20
        surface.add_slice(0.1, K, ivs)
        surface.add_slice(0.3, K, ivs + 0.02)
        surface.build()
        sigs = TermArbitrageSignals().compute(surface, spot=100)
        types = {s.signal_type for s in sigs}
        assert "IV_SKEW" in types  # 验收项 8

    def test_surface_arb_triggers(self):
        """构造局部凸起 → 触发 SURFACE_ARB 信号。"""
        surface = VolSurface()
        surface.set_forward(100.0)
        K = np.array([90.0, 95, 100, 105, 110])
        ivs = np.array([0.20, 0.21, 0.30, 0.21, 0.20])  # 中间 100 异常凸起
        surface.add_slice(0.1, K, ivs)
        surface.add_slice(0.3, K, ivs)
        surface.build()
        sigs = TermArbitrageSignals().compute(surface, spot=100)
        assert any(s.signal_type == "SURFACE_ARB" for s in sigs)

    def test_term_structure_with_history(self):
        """提供历史 → 期限结构 z-score 异常触发 TERM_STRUCTURE。"""
        surface = VolSurface()
        surface.set_forward(100.0)
        K = np.arange(80, 121, 5).astype(float)
        surface.add_slice(0.1, K, 0.20 + 0.0 * K)
        surface.add_slice(0.6, K, 0.40 + 0.0 * K)  # 远月 IV 远高 → 大 spread
        surface.build()
        hist = {"term_spread_hist": list(np.random.normal(0.0, 0.01, 50))}
        sigs = TermArbitrageSignals().compute(surface, spot=100, history=hist)
        assert any(s.signal_type == "TERM_STRUCTURE" for s in sigs)
