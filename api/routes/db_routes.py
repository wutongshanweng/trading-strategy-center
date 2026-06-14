"""
Database CRUD API Routes

Provides generic CRUD endpoints for core database tables.
Allows direct querying and management of database records.

Prefix: /api/v1/db
Tags: database
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/db", tags=["database"])


# ============================================================
# Pydantic schemas
# ============================================================

class ContractCreate(BaseModel):
    symbol: str
    name: str
    exchange: str
    category: str
    multiplier: int = 1
    min_tick: float = 0.01
    margin_rate: float = 0.1
    commission: float = 0.0
    is_active: bool = True
    delivery_months: Optional[str] = None


class KlineQuery(BaseModel):
    symbol: str
    period: str = "1d"
    start: Optional[str] = None
    end: Optional[str] = None
    limit: int = 100


class SignalQuery(BaseModel):
    symbol: Optional[str] = None
    strategy: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    limit: int = 50


class TradeRecordQuery(BaseModel):
    symbol: Optional[str] = None
    strategy: Optional[str] = None
    status: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    limit: int = 50


# ============================================================
# Contracts CRUD
# ============================================================

@router.get("/contracts", summary="列出所有品种合约")
async def list_contracts(
    exchange: Optional[str] = Query(None, description="交易所过滤"),
    category: Optional[str] = Query(None, description="分类过滤"),
    active_only: bool = Query(True, description="仅活跃品种"),
    limit: int = Query(100, le=500),
):
    """查询品种合约列表，支持按交易所/分类过滤。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    Session = get_session_maker()
    async with Session() as session:
        conditions = []
        params: Dict[str, Any] = {"limit": limit}
        if exchange:
            conditions.append("exchange = :exchange")
            params["exchange"] = exchange
        if category:
            conditions.append("category = :category")
            params["category"] = category
        if active_only:
            conditions.append("is_active = true")

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM contracts WHERE {where} ORDER BY symbol LIMIT :limit"

        result = await session.execute(text(sql), params)
        rows = result.fetchall()
        columns = result.keys()

    return [dict(zip(columns, row)) for row in rows]


@router.get("/contracts/{symbol}", summary="获取品种合约详情")
async def get_contract(symbol: str):
    """查询单个品种合约的详情。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    Session = get_session_maker()
    async with Session() as session:
        result = await session.execute(
            text("SELECT * FROM contracts WHERE symbol = :symbol"),
            {"symbol": symbol},
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Contract '{symbol}' not found")
        columns = result.keys()
    return dict(zip(columns, row))


@router.post("/contracts", summary="创建品种合约")
async def create_contract(contract: ContractCreate):
    """创建新的品种合约。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    Session = get_session_maker()
    async with Session() as session:
        async with session.begin():
            # 检查是否已存在
            existing = await session.execute(
                text("SELECT id FROM contracts WHERE symbol = :symbol"),
                {"symbol": contract.symbol},
            )
            if existing.fetchone():
                raise HTTPException(status_code=409, detail=f"Contract '{contract.symbol}' already exists")

            await session.execute(
                text("""
                    INSERT INTO contracts
                        (symbol, name, exchange, category, multiplier, min_tick,
                         margin_rate, commission, is_active, delivery_months)
                    VALUES
                        (:symbol, :name, :exchange, :category, :multiplier, :min_tick,
                         :margin_rate, :commission, :is_active, :delivery_months)
                """),
                contract.model_dump(),
            )
    return {"status": "created", "symbol": contract.symbol}


# ============================================================
# Klines query
# ============================================================

@router.post("/klines/query", summary="查询 K 线数据")
async def query_klines(query: KlineQuery):
    """按品种/周期/时间范围查询 K 线。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    Session = get_session_maker()
    async with Session() as session:
        conditions = ["symbol = :symbol", "period = :period"]
        params: Dict[str, Any] = {
            "symbol": query.symbol,
            "period": query.period,
            "limit": query.limit,
        }
        if query.start:
            conditions.append("timestamp >= :start")
            params["start"] = query.start
        if query.end:
            conditions.append("timestamp <= :end")
            params["end"] = query.end

        where = " AND ".join(conditions)
        sql = f"""
            SELECT timestamp, open, high, low, close, volume, open_interest
            FROM klines
            WHERE {where}
            ORDER BY timestamp DESC
            LIMIT :limit
        """
        result = await session.execute(text(sql), params)
        rows = result.fetchall()
        columns = result.keys()

    return [dict(zip(columns, row)) for row in rows]


# ============================================================
# Signals query
# ============================================================

@router.post("/signals/query", summary="查询交易信号")
async def query_signals(query: SignalQuery):
    """按条件查询交易信号。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker
    import json

    Session = get_session_maker()
    async with Session() as session:
        conditions: List[str] = []
        params: Dict[str, Any] = {"limit": query.limit}

        if query.symbol:
            conditions.append("contract = :symbol")
            params["symbol"] = query.symbol
        if query.strategy:
            conditions.append("strategy_name = :strategy")
            params["strategy"] = query.strategy
        if query.start:
            conditions.append("timestamp >= :start")
            params["start"] = query.start
        if query.end:
            conditions.append("timestamp <= :end")
            params["end"] = query.end

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM signals WHERE {where} ORDER BY created_at DESC LIMIT :limit"

        result = await session.execute(text(sql), params)
        rows = result.fetchall()
        columns = result.keys()

    records = []
    for row in rows:
        record = dict(zip(columns, row))
        # 确保 JSON 字段可序列化
        if isinstance(record.get("extra"), str):
            try:
                record["extra"] = json.loads(record["extra"])
            except (json.JSONDecodeError, TypeError):
                pass
        records.append(record)
    return records


# ============================================================
# Trade Records
# ============================================================

@router.post("/trades/query", summary="查询成交记录")
async def query_trades(query: TradeRecordQuery):
    """按条件查询成交记录。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    Session = get_session_maker()
    async with Session() as session:
        conditions: List[str] = []
        params: Dict[str, Any] = {"limit": query.limit}

        if query.symbol:
            conditions.append("symbol = :symbol")
            params["symbol"] = query.symbol
        if query.strategy:
            conditions.append("strategy = :strategy")
            params["strategy"] = query.strategy
        if query.status:
            conditions.append("status = :status")
            params["status"] = query.status
        if query.start:
            conditions.append("entry_time >= :start")
            params["start"] = query.start
        if query.end:
            conditions.append("entry_time <= :end")
            params["end"] = query.end

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM trade_records WHERE {where} ORDER BY entry_time DESC LIMIT :limit"

        result = await session.execute(text(sql), params)
        rows = result.fetchall()
        columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


# ============================================================
# Positions
# ============================================================

@router.get("/positions", summary="查询当前持仓")
async def list_positions(
    symbol: Optional[str] = Query(None),
    status: str = Query("OPEN"),
):
    """查询当前持仓记录。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    Session = get_session_maker()
    async with Session() as session:
        if symbol:
            result = await session.execute(
                text("SELECT * FROM positions WHERE symbol = :symbol AND status = :status ORDER BY opened_at DESC"),
                {"symbol": symbol, "status": status},
            )
        else:
            result = await session.execute(
                text("SELECT * FROM positions WHERE status = :status ORDER BY opened_at DESC"),
                {"status": status},
            )
        rows = result.fetchall()
        columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


# ============================================================
# Backtest Results
# ============================================================

@router.get("/backtests", summary="查询回测结果")
async def list_backtests(
    strategy: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
):
    """查询历史回测结果。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    Session = get_session_maker()
    async with Session() as session:
        conditions: List[str] = []
        params: Dict[str, Any] = {"limit": limit}
        if strategy:
            conditions.append("strategy = :strategy")
            params["strategy"] = strategy
        if symbol:
            conditions.append("symbol = :symbol")
            params["symbol"] = symbol

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM backtest_results WHERE {where} ORDER BY created_at DESC LIMIT :limit"

        result = await session.execute(text(sql), params)
        rows = result.fetchall()
        columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


# ============================================================
# Performance Snapshots
# ============================================================

@router.get("/performance", summary="查询每日表现快照")
async def list_performance(
    strategy: Optional[str] = Query(None),
    days: int = Query(30, le=365),
):
    """查询最近的每日表现快照。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    Session = get_session_maker()
    async with Session() as session:
        conditions: List[str] = []
        params: Dict[str, Any] = {"cutoff": cutoff_date}
        if strategy:
            conditions.append("strategy_name = :strategy")
            params["strategy"] = strategy

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"""
            SELECT * FROM performance_snapshots
            WHERE {where}
              AND snapshot_date >= :cutoff
            ORDER BY snapshot_date DESC
        """
        result = await session.execute(text(sql), params)
        rows = result.fetchall()
        columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


# ============================================================
# Model Versions
# ============================================================

@router.get("/models", summary="查询 ML 模型版本")
async def list_models(
    model_name: Optional[str] = Query(None),
    active_only: bool = Query(False),
):
    """查询 ML 模型版本列表。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    Session = get_session_maker()
    async with Session() as session:
        if active_only:
            result = await session.execute(
                text("SELECT * FROM model_versions WHERE is_active = true ORDER BY model_name, created_at DESC")
            )
        elif model_name:
            result = await session.execute(
                text("SELECT * FROM model_versions WHERE model_name = :name ORDER BY version DESC"),
                {"name": model_name},
            )
        else:
            result = await session.execute(
                text("SELECT * FROM model_versions ORDER BY model_name, created_at DESC")
            )
        rows = result.fetchall()
        columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


# ============================================================
# Monitor: Rules + Alerts
# ============================================================

@router.get("/monitor/rules", summary="查询告警规则")
async def list_monitor_rules(
    rule_type: Optional[str] = Query(None),
    enabled_only: bool = Query(False),
):
    """查询监控告警规则。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    Session = get_session_maker()
    async with Session() as session:
        conditions: List[str] = []
        params: Dict[str, Any] = {}
        if rule_type:
            conditions.append("rule_type = :rule_type")
            params["rule_type"] = rule_type
        if enabled_only:
            conditions.append("enabled = true")

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM monitor_rules WHERE {where} ORDER BY name"

        result = await session.execute(text(sql), params)
        rows = result.fetchall()
        columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/monitor/alerts", summary="查询告警记录")
async def list_monitor_alerts(
    level: Optional[str] = Query(None, description="告警级别: INFO/WARNING/CRITICAL/EMERGENCY"),
    unacknowledged_only: bool = Query(False),
    limit: int = Query(50, le=200),
):
    """查询告警记录。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker
    import json

    Session = get_session_maker()
    async with Session() as session:
        conditions: List[str] = []
        params: Dict[str, Any] = {"limit": limit}
        if level:
            conditions.append("level = :level")
            params["level"] = level
        if unacknowledged_only:
            conditions.append("acknowledged = false")

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM monitor_alerts WHERE {where} ORDER BY created_at DESC LIMIT :limit"

        result = await session.execute(text(sql), params)
        rows = result.fetchall()
        columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


# ============================================================
# Tournament
# ============================================================

@router.get("/tournament/strategies", summary="查询参赛策略")
async def list_tournament_strategies(
    active_only: bool = Query(True),
    round: Optional[int] = Query(None),
):
    """查询锦标赛参赛策略。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    Session = get_session_maker()
    async with Session() as session:
        conditions: List[str] = []
        params: Dict[str, Any] = {}
        if active_only:
            conditions.append("is_active = true")
        if round is not None:
            conditions.append("tournament_round = :round")
            params["round"] = round

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM tournament_strategies WHERE {where} ORDER BY score DESC"

        result = await session.execute(text(sql), params)
        rows = result.fetchall()
        columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/tournament/records", summary="查询锦标赛轮次记录")
async def list_tournament_records(limit: int = Query(20, le=100)):
    """查询锦标赛轮次历史。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    Session = get_session_maker()
    async with Session() as session:
        result = await session.execute(
            text("SELECT * FROM tournament_records ORDER BY round DESC LIMIT :limit"),
            {"limit": limit},
        )
        rows = result.fetchall()
        columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


# ============================================================
# DB statistics
# ============================================================

@router.get("/stats", summary="数据库统计")
async def db_stats():
    """返回各表的数据量和数据库整体状态。"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    Session = get_session_maker()
    async with Session() as session:
        tables = [
            "contracts", "klines", "signals", "parameter_versions",
            "positions", "trade_records", "backtest_results",
            "performance_snapshots", "model_versions",
            "tournament_strategies", "tournament_records",
            "monitor_rules", "monitor_alerts",
        ]
        stats = {}
        for table in tables:
            try:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                stats[table] = result.scalar()
            except Exception:
                stats[table] = -1

    return {
        "table_count": len(tables),
        "total_rows": sum(v for v in stats.values() if v > 0),
        "details": stats,
    }
