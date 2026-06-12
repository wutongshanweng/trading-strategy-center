from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from core.exceptions import AppException

_HTTP_CODE_MAP = {
    4: 400, 41: 400, 42: 400, 43: 422, 44: 422,
    5: 500, 50: 500, 51: 503, 52: 502, 53: 503,
}


def _code_to_http(code: int) -> int:
    prefix = code // 100
    return _HTTP_CODE_MAP.get(prefix, min(prefix, 511))


async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(f"{exc.code} {exc.message} | {request.url.path}")
    return JSONResponse(
        status_code=_code_to_http(exc.code),
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled: {exc} | {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"code": 50000, "message": "Internal server error"},
    )
