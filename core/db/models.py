from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Date, Enum, Text, JSON, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
import enum
from typing import Optional


class Base(DeclarativeBase):
    pass


class SignalDirection(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class AlertLevel(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class PositionStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


# ========================
# 核心数据表
# ========================

class Contract(Base):
    """品种合约信息表"""
    __tablename__ = "contracts"
    __table_args__ = (
        Index("idx_contract_exchange", "exchange"),
        Index("idx_contract_category", "category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="品种中文名")
    exchange: Mapped[str] = mapped_column(String(20), nullable=False, comment="交易所 SHFE/DCE/CZCE/CFFEX/INE/GFEX")
    category: Mapped[str] = mapped_column(String(20), nullable=False, comment="分类 metal/energy/chemical/agri/equity/rate")
    multiplier: Mapped[int] = mapped_column(Integer, default=1, comment="合约乘数")
    min_tick: Mapped[float] = mapped_column(Float, default=0.01, comment="最小变动价位")
    margin_rate: Mapped[float] = mapped_column(Float, default=0.1, comment="保证金比例")
    commission: Mapped[float] = mapped_column(Float, default=0.0, comment="手续费")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    delivery_months: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="交割月份列表,逗号分隔")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Kline(Base):
    """K线数据表"""
    __tablename__ = "klines"
    __table_args__ = (
        UniqueConstraint("symbol", "period", "timestamp"),
        Index("idx_kline_symbol_period", "symbol", "period"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20))
    period: Mapped[str] = mapped_column(String(10))
    timestamp: Mapped[datetime]
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    open_interest: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# ========================
# 策略与信号表
# ========================

class Signal(Base):
    """交易信号表"""
    __tablename__ = "signals"
    __table_args__ = (
        UniqueConstraint("contract", "period", "timestamp", "strategy_name"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    contract: Mapped[str] = mapped_column(String(20))
    period: Mapped[str] = mapped_column(String(10))
    timestamp: Mapped[datetime]
    strategy_name: Mapped[str] = mapped_column(String(50))
    direction: Mapped[str] = mapped_column(String(10))
    confidence: Mapped[float] = mapped_column(Float)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class ParameterVersion(Base):
    """策略参数版本表"""
    __tablename__ = "parameter_versions"
    __table_args__ = (
        UniqueConstraint("strategy_name", "version", name="uq_strategy_version"),
        Index("idx_parameter_strategy_name", "strategy_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_name: Mapped[str] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer)
    params: Mapped[dict] = mapped_column(JSON)
    score: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[float] = mapped_column(Float)
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# ========================
# 交易与持仓表
# ========================

class Position(Base):
    """持仓表"""
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20))
    direction: Mapped[str] = mapped_column(String(10))
    quantity: Mapped[int] = mapped_column(Integer)
    entry_price: Mapped[float] = mapped_column(Float)
    current_price: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    take_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    strategy: Mapped[str] = mapped_column(String(100), default="", comment="关联策略名称")
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    opened_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class TradeRecord(Base):
    """成交记录表"""
    __tablename__ = "trade_records"
    __table_args__ = (
        Index("idx_trade_symbol_time", "symbol", "entry_time"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer)
    entry_time: Mapped[datetime]
    exit_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    pnl_pct: Mapped[float] = mapped_column(Float, default=0.0)
    strategy: Mapped[str] = mapped_column(String(100))
    stop_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    take_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# ========================
# 回测与表现表
# ========================

class BacktestResult(Base):
    """回测结果表"""
    __tablename__ = "backtest_results"
    __table_args__ = (
        UniqueConstraint("symbol", "strategy", "start_date", "end_date", name="uq_backtest_run"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    strategy: Mapped[str] = mapped_column(String(50))
    symbol: Mapped[str] = mapped_column(String(20))
    start_date: Mapped[str] = mapped_column(String(10))
    end_date: Mapped[str] = mapped_column(String(10))
    total_return: Mapped[float] = mapped_column(Float)
    sharpe_ratio: Mapped[float] = mapped_column(Float)
    max_drawdown: Mapped[float] = mapped_column(Float)
    win_rate: Mapped[float] = mapped_column(Float)
    total_trades: Mapped[int] = mapped_column(Integer)
    params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class PerformanceSnapshot(Base):
    """每日表现快照表"""
    __tablename__ = "performance_snapshots"
    __table_args__ = (
        UniqueConstraint("snapshot_date", "strategy_name", name="uq_snapshot_strategy"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    total_equity: Mapped[float] = mapped_column(Float, default=0.0)
    cash: Mapped[float] = mapped_column(Float, default=0.0)
    positions_value: Mapped[float] = mapped_column(Float, default=0.0)
    daily_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    total_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    drawdown: Mapped[float] = mapped_column(Float, default=0.0)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="扩展指标JSON")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# ========================
# ML 模型表
# ========================

class ModelVersion(Base):
    """ML模型版本管理表"""
    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("model_name", "version", name="uq_model_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="训练指标")
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    trained_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# ========================
# 锦标赛表
# ========================

class TournamentStrategy(Base):
    """参赛策略注册表"""
    __tablename__ = "tournament_strategies"
    __table_args__ = (
        UniqueConstraint("strategy_name", "tournament_round", name="uq_tournament_strategy"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tournament_round: Mapped[int] = mapped_column(Integer, default=1)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    sharpe: Mapped[float] = mapped_column(Float, default=0.0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    total_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_eliminated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class TournamentRecord(Base):
    """锦标赛轮次记录表"""
    __tablename__ = "tournament_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, comment="DUEL/TOURNAMENT/EXPLORATION")
    total_strategies: Mapped[int] = mapped_column(Integer, default=0)
    eliminated_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# ========================
# 监控告警表
# ========================

class MonitorRule(Base):
    """告警规则表"""
    __tablename__ = "monitor_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="规则名称")
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="规则类型: drawdown/var/volume/signal")
    symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    params: Mapped[dict] = mapped_column(JSON, nullable=False, comment="规则参数JSON")
    level: Mapped[str] = mapped_column(String(20), default="WARNING")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class MonitorAlert(Base):
    """告警记录表"""
    __tablename__ = "monitor_alerts"
    __table_args__ = (
        Index("idx_alert_level_time", "level", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rule_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rule_name: Mapped[str] = mapped_column(String(100))
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[Text] = mapped_column(Text, nullable=False)
    symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    metric_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
