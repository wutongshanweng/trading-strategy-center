"""
全量历史数据下载编排器 (设计文档 Phase 1-6 顺序)。

特性:
- 断点续传: 进度写 data_center/download_checkpoint.json, 已完成的 key 跳过
- 网络容错: 单项失败不中断整体, 记录到 failures
- 限速: 每项之间 sleep, 避免被源封禁
- 分阶段: futures-D1 -> futures-M5 -> aggregate -> stocks -> options -> macro -> cross-market

用法:
    python -m scripts.download_all --phase futures-d1
    python -m scripts.download_all --phase all
    python -m scripts.download_all --resume
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict, List

from loguru import logger

from data_center.storage import get_store
from data_center.db.seed_loader import load_all
from data_center.collectors import (
    FuturesCollector, StocksCollector, OptionsCollector, MacroCollector,
)
from data_center.aggregator import aggregate_all
from data_center.cross_market import compute_all as compute_cross_market

_CKPT = Path(__file__).resolve().parent.parent / "data_center" / "download_checkpoint.json"


class Checkpoint:
    def __init__(self, path: Path = _CKPT):
        self.path = path
        self.data: Dict = self._load()

    def _load(self) -> Dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"done": [], "failures": {}, "stats": {}}

    def save(self):
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def is_done(self, key: str) -> bool:
        return key in self.data["done"]

    def mark_done(self, key: str, rows: int = 0):
        if key not in self.data["done"]:
            self.data["done"].append(key)
        self.data["stats"][key] = rows
        self.save()

    def mark_fail(self, key: str, err: str):
        self.data["failures"][key] = err
        self.save()


def _products(asset_type: str) -> List[str]:
    df = get_store().query(
        "SELECT code FROM products WHERE asset_type = ? ORDER BY code", [asset_type]
    )
    return df["code"].tolist()


def phase_futures(ckpt: Checkpoint, with_minute: bool, sleep: float = 0.3) -> Dict:
    """期货全合约 D1 (+M5)。逐品种逐合约, 断点续传。"""
    fc = FuturesCollector()
    totals = {"D1": 0, "M5": 0, "contracts": 0}
    for product in _products("futures"):
        try:
            contracts = fc.discover_contracts(product)
        except Exception as e:
            logger.warning(f"{product} 合约发现失败: {e}")
            ckpt.mark_fail(f"discover:{product}", str(e))
            continue
        for c in contracts:
            tf_tag = "M5" if with_minute else "D1"
            key = f"fut:{c}:{tf_tag}"
            if ckpt.is_done(key):
                continue
            try:
                res = fc.collect_contract(c, product, with_minute=with_minute)
                rows = sum(res.values())
                totals["D1"] += res.get("D1", 0)
                totals["M5"] += res.get("M5", 0)
                totals["contracts"] += 1
                ckpt.mark_done(key, rows)
                logger.info(f"{c}: {res}")
            except Exception as e:
                logger.warning(f"{c} 采集失败: {e}")
                ckpt.mark_fail(key, str(e))
            time.sleep(sleep)
    return totals


def phase_stocks(ckpt: Checkpoint, sleep: float = 0.5) -> Dict:
    sc = StocksCollector()
    totals = {"rows": 0, "stocks": 0}
    for code in _products("stock"):
        key = f"stk:{code}:D1"
        if ckpt.is_done(key):
            continue
        try:
            n = sc.collect_kline(code)
            totals["rows"] += n
            totals["stocks"] += 1
            ckpt.mark_done(key, n)
            logger.info(f"{code}: {n} 日线")
        except Exception as e:
            logger.warning(f"{code} 股票采集失败: {e}")
            ckpt.mark_fail(key, str(e))
        time.sleep(sleep)
    return totals


def phase_macro(ckpt: Checkpoint) -> Dict:
    mc = MacroCollector()
    res = {}
    for code, n in mc.collect_all().items():
        ckpt.mark_done(f"macro:{code}", n)
        res[code] = n
    return res


def phase_aggregate(ckpt: Checkpoint) -> Dict:
    res = aggregate_all()
    ckpt.mark_done("aggregate:all", sum(res.values()))
    return res


def phase_cross_market(ckpt: Checkpoint) -> int:
    n = compute_cross_market()
    ckpt.mark_done("cross_market:all", n)
    return n


def run(phase: str, with_minute: bool = True) -> Dict:
    ckpt = Checkpoint()
    load_all()  # 确保 products/cross-market 种子就绪 (幂等)
    results: Dict = {}

    if phase in ("futures-d1", "futures", "all"):
        results["futures"] = phase_futures(ckpt, with_minute=(phase != "futures-d1") and with_minute)
    if phase in ("stocks", "all"):
        results["stocks"] = phase_stocks(ckpt)
    if phase in ("macro", "all"):
        results["macro"] = phase_macro(ckpt)
    if phase in ("aggregate", "all"):
        results["aggregate"] = phase_aggregate(ckpt)
    if phase in ("cross-market", "all"):
        results["cross_market"] = phase_cross_market(ckpt)

    logger.info(f"完成阶段 [{phase}]: {results}")
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--phase", default="all",
                   choices=["futures-d1", "futures", "aggregate", "stocks", "macro",
                            "cross-market", "all"])
    p.add_argument("--no-minute", action="store_true", help="期货仅下载 D1, 跳过 M5")
    args = p.parse_args()
    out = run(args.phase, with_minute=not args.no_minute)
    print(json.dumps(out, ensure_ascii=False, indent=2))
