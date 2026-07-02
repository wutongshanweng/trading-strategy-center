"""全球指数实时行情 API — yfinance 主 + akshare 备 + 60s 缓存。"""

from __future__ import annotations

import logging
import time
from datetime import datetime

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["indices"])

_cache: tuple[float, list[dict]] | None = None
CACHE_TTL = 60

INDEX_MAP = {
    "^GSPC":  {"name": "S&P 500", "region": "US", "currency": "USD"},
    "^DJI":   {"name": "道琼斯", "region": "US", "currency": "USD"},
    "^IXIC":  {"name": "纳斯达克", "region": "US", "currency": "USD"},
    "^N225":  {"name": "日经225", "region": "JP", "currency": "JPY"},
    "^HSI":   {"name": "恒生指数", "region": "HK", "currency": "HKD"},
    "000001.SS": {"name": "上证指数", "region": "CN", "currency": "CNY"},
    "000300.SS": {"name": "沪深300", "region": "CN", "currency": "CNY"},
    "^FTSE":  {"name": "FTSE 100", "region": "UK", "currency": "GBP"},
    "^GDAXI": {"name": "DAX", "region": "DE", "currency": "EUR"},
    "^KS11":  {"name": "KOSPI", "region": "KR", "currency": "KRW"},
}


def _fetch_yf() -> list[dict]:
    import yfinance as yf
    import pandas as pd
    symbols = list(INDEX_MAP.keys())
    data = yf.download(symbols, period="2d", auto_adjust=True, timeout=15)
    if data.empty:
        raise RuntimeError("yfinance returned empty data")

    results = []
    for sym in symbols:
        try:
            if isinstance(data.columns, pd.MultiIndex):
                series = data.xs(sym, level=1, axis=1)
            else:
                series = data
            closes = series["Close"].dropna()
            opens = series["Open"].dropna()
            if closes.empty:
                continue
            price = float(closes.iloc[-1])
            prev_close = float(closes.iloc[-2]) if len(closes) >= 2 else (float(opens.iloc[0]) if not opens.empty else None)
            change = round(price - prev_close, 2) if prev_close else None
            change_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close and prev_close != 0 else None
            results.append({"symbol": sym, **INDEX_MAP[sym], "price": price, "change": change, "change_pct": change_pct, "timestamp": datetime.now().isoformat()})
        except Exception as e:
            logger.warning("yf parse fail %s: %s", sym, e)
    if not results:
        raise RuntimeError("no symbols parsed from yfinance")
    return results


def _fetch_akshare() -> list[dict]:
    import akshare as ak
    df = ak.index_global_spot_em()
    code_to_sym = {
        "SPX": "^GSPC", "DJI": "^DJI", "IXIC": "^IXIC",
        "N225": "^N225", "HSI": "^HSI", "KS11": "^KS11",
        "FTSE": "^FTSE", "GDAXI": "^GDAXI",
    }
    results = []
    for _, row in df.iterrows():
        code = str(row.iloc[1]).strip()
        if code in code_to_sym:
            sym = code_to_sym[code]
            meta = INDEX_MAP[sym]
            price = row.iloc[3]
            change = row.iloc[4]
            change_pct = row.iloc[5]
            results.append({
                "symbol": sym, **meta,
                "price": float(price) if price not in (None, "-") else None,
                "change": float(change) if change not in (None, "-") else None,
                "change_pct": float(change_pct) if change_pct not in (None, "-") else None,
                "timestamp": datetime.now().isoformat(),
            })
    return results


@router.get("/market/indices")
async def market_indices():
    global _cache
    now = time.time()

    # 缓存命中
    if _cache and (now - _cache[0]) < CACHE_TTL:
        return {"indices": _cache[1], "count": len(_cache[1])}

    results = []
    errors = []

    # 尝试 yfinance
    try:
        results = _fetch_yf()
    except Exception as e:
        errors.append(f"yfinance: {e}")

    # yfinance 失败, 尝试 akshare
    if not results:
        try:
            results = _fetch_akshare()
        except Exception as e:
            errors.append(f"akshare: {e}")

    # 都失败但有缓存, 返回过期缓存
    if not results:
        if _cache:
            logger.warning("both APIs failed, returning stale cache")
            return {"indices": _cache[1], "count": len(_cache[1]), "stale": True}
        # 无缓存, 返回最近已知参考值作为 fallback
        results = _fallback_data()
        logger.warning("using fallback data, APIs failed: %s", "; ".join(errors))

    _cache = (now, results)
    return {"indices": results, "count": len(results)}


_FALLBACK = {
    "^GSPC":  (5450.12, 15.23, 0.28),
    "^DJI":   (38950.45, -85.60, -0.22),
    "^IXIC":  (17680.30, 95.40, 0.54),
    "^N225":  (39620.50, 180.20, 0.46),
    "^HSI":   (18150.80, -120.30, -0.66),
    "000001.SS": (3050.15, -8.45, -0.28),
    "000300.SS": (3560.40, -12.60, -0.35),
    "^FTSE":  (8290.60, 35.20, 0.43),
    "^GDAXI": (18320.75, 95.30, 0.52),
    "^KS11":  (2810.90, 12.40, 0.44),
}


def _fallback_data() -> list[dict]:
    return [
        {"symbol": sym, **INDEX_MAP[sym], "price": p, "change": c, "change_pct": cp, "timestamp": datetime.now().isoformat(), "fallback": True}
        for sym, (p, c, cp) in _FALLBACK.items()
    ]
