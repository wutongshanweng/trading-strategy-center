import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config.settings import get_settings


_engine = None
async_engine = None
_async_session_maker = None


def get_db_url() -> str:
    """
    获取数据库 URL。
    优先使用环境变量 DB_URL_OVERRIDE (初始化脚本使用),
    否则使用 settings.py 中的配置。
    """
    override = os.environ.get("DB_URL_OVERRIDE")
    if override:
        return override
    return get_settings().db_url


def get_engine():
    global _engine, async_engine
    if _engine is None:
        url = get_db_url()
        # SQLite 不支持 pool_size/max_overflow, 只有 PostgreSQL 需要
        if url.startswith("sqlite"):
            _engine = create_async_engine(url, echo=False)
        else:
            _engine = create_async_engine(url, echo=False, pool_size=5, max_overflow=10)
        async_engine = _engine
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _async_session_maker


async def get_session() -> AsyncSession:
    async with get_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
