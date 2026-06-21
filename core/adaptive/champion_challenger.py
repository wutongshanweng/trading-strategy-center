"""Champion/Challenger 安全晋级 (阶段4)。

策略生命周期: challenger (考察) → champion (实盘分配) → retired (淘汰)。
安全护栏: 新策略先以 challenger 入场, 连续 N 次评估达标 + 通过晋升闸门 + 人工批准
才毕业为 champion 并获得资金分配权重。无券商接入, 分配为记录性权重 + 标志位。

数据: data/champion_challenger.json (JSON 持久化)。
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_STATE_FILE = _DATA_DIR / "champion_challenger.json"

# 毕业门槛
MIN_EVALS_TO_GRADUATE = 3       # 至少连续 N 次评估
MIN_PASS_RATE = 0.67            # 其中通过晋升闸门的比例
MIN_AVG_OOS_SHARPE = 0.3        # 平均样本外夏普下限


@dataclass
class ChallengerRecord:
    name: str
    status: str = "challenger"          # challenger / champion / retired
    regime: str = "UNKNOWN"
    evals: List[Dict] = field(default_factory=list)   # 每次评估 {ts, passed, oos_sharpe}
    allocation: float = 0.0             # champion 的资金权重 (记录性)
    approved_by: str = ""               # 人工批准标记
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    graduated_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def n_evals(self) -> int:
        return len(self.evals)

    @property
    def pass_rate(self) -> float:
        if not self.evals:
            return 0.0
        return sum(1 for e in self.evals if e.get("passed")) / len(self.evals)

    @property
    def avg_oos_sharpe(self) -> float:
        if not self.evals:
            return 0.0
        return sum(e.get("oos_sharpe", 0.0) for e in self.evals) / len(self.evals)

    def eligible_for_graduation(self) -> bool:
        return (self.status == "challenger"
                and self.n_evals >= MIN_EVALS_TO_GRADUATE
                and self.pass_rate >= MIN_PASS_RATE
                and self.avg_oos_sharpe >= MIN_AVG_OOS_SHARPE)


class ChampionChallengerRegistry:
    """策略晋级生命周期管理。"""

    def __init__(self):
        self._records: Dict[str, ChallengerRecord] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if not _STATE_FILE.exists():
            return
        try:
            data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
            for d in data:
                self._records[d["name"]] = ChallengerRecord(**d)
        except Exception as e:
            logger.warning(f"[cc] load failed: {e}")

    def _save(self) -> None:
        with self._lock:
            _DATA_DIR.mkdir(parents=True, exist_ok=True)
            _STATE_FILE.write_text(
                json.dumps([r.to_dict() for r in self._records.values()],
                           ensure_ascii=False, indent=2), encoding="utf-8")

    def enroll(self, name: str, regime: str = "UNKNOWN") -> ChallengerRecord:
        """新策略以 challenger 入场。"""
        rec = self._records.get(name)
        if rec is None:
            rec = ChallengerRecord(name=name, regime=regime)
            self._records[name] = rec
        self._save()
        return rec

    def record_evaluation(self, name: str, passed: bool, oos_sharpe: float,
                          regime: str = "UNKNOWN") -> ChallengerRecord:
        """记录一次 paper-trading/验证评估结果。"""
        rec = self._records.get(name) or self.enroll(name, regime)
        rec.evals.append({"ts": datetime.now().isoformat(),
                          "passed": passed, "oos_sharpe": round(oos_sharpe, 4)})
        if regime != "UNKNOWN":
            rec.regime = regime
        # 只保留最近 10 次
        rec.evals = rec.evals[-10:]
        self._save()
        return rec

    def ingest_promotion_verdicts(self, verdicts: List[Dict]) -> Dict:
        """把晋升闸门结果灌入考察记录 (一次评估)。"""
        enrolled, recorded = 0, 0
        for v in verdicts:
            name = v.get("strategy_name")
            if not name:
                continue
            if name not in self._records:
                self.enroll(name, v.get("regime", "UNKNOWN"))
                enrolled += 1
            self.record_evaluation(name, bool(v.get("passed")),
                                   float(v.get("mean_oos_sharpe", 0.0)),
                                   v.get("regime", "UNKNOWN"))
            recorded += 1
        return {"enrolled": enrolled, "evaluations_recorded": recorded}

    def graduate(self, name: str, approved_by: str, allocation: float = 0.1) -> Dict:
        """人工批准 challenger 毕业为 champion (安全闸门)。"""
        rec = self._records.get(name)
        if rec is None:
            return {"ok": False, "reason": "策略不存在"}
        if not rec.eligible_for_graduation():
            return {"ok": False, "reason": (
                f"未达毕业门槛: 评估{rec.n_evals}/{MIN_EVALS_TO_GRADUATE}, "
                f"通过率{rec.pass_rate:.0%}/{MIN_PASS_RATE:.0%}, "
                f"平均OOS夏普{rec.avg_oos_sharpe:.2f}/{MIN_AVG_OOS_SHARPE}")}
        rec.status = "champion"
        rec.approved_by = approved_by
        rec.allocation = allocation
        rec.graduated_at = datetime.now().isoformat()
        self._save()
        logger.info(f"[cc] {name} 毕业为 champion (批准人={approved_by}, 分配={allocation})")
        return {"ok": True, "name": name, "status": "champion", "allocation": allocation}

    def retire(self, name: str) -> Dict:
        rec = self._records.get(name)
        if rec is None:
            return {"ok": False, "reason": "策略不存在"}
        rec.status = "retired"
        rec.allocation = 0.0
        self._save()
        return {"ok": True, "name": name, "status": "retired"}

    def list_all(self) -> Dict:
        recs = list(self._records.values())
        return {
            "champions": [self._view(r) for r in recs if r.status == "champion"],
            "challengers": [self._view(r) for r in recs if r.status == "challenger"],
            "retired": [self._view(r) for r in recs if r.status == "retired"],
        }

    def _view(self, r: ChallengerRecord) -> Dict:
        return {"name": r.name, "status": r.status, "regime": r.regime,
                "n_evals": r.n_evals, "pass_rate": round(r.pass_rate, 3),
                "avg_oos_sharpe": round(r.avg_oos_sharpe, 4),
                "allocation": r.allocation, "approved_by": r.approved_by,
                "eligible": r.eligible_for_graduation()}


_registry: Optional[ChampionChallengerRegistry] = None


def get_registry() -> ChampionChallengerRegistry:
    global _registry
    if _registry is None:
        _registry = ChampionChallengerRegistry()
    return _registry
