from tasks.celery_app import celery_app
from loguru import logger
import numpy as np
import asyncio
import pandas as pd


def _generate_ohlcv(symbol, start_date, end_date):
    np.random.seed(hash(f"{symbol}_{start_date}") % (2**31))
    n = max((pd.to_datetime(end_date) - pd.to_datetime(start_date)).days, 252)
    returns = np.random.normal(0.0005, 0.01, n)
    close = 100.0 * np.exp(np.cumsum(returns))
    return pd.DataFrame({
        "open": close * np.exp(np.random.normal(0, 0.002, n)),
        "high": close * np.exp(np.abs(np.random.normal(0, 0.005, n))),
        "low": close * np.exp(-np.abs(np.random.normal(0, 0.005, n))),
        "close": close,
        "volume": np.random.randint(10000, 1000000, n),
    }, index=pd.date_range(start=start_date, periods=n))


def _run_vectorized_backtest(symbol, strategy_name, start_date, end_date, initial_capital):
    from signals.registry import get_strategy
    from backtest.vectorized_engine import VectorizedBacktest
    df = _generate_ohlcv(symbol, start_date, end_date)
    strategy_cls = get_strategy(strategy_name)
    if strategy_cls is None:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    strategy = strategy_cls()
    bt = VectorizedBacktest(initial_capital=initial_capital)
    return bt.run(df, strategy, symbol)


async def _save_backtest_result(result, symbol, strategy_name, start_date="", end_date=""):
    from core.db.session import get_session_maker
    from core.db.models import BacktestResult
    Session = get_session_maker()
    async with Session() as session:
        session.add(BacktestResult(
            name=f"{strategy_name}_{symbol}_{start_date}",
            strategy=strategy_name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            total_return=result.total_return,
            sharpe_ratio=result.sharpe_ratio,
            max_drawdown=getattr(result, "max_drawdown", 0.0),
            win_rate=getattr(result, "win_rate", 0.0),
            total_trades=getattr(result, "total_trades", 0),
            params=None,
        ))
        await session.commit()


@celery_app.task(name="run_backtest", bind=True, max_retries=3, acks_late=True)
def run_backtest(self, symbol, strategy_name, start_date, end_date, initial_capital=1_000_000):
    try:
        logger.info(f"run_backtest: {symbol} {strategy_name} {start_date}-{end_date}")
        result = _run_vectorized_backtest(symbol, strategy_name, start_date, end_date, initial_capital)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_save_backtest_result(result, symbol, strategy_name, start_date, end_date))
        finally:
            loop.close()
        return {
            "status": "success", "symbol": symbol, "strategy": strategy_name,
            "total_return": float(result.total_return),
            "sharpe_ratio": float(result.sharpe_ratio),
            "max_drawdown": float(getattr(result, "max_drawdown", 0.0)),
            "n_trades": int(getattr(result, "total_trades", 0)),
        }
    except Exception as e:
        logger.error(f"run_backtest failed: {e}")
        countdown = min(60 * (2 ** self.request.retries), 3600)
        raise self.retry(exc=e, countdown=countdown)


@celery_app.task(name="compare_strategies")
def compare_strategies(symbol, start_date, end_date, initial_capital=1_000_000):
    from signals.registry import list_strategies
    comparison = []
    for name in list_strategies():
        try:
            result = _run_vectorized_backtest(symbol, name, start_date, end_date, initial_capital)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_save_backtest_result(result, symbol, name, start_date, end_date))
            finally:
                loop.close()
            comparison.append({
                "strategy": name,
                "total_return": float(result.total_return),
                "sharpe_ratio": float(result.sharpe_ratio),
                "max_drawdown": float(getattr(result, "max_drawdown", 0.0)),
                "n_trades": int(getattr(result, "total_trades", 0)),
            })
        except Exception as e:
            comparison.append({"strategy": name, "error": str(e)})
    comparison.sort(key=lambda r: r.get("sharpe_ratio", -999), reverse=True)
    return {"status": "success", "symbol": symbol, "comparison": comparison}
