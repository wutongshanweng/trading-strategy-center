from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config.settings import get_settings


_engine = None
async_engine = None
_async_session_maker = None


def get_engine():
    global _engine, async_engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.db_url, echo=settings.debug, pool_size=5, max_overflow=10)
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
