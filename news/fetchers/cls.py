"""财联社快讯采集器 — 多源容错。

抓取顺序 (任一成功即用):
1. akshare stock_info_global_cls (财联社电报)
2. akshare stock_info_global_em (东财全球财经快讯)
3. 内置种子数据 (全部失败时, 保证页面非空)

网络维护/2026 时钟下远程可能拉不到, 因此全部容错, 不抛异常。
"""

from __future__ import annotations

import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List

from loguru import logger


# 种子快讯 (全部数据源失败时的兜底, 标注为 seed 源)
_SEED_NEWS: List[Dict] = [
    {"title": "国家统计局: 制造业PMI回升至扩张区间, 工业品需求边际改善",
     "content": "最新制造业PMI录得50.8, 较上月回升0.5个百分点, 重回荣枯线上方, 钢材、有色等工业品需求预期改善。"},
    {"title": "央行: 保持流动性合理充裕, M2同比增长8.3%",
     "content": "央行发布数据显示货币供应量保持稳健增长, 市场流动性充裕, 利好风险资产。"},
    {"title": "钢材社会库存连续三周下降, 螺纹钢现货价格企稳回升",
     "content": "Mysteel数据显示主要钢材品种社会库存去化加速, 表观需求回升, 螺纹钢价格突破前期平台。"},
    {"title": "铁矿石港口库存小幅累库, 价格承压回落",
     "content": "45港铁矿石库存环比增加, 钢厂补库意愿不强, 矿价短期偏弱震荡。"},
    {"title": "美联储官员暗示年内或维持高利率, 黄金价格高位回落",
     "content": "市场对降息预期降温, 贵金属承压, 但避险需求仍提供支撑。"},
    {"title": "OPEC+维持减产协议不变, 国际原油价格小幅上涨",
     "content": "供给端收紧预期支撑油价, SC原油主力合约走强。"},
    {"title": "豆粕: 美豆产区天气良好, 进口大豆到港量增加, 价格回落",
     "content": "供应宽松格局下豆粕承压, 关注后续生猪存栏恢复带来的需求支撑。"},
    {"title": "沪铜: 全球制造业回暖叠加库存低位, 铜价震荡走高",
     "content": "LME库存持续下降, 国内现货升水扩大, 铜价获得支撑。"},
]


class CLSNewsFetcher:
    """财联社/东财快讯采集器 (多源容错)。"""

    def __init__(self):
        self._ak = None

    def _get_ak(self):
        if self._ak is None:
            import akshare as ak
            self._ak = ak
        return self._ak

    def _from_cls(self, limit: int) -> List[Dict]:
        ak = self._get_ak()
        df = ak.stock_info_global_cls(symbol="全部")
        rows: List[Dict] = []
        for _, r in df.head(limit).iterrows():
            title = str(r.get("标题") or r.get("title") or "").strip()
            content = str(r.get("内容") or r.get("content") or title).strip()
            pub_date = str(r.get("发布日期") or "")
            pub_time = str(r.get("发布时间") or "")
            ts = f"{pub_date} {pub_time}".strip() or datetime.now().isoformat()
            if title or content:
                rows.append({"title": title or content[:40], "content": content,
                             "timestamp": ts, "source": "财联社"})
        return rows

    def _from_em(self, limit: int) -> List[Dict]:
        ak = self._get_ak()
        df = ak.stock_info_global_em()
        rows: List[Dict] = []
        for _, r in df.head(limit).iterrows():
            title = str(r.get("标题") or "").strip()
            content = str(r.get("摘要") or title).strip()
            ts = str(r.get("发布时间") or datetime.now().isoformat())
            if title:
                rows.append({"title": title, "content": content,
                             "timestamp": ts, "source": "东方财富"})
        return rows

    def _seed(self) -> List[Dict]:
        now = datetime.now()
        rows = []
        for i, n in enumerate(_SEED_NEWS):
            ts = (now - timedelta(minutes=15 * i)).isoformat()
            rows.append({**n, "timestamp": ts, "source": "seed"})
        return rows

    def fetch(self, limit: int = 80, timeout: float = 12.0) -> List[Dict]:
        """抓取最新快讯, 多源容错 + 单源超时。返回 [{title, content, timestamp, source}]。"""
        for name, fn in (("cls", self._from_cls), ("em", self._from_em)):
            ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            try:
                rows = ex.submit(fn, limit).result(timeout=timeout)
                if rows:
                    logger.info(f"[news] fetched {len(rows)} items from {name}")
                    return rows
            except concurrent.futures.TimeoutError:
                logger.warning(f"[news] source {name} timed out after {timeout}s")
            except Exception as e:
                logger.warning(f"[news] source {name} failed: {type(e).__name__}: {e}")
            finally:
                ex.shutdown(wait=False)  # 不等待挂起的慢调用
        logger.warning("[news] all live sources failed, using seed data")
        return self._seed()
