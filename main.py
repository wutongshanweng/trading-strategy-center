import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from core.config.settings import get_settings
from core.utils.logger import setup_logger
from api.middleware.error_handler import app_exception_handler, unhandled_exception_handler
from core.exceptions import AppException
from api.routes.health_routes import router as health_router
from api.routes.data_routes import router as data_router
from api.routes.strategy_routes import router as strategy_router
from api.routes.trading_routes import router as trading_router
from api.routes.backtest_routes import router as backtest_router
from api.routes.portfolio_routes import router as portfolio_router
from api.routes.ml_routes import router as ml_router
from api.routes.intelligence_routes import router as intelligence_router
from api.routes.tournament_routes import router as tournament_router
from api.routes.llm_routes import router as llm_router
from api.routes.db_routes import router as db_router
from api.routes.factor_routes import router as factor_router
from api.routes.phase3_routes import router as phase3_router
from api.routes.feedback_routes import router as feedback_router
from api.routes.mlopts_routes import router as mlopts_router
from api.routes.macro_news_routes import router as macro_news_router
from api.routes.alert_routes import router as alert_router
from api.routes.simulated_trading_routes import router as simulated_trading_router
from api.websocket.trading_stream import router as ws_router, start_periodic_updates
from data_center.api import router as data_center_router
from data_center.api.warehouse import router as warehouse_router
from api.routes.fundamental_routes import router as fundamental_router
from api.routes.news_routes import router as news_router
from api.routes.market_intelligence_routes import router as market_intelligence_router
from api.routes.vstock_routes import router as vstock_router
from api.routes.vibe_routes import router as vibe_router
from api.routes.china_finance_routes import router as china_finance_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logger(debug=settings.debug)
    logger.info("Trading Strategy Center starting...")
    _start_background_refresh()
    # 触发数据库引擎初始化（延迟加载）
    from core.db.session import get_engine
    get_engine()
    # 启动时自动抓取新闻 (在后台线程执行, 避免 GIL 问题)
    try:
        import asyncio
        from api.routes.news_routes import bootstrap_news
        asyncio.create_task(bootstrap_news())
        logger.info("[bootstrap] 新闻抓取已启动")
    except Exception as e:
        logger.warning(f"[bootstrap] 新闻抓取失败: {e}")
    # 实时同步调度器: 若上次为运行态则自动恢复 (重启自恢复)
    try:
        from data_center.api import _scheduler
        await _scheduler.autostart_if_enabled()
    except Exception as e:
        logger.warning(f"实时同步自启失败: {e}")
    yield
    from core.db.session import async_engine
    if async_engine is not None:
        await async_engine.dispose()
    logger.info("Shutting down.")


def _start_background_refresh():
    """后台线程: 定时刷新新闻缓存(30min) 与信号扫描(15min)。

    daemon 线程, 随主进程退出。首轮延迟启动避免拖慢启动。
    """
    import threading
    import time

    def _loop():
        time.sleep(20)  # 启动后稍等, 避免与首批请求争抢
        news_every, scan_every = 1800, 300  # 新闻30min / 信号扫描5min
        auto_check_every = 3600  # 每小时检查一次是否到自动迭代周期
        last_news = last_scan = last_auto = 0.0
        while True:
            now = time.time()
            if now - last_news >= news_every:
                try:
                    from news.pipeline import get_pipeline
                    get_pipeline().refresh()
                except Exception as e:
                    logger.warning(f"[bg] news refresh failed: {e}")
                last_news = now
            if now - last_scan >= scan_every:
                try:
                    from signals.alert_aggregator import get_aggregator
                    get_aggregator().run_once()
                except Exception as e:
                    logger.warning(f"[bg] signal scan failed: {e}")
                last_scan = now
            if now - last_auto >= auto_check_every:
                try:
                    import asyncio
                    from core.adaptive.auto_iteration import should_run_now, run_safe_cycle
                    if should_run_now():
                        logger.info("[bg] auto-iteration cycle triggered")
                        asyncio.run(run_safe_cycle(trigger="scheduled"))
                except Exception as e:
                    logger.warning(f"[bg] auto-iteration failed: {e}")
                last_auto = now
            time.sleep(60)

    t = threading.Thread(target=_loop, name="bg-refresh", daemon=True)
    t.start()
    logger.info("Background refresh thread started (news 30min / signals 15min / auto-iteration hourly-check)")


settings = get_settings()
app = FastAPI(
    title="Trading Strategy Center",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=bool(settings.cors_origins != ["*"]),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(health_router)
app.include_router(data_router)
app.include_router(strategy_router)
app.include_router(trading_router)
app.include_router(backtest_router)
app.include_router(portfolio_router)
app.include_router(ml_router)
app.include_router(intelligence_router)
app.include_router(tournament_router)
app.include_router(llm_router)
app.include_router(db_router)
app.include_router(factor_router)
app.include_router(phase3_router)
app.include_router(feedback_router)
app.include_router(mlopts_router)
app.include_router(macro_news_router)
app.include_router(alert_router)
app.include_router(simulated_trading_router)
app.include_router(ws_router)
app.include_router(data_center_router)
app.include_router(warehouse_router)
app.include_router(fundamental_router)
app.include_router(news_router)
app.include_router(market_intelligence_router)
app.include_router(vstock_router)
app.include_router(vibe_router)
app.include_router(china_finance_router)


if __name__ == "__main__":
    import os
    import uvicorn
    # 默认单进程运行 — DuckDB 是单进程独占锁, --reload 的双进程会冲突,
    # 且长时下载任务会被文件改动重启打断。开发期可设 DEV_RELOAD=1 开启热重载。
    dev_reload = os.getenv("DEV_RELOAD") == "1"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=dev_reload)
