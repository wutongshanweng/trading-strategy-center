from typing import List, Dict
import numpy as np
import pandas as pd


class FourierAnalyzer:
    def __init__(self):
        self.fft_values = self.frequencies = None
        self.mean, self.n = 0.0, 0

    def fit(self, series: pd.Series):
        clean = series.dropna().values
        if len(clean) < 4:
            return self
        self.n, self.mean = len(clean), float(np.mean(clean))
        self.fft_values = np.fft.fft(clean - self.mean)
        self.frequencies = np.fft.fftfreq(self.n)
        return self

    def get_cycles(self, top_n: int = 3):
        if self.fft_values is None or self.n < 4:
            return []
        amp, phase, freqs = np.abs(self.fft_values[:self.n // 2]), np.angle(self.fft_values[:self.n // 2]), self.frequencies[:self.n // 2]
        valid = freqs > 0
        amp, phase, freqs = amp[valid], phase[valid], freqs[valid]
        if len(amp) == 0:
            return []
        top_n = min(top_n, len(amp))
        total_amp = np.sum(amp) + 1e-10
        return [{"amplitude": float(amp[i]), "phase": float(phase[i]), "frequency": float(freqs[i]),
                 "period": float(1.0 / freqs[i]) if freqs[i] > 0 else np.inf,
                 "strength": float(amp[i] / total_amp)}
                for i in np.argsort(amp)[::-1][:top_n]]

    def reconstruct(self, n_components: int = 5):
        if self.fft_values is None or self.n < 2:
            return np.array([])
        n = min(n_components, self.n // 2)
        fft_filtered = np.zeros(self.n, dtype=complex)
        for i in np.argsort(np.abs(self.fft_values[:self.n // 2]))[::-1][:n]:
            fft_filtered[i] = self.fft_values[i]
            if i > 0:
                fft_filtered[self.n - i] = self.fft_values[self.n - i]
        return np.real(np.fft.ifft(fft_filtered)) + self.mean
