from typing import Optional


class DrawdownController:
    def __init__(self, max_drawdown_pct: float = 0.15):
        self.peak_capital: Optional[float] = None
        self.max_drawdown_pct = max_drawdown_pct
        self._locked = False

    def update(self, capital: float) -> dict:
        if self.peak_capital is None or capital > self.peak_capital:
            self.peak_capital = capital
        if self.peak_capital == 0:
            return {"drawdown_pct": 0.0, "locked": False}
        dd = (self.peak_capital - capital) / self.peak_capital
        self._locked = dd >= self.max_drawdown_pct
        return {"drawdown_pct": round(dd, 4), "locked": self._locked}

    @property
    def locked(self) -> bool:
        return self._locked

    def reset(self):
        self.peak_capital = None
        self._locked = False
