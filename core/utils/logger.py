import sys
from loguru import logger


def setup_logger(debug: bool = True):
    logger.remove()
    level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:^7}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - {message}",
        level=level,
    )
    logger.add("logs/trading_{time:YYYY-MM-DD}.log", rotation="1 day", retention="30 days", level="INFO")
    return logger
