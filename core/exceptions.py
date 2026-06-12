from typing import Optional, Any


class AppException(Exception):
    code: int = 50000
    message: str = "Internal server error"
    detail: Optional[Any] = None

    def __init__(self, message: str = None, detail: Any = None):
        if message:
            self.message = message
        if detail is not None:
            self.detail = detail
        super().__init__(self.message)


class DataException(AppException):
    code: int = 40001
    message: str = "Data error"


class StrategyException(AppException):
    code: int = 41000
    message: str = "Strategy error"


class TradingException(AppException):
    code: int = 42000
    message: str = "Trading error"


class BacktestException(AppException):
    code: int = 43000
    message: str = "Backtest error"


class ConfigException(AppException):
    code: int = 44000
    message: str = "Configuration error"


class InsufficientDataError(DataException):
    code: int = 40002
    message: str = "Insufficient data quality"


class PositionLimitExceeded(TradingException):
    code: int = 42002
    message: str = "Position limit exceeded"


class StrategyNotFound(StrategyException):
    code: int = 41002
    message: str = "Strategy not registered"
