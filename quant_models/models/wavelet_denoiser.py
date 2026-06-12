import numpy as np
from typing import Dict, Any, Optional
import pywt
from .. import QuantModel


class WaveletDenoiserModel(QuantModel):
    name = "WaveletDenoiser"

    def __init__(self, wavelet: str = 'db4', level: Optional[int] = None, mode: str = 'soft'):
        self.wavelet = wavelet
        self.level = level
        self.mode = mode
        self._threshold = None
        self._fitted = False

    def fit(self, df, **kwargs):
        close = df['close'].dropna().values
        if len(close) < 4:
            raise ValueError("Need at least 4 data points")
        w = pywt.Wavelet(self.wavelet)
        max_level = pywt.dwt_max_level(len(close), w.dec_len)
        level = min(self.level or max_level, max_level)
        coeffs = pywt.wavedec(close, w, level=level)
        sigma = np.median(np.abs(coeffs[-1])) / 0.6745
        self._threshold = sigma * np.sqrt(2.0 * np.log(len(close)))
        self._level = level
        self._fitted = True

    def predict(self, df):
        close = df['close'].dropna().values
        if len(close) < 4:
            return close.copy()
        w = pywt.Wavelet(self.wavelet)
        level = self._level if self._fitted else 1
        coeffs = pywt.wavedec(close, w, level=level)
        denoised = [coeffs[0]] + [pywt.threshold(c, self._threshold, mode=self.mode) for c in coeffs[1:]]
        return pywt.waverec(denoised, w)[:len(close)]

    def get_params(self) -> Dict[str, Any]:
        return {"wavelet": self.wavelet, "level": self._level if self._fitted else self.level,
                "mode": self.mode, "threshold": self._threshold}
