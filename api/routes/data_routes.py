from fastapi import APIRouter, Depends, Query, HTTPException
from core.data.market_data_manager import MarketDataManager

router = APIRouter(prefix="/api/v1/data", tags=["data"])
_data_manager = None
_MAX_KLINE_ROWS = 5000


def get_data_manager():
    global _data_manager
    if _data_manager is None:
        _data_manager = MarketDataManager()
    return _data_manager


def _validate_symbol(symbol: str):
    if not symbol or len(symbol) > 20 or not symbol.isascii():
        raise HTTPException(status_code=400, detail=f"Invalid symbol: {symbol}")


@router.get("/kline/{symbol}")
async def get_kline(symbol: str, timeframe: str = Query("1d"),
                    start: str = Query(None), end: str = Query(None),
                    limit: int = Query(1000, le=_MAX_KLINE_ROWS),
                    dm: MarketDataManager = Depends(get_data_manager)):
    _validate_symbol(symbol)
    feed = await dm.get_data_feed(symbol, timeframe, start, end)
    klines = []
    for ts, row in feed.df.head(limit).iterrows():
        klines.append({
            "timestamp": str(ts)[:19],
            "open": float(row["open"]), "high": float(row["high"]),
            "low": float(row["low"]), "close": float(row["close"]),
            "volume": float(row.get("volume", 0)),
        })
    return {
        "symbol": symbol, "timeframe": timeframe,
        "quality_score": feed.quality_score,
        "start": feed.start_date, "end": feed.end_date,
        "klines": klines, "total": len(klines),
    }


@router.get("/symbols")
async def list_symbols(dm: MarketDataManager = Depends(get_data_manager)):
    symbols = await dm.list_available_symbols()
    return {"symbols": symbols}


@router.get("/quality/{symbol}")
async def check_quality(symbol: str, dm: MarketDataManager = Depends(get_data_manager)):
    _validate_symbol(symbol)
    try:
        feed = await dm.get_data_feed(symbol, "1d")
        return {"symbol": symbol, "quality_score": feed.quality_score, "rows": len(feed.df)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
