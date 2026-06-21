"""实时同步调度器 — 服务端常驻, 定时增量同步市场数据。

生产特性 (设好就不用管):
- 关注品种持久化 (data/sync_watchlist.json), 重启不丢
- main.py lifespan 自动拉起 (读持久化列表, 服务器起来就跑)
- 支持期货/股票/期权三类, 各品种独立间隔
- 关网页不影响 (服务端 asyncio 常驻); 重启自恢复

注意: 与全量采集任务 (CollectJobs) 共享 DuckDB 写锁, 有全量在跑时本轮跳过。
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

_WATCHLIST_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "sync_watchlist.json"


@dataclass
class SyncConfig:
    """单品种同步配置。"""
    symbol: str                       # 期货品种码RB / 股票600019.SH / 期权标的510050
    asset_type: str = "futures"       # futures / stock / option
    with_minute: bool = False         # 是否同采分钟线
    enabled: bool = True
    sync_interval_seconds: int = 300  # 该品种多久同步一次
    last_sync: float = 0.0            # 上次同步时间戳 (运行时)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("last_sync", None)      # 运行时态不持久化
        return d


class SyncScheduler:
    """实时同步调度器 (常驻 + 持久化 + 多资产)。"""

    def __init__(self, download_mgr=None, data_store=None):
        self._dl_mgr = download_mgr
        self._store = data_store
        self._configs: Dict[str, SyncConfig] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._auto_start = False   # 持久化: 服务器重启后是否自动恢复运行
        self._load()

    # ---- 持久化 ----
    def _key(self, asset_type: str, symbol: str) -> str:
        return f"{asset_type}:{symbol.upper()}"

    def _load(self) -> None:
        if not _WATCHLIST_FILE.exists():
            return
        try:
            data = json.loads(_WATCHLIST_FILE.read_text(encoding="utf-8"))
            self._auto_start = bool(data.get("auto_start", False))
            for c in data.get("configs", []):
                cfg = SyncConfig(**c)
                self._configs[self._key(cfg.asset_type, cfg.symbol)] = cfg
            logger.info(f"[sync] 恢复 {len(self._configs)} 个关注品种, auto_start={self._auto_start}")
        except Exception as e:
            logger.warning(f"[sync] 关注列表读取失败: {e}")

    def _save(self) -> None:
        try:
            _WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
            payload = {"updated_at": datetime.now().isoformat(),
                       "auto_start": self._auto_start,
                       "configs": [c.to_dict() for c in self._configs.values()]}
            _WATCHLIST_FILE.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"[sync] 关注列表持久化失败: {e}")

    # ---- 品种管理 ----
    def add_symbol(self, symbol: str, asset_type: str = "futures",
                   with_minute: bool = False, sync_seconds: int = 300) -> SyncConfig:
        cfg = SyncConfig(symbol=symbol.upper(), asset_type=asset_type,
                         with_minute=with_minute, sync_interval_seconds=sync_seconds)
        self._configs[self._key(asset_type, symbol)] = cfg
        self._save()
        return cfg

    def remove_symbol(self, symbol: str, asset_type: str = "futures") -> None:
        self._configs.pop(self._key(asset_type, symbol), None)
        self._save()

    # ---- 调度 ----
    async def start(self) -> None:
        if self._running:
            logger.warning("[sync] 调度器已在运行")
            return
        self._running = True
        self._auto_start = True   # 标记: 重启后自动恢复
        self._save()
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"[sync] 调度器启动, {len(self._configs)} 个品种")

    async def stop(self) -> None:
        self._running = False
        self._auto_start = False  # 用户主动停止 → 重启后不再自启
        self._save()
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("[sync] 调度器停止")

    async def autostart_if_enabled(self) -> bool:
        """服务器启动时调用: 若上次是运行态则自动恢复。"""
        if self._auto_start and not self._running:
            await self.start()
            logger.info("[sync] 服务器重启后自动恢复实时同步")
            return True
        return False

    async def _run_loop(self) -> None:
        while self._running:
            now = time.time()
            for cfg in list(self._configs.values()):
                if not cfg.enabled:
                    continue
                # 尊重各品种独立间隔
                if now - cfg.last_sync < cfg.sync_interval_seconds:
                    continue
                try:
                    await self._sync_one(cfg)
                    cfg.last_sync = time.time()
                except Exception as e:
                    logger.error(f"[sync] {cfg.asset_type}:{cfg.symbol} 失败: {e}")
            await asyncio.sleep(30)  # 每 30 秒检查一次到期品种

    async def _sync_one(self, cfg: SyncConfig) -> bool:
        """按资产类型增量同步单品种 (近1月)。有全量任务在跑则跳过 (避免写锁争用)。"""
        from .collect_jobs import get_jobs
        if get_jobs().is_running():
            logger.debug(f"[sync] 全量任务运行中, 跳过 {cfg.symbol}")
            return False
        start = (datetime.now() - timedelta(days=31)).strftime("%Y-%m-%d")
        if cfg.asset_type == "futures":
            from ..collectors import FuturesCollector
            fc = FuturesCollector()
            res = await asyncio.to_thread(fc.collect_product, cfg.symbol, cfg.with_minute, 0.3, start)
        elif cfg.asset_type == "stock":
            from ..collectors import StocksCollector
            sc = StocksCollector()
            res = await asyncio.to_thread(sc.collect_kline, cfg.symbol, start)
        elif cfg.asset_type == "option":
            from ..collectors import OptionsCollector
            oc = OptionsCollector()
            # ETF 期权标的: 刷当前在挂合约
            res = await asyncio.to_thread(self._sync_option_underlying, oc, cfg.symbol)
        else:
            logger.warning(f"[sync] 未知资产类型: {cfg.asset_type}")
            return False
        logger.info(f"[sync] {cfg.asset_type}:{cfg.symbol} -> {res}")
        return True

    @staticmethod
    def _sync_option_underlying(oc, underlying: str) -> Dict[str, int]:
        """同步某 ETF 期权标的的当前在挂合约 (看涨+看跌)。"""
        total = {"rows": 0, "contracts": 0}
        for otype in ("看涨期权", "看跌期权"):
            try:
                cdf = oc._opt.get_etf_option_codes(option_type=otype, underlying=underlying)
                col = next((c for c in ("期权代码", "合约代码", "代码")
                            if cdf is not None and not cdf.empty and c in cdf.columns), None)
                if not col:
                    continue
                for c in [str(x) for x in cdf[col].tolist()]:
                    n = oc.collect_etf_option_daily(c, underlying)
                    total["rows"] += n
                    if n > 0:
                        total["contracts"] += 1
            except Exception as e:
                logger.warning(f"[sync] 期权 {underlying}/{otype} 失败: {e}")
        return total

    # ---- 状态 ----
    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "symbols": len(self._configs),
            "configs": [
                {"symbol": c.symbol, "asset_type": c.asset_type,
                 "with_minute": c.with_minute, "enabled": c.enabled,
                 "interval_s": c.sync_interval_seconds,
                 "last_sync": datetime.fromtimestamp(c.last_sync).isoformat() if c.last_sync else None}
                for c in self._configs.values()
            ],
        }

    def get_configs(self) -> List[SyncConfig]:
        return list(self._configs.values())
