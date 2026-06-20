"""
技术面特征集 — 从行情数据自动构建。

分类: 动量 / 波动 / 量价 / 形态。
compute_fn 签名: fn(data: pd.DataFrame) -> pd.Series

用法:
    pipe = FeaturePipeline()
    pipe.register_module(TechnicalFeatureSet())
    X = pipe.compute_all(data)
"""

from __future__ import annotations

from typing import Callable, List, Tuple

import pandas as pd


class TechnicalFeatureSet:
    """技术面特征集合 (模块化注册)。"""

    def get_features(self) -> List[Tuple[str, Callable, str]]:
        return [
            ("momentum_5d", self._momentum, "technical"),
            ("momentum_10d", self._momentum_10d, "technical"),
            ("momentum_20d", self._momentum_20d, "technical"),
            ("rsi_14", self._rsi_14, "technical"),
            ("rsi_7", self._rsi_7, "technical"),
            ("close_to_ma5", self._close_to_ma5, "technical"),
            ("close_to_ma20", self._close_to_ma20, "technical"),
            ("close_to_ma60", self._close_to_ma60, "technical"),
            ("atr_14", self._atr_14, "technical"),
            ("volatility_5d", self._vol_5d, "technical"),
            ("volatility_20d", self._vol_20d, "technical"),
            ("vol_ratio_5_20", self._vol_ratio, "technical"),
            ("gap_pct", self._gap_pct, "technical"),
            ("volume_change_5d", self._vol_change, "technical"),
            ("volume_ma_ratio", self._volume_ma_ratio, "technical"),
            ("obv_change", self._obv_change, "technical"),
            ("macd_hist", self._macd_hist, "technical"),
            ("bb_position", self._bb_position, "technical"),
            ("kdj_k", self._kdj_k, "technical"),
            ("price_position_20d", self._price_position, "technical"),
            ("crossover_signals", self._crossover_signals, "technical"),
        ]

    def _momentum(self, data: pd.DataFrame) -> pd.Series:
        return data["close"].pct_change(5)

    def _momentum_10d(self, data: pd.DataFrame) -> pd.Series:
        return data["close"].pct_change(10)

    def _momentum_20d(self, data: pd.DataFrame) -> pd.Series:
        return data["close"].pct_change(20)

    def _rsi_14(self, data: pd.DataFrame) -> pd.Series:
        delta = data["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))

    def _rsi_7(self, data: pd.DataFrame) -> pd.Series:
        delta = data["close"].diff()
        gain = delta.clip(lower=0).rolling(7).mean()
        loss = (-delta.clip(upper=0)).rolling(7).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))

    def _close_to_ma5(self, data: pd.DataFrame) -> pd.Series:
        c = data["close"]; ma = c.rolling(5).mean()
        return (c - ma) / (ma + 1e-10)

    def _close_to_ma20(self, data: pd.DataFrame) -> pd.Series:
        c = data["close"]; ma = c.rolling(20).mean()
        return (c - ma) / (ma + 1e-10)

    def _close_to_ma60(self, data: pd.DataFrame) -> pd.Series:
        c = data["close"]; ma = c.rolling(60).mean()
        return (c - ma) / (ma + 1e-10)

    def _atr_14(self, data: pd.DataFrame) -> pd.Series:
        h, l, c = data["high"], data["low"], data["close"]
        tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()],
                       axis=1).max(axis=1)
        return tr.rolling(14).mean() / c

    def _vol_5d(self, data: pd.DataFrame) -> pd.Series:
        return data["close"].pct_change().rolling(5).std()

    def _vol_20d(self, data: pd.DataFrame) -> pd.Series:
        return data["close"].pct_change().rolling(20).std()

    def _vol_ratio(self, data: pd.DataFrame) -> pd.Series:
        v5 = data["close"].pct_change().rolling(5).std()
        v20 = data["close"].pct_change().rolling(20).std()
        return v5 / (v20 + 1e-10)

    def _gap_pct(self, data: pd.DataFrame) -> pd.Series:
        return (data["open"] - data["close"].shift(1)) / (data["close"].shift(1) + 1e-10)

    def _vol_change(self, data: pd.DataFrame) -> pd.Series:
        return data["volume"].pct_change(5)

    def _volume_ma_ratio(self, data: pd.DataFrame) -> pd.Series:
        v = data["volume"]
        return v / (v.rolling(20).mean() + 1e-10)

    def _obv_change(self, data: pd.DataFrame) -> pd.Series:
        close, volume = data["close"], data["volume"]
        obv = (volume * (close.diff() > 0).astype(int)
               - volume * (close.diff() < 0).astype(int)).cumsum()
        return obv.pct_change(5)

    def _macd_hist(self, data: pd.DataFrame) -> pd.Series:
        c = data["close"]
        macd = c.ewm(span=12).mean() - c.ewm(span=26).mean()
        return macd - macd.ewm(span=9).mean()

    def _bb_position(self, data: pd.DataFrame) -> pd.Series:
        c = data["close"]; ma = c.rolling(20).mean(); std = c.rolling(20).std()
        upper, lower = ma + 2 * std, ma - 2 * std
        return (c - lower) / (upper - lower + 1e-10)

    def _kdj_k(self, data: pd.DataFrame) -> pd.Series:
        h = data["high"].rolling(9).max(); l = data["low"].rolling(9).min()
        rsv = (data["close"] - l) / (h - l + 1e-10) * 100
        return rsv.ewm(span=3).mean()

    def _price_position(self, data: pd.DataFrame) -> pd.Series:
        c = data["close"]; mn = c.rolling(20).min(); mx = c.rolling(20).max()
        return (c - mn) / (mx - mn + 1e-10)

    def _crossover_signals(self, data: pd.DataFrame) -> pd.Series:
        ma5 = data["close"].rolling(5).mean()
        ma20 = data["close"].rolling(20).mean()
        cross = pd.Series(0.0, index=data.index)
        cross[(ma5 > ma20) & (ma5.shift(1) <= ma20.shift(1))] = 1
        cross[(ma5 < ma20) & (ma5.shift(1) >= ma20.shift(1))] = -1
        return cross
