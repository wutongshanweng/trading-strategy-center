from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

try:
    from sqlalchemy.orm import Session
    from core.db.models import ParameterVersion as DBParameterVersion
except ImportError:
    Session = None
    DBParameterVersion = None


@dataclass
class ParameterVersion:
    version: int
    params: Dict[str, float]
    score: float
    strategy_name: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None


class ParameterStore:
    def __init__(self, base_path: str = "parameter_store", db_session: Optional[Any] = None):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, List[ParameterVersion]] = {}
        self.db_session = db_session

    def _strategy_dir(self, strategy_name: str) -> Path:
        d = self.base_path / strategy_name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _version_file(self, strategy_name: str) -> Path:
        return self._strategy_dir(strategy_name) / "versions.json"

    def _load_versions(self, strategy_name: str) -> List[ParameterVersion]:
        if strategy_name in self._cache:
            return self._cache[strategy_name]

        if self.db_session is not None and DBParameterVersion is not None:
            db_versions = (
                self.db_session.query(DBParameterVersion)
                .filter(DBParameterVersion.strategy_name == strategy_name)
                .order_by(DBParameterVersion.version)
                .all()
            )
            versions = [
                ParameterVersion(
                    version=db_v.version,
                    params=db_v.params,
                    score=db_v.score,
                    strategy_name=db_v.strategy_name,
                    timestamp=db_v.timestamp,
                    metadata=db_v.extra_metadata,
                )
                for db_v in db_versions
            ]
        else:
            vf = self._version_file(strategy_name)
            if vf.exists():
                with open(vf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                versions = [ParameterVersion(**v) for v in data]
            else:
                versions = []

        self._cache[strategy_name] = versions
        return versions

    def _save_versions(self, strategy_name: str, versions: List[ParameterVersion]) -> None:
        self._cache[strategy_name] = versions
        
        if self.db_session is not None and DBParameterVersion is not None:
            # Delete existing versions for this strategy
            self.db_session.query(DBParameterVersion).filter(
                DBParameterVersion.strategy_name == strategy_name
            ).delete()
            
            # Insert new versions
            for v in versions:
                db_v = DBParameterVersion(
                    strategy_name=v.strategy_name,
                    version=v.version,
                    params=v.params,
                    score=v.score,
                    timestamp=v.timestamp,
                    extra_metadata=v.metadata,
                )
                self.db_session.add(db_v)
            self.db_session.commit()
        else:
            vf = self._version_file(strategy_name)
            with open(vf, "w", encoding="utf-8") as f:
                json.dump([asdict(v) for v in versions], f, indent=2)

    def save(
        self,
        strategy_name: str,
        params: Dict[str, float],
        score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ParameterVersion:
        versions = self._load_versions(strategy_name)
        new_version = len(versions) + 1

        pv = ParameterVersion(
            version=new_version,
            params=params,
            score=score,
            strategy_name=strategy_name,
            timestamp=time.time(),
            metadata=metadata,
        )
        versions.append(pv)
        self._save_versions(strategy_name, versions)

        logger.info(
            f"Saved version {new_version} for {strategy_name} "
            f"(score={score:.6f})"
        )
        return pv

    def load_latest(self, strategy_name: str) -> Optional[ParameterVersion]:
        versions = self._load_versions(strategy_name)
        if not versions:
            return None
        return versions[-1]

    def load_version(
        self, strategy_name: str, version: int
    ) -> Optional[ParameterVersion]:
        versions = self._load_versions(strategy_name)
        for v in versions:
            if v.version == version:
                return v
        return None

    def list_versions(self, strategy_name: str) -> List[ParameterVersion]:
        return self._load_versions(strategy_name)

    def list_strategies(self) -> List[str]:
        """列出所有有参数版本记录的策略 (扫描 base_path 子目录)。"""
        if not self.base_path.exists():
            return []
        names = []
        for d in self.base_path.iterdir():
            if d.is_dir() and (d / "versions.json").exists():
                names.append(d.name)
        return sorted(names)

    def get_best(
        self, strategy_name: str, higher_is_better: bool = True
    ) -> Optional[ParameterVersion]:
        versions = self._load_versions(strategy_name)
        if not versions:
            return None
        if higher_is_better:
            return max(versions, key=lambda v: v.score)
        return min(versions, key=lambda v: v.score)

    def delete_version(self, strategy_name: str, version: int) -> bool:
        versions = self._load_versions(strategy_name)
        new_versions = [v for v in versions if v.version != version]
        if len(new_versions) == len(versions):
            return False
        self._save_versions(strategy_name, new_versions)
        return True

    def clear(self, strategy_name: str) -> None:
        self._save_versions(strategy_name, [])

    def export_strategy(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        versions = self._load_versions(strategy_name)
        if not versions:
            return None
        best = self.get_best(strategy_name)
        return {
            "strategy_name": strategy_name,
            "total_versions": len(versions),
            "best_version": asdict(best) if best else None,
            "history": [asdict(v) for v in versions],
        }

    def rollback(self, strategy_name: str, version: int) -> bool:
        versions = self._load_versions(strategy_name)
        target_version = None
        for v in versions:
            if v.version == version:
                target_version = v
                break
        
        if target_version is None:
            return False
        
        new_versions = [v for v in versions if v.version <= version]
        self._save_versions(strategy_name, new_versions)
        return True
