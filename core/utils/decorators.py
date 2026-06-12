import asyncio
import functools
import time
from typing import Type, Tuple
from loguru import logger


def retry(max_attempts: int = 3, delay: float = 1.0,
          backoff: float = 2.0,
          exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_attempts:
                        wait = delay * (backoff ** (attempt - 1))
                        logger.warning(f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}, retrying in {wait:.1f}s")
                        await asyncio.sleep(wait)
            raise last_exc
        return async_wrapper
    return decorator


def timed(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper


def log_call(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger.debug(f"→ {func.__name__}")
        result = await func(*args, **kwargs)
        logger.debug(f"← {func.__name__}")
        return result
    return wrapper
