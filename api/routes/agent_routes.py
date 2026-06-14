"""
Agent API - 对外API接口，供外部Agent使用
External Agent API for data, strategies, and trading
"""
from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])

# 密钥配置（生产环境应从环境变量读取）
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 模拟的API Key数据库
API_KEYS = {
    "agent_001": {
        "name": "Agent Alpha",
        "permissions": ["read_data", "read_strategies", "simulate_trade"],
        "created_at": "2024-01-01",
    },
    "agent_002": {
        "name": "Agent Beta",
        "permissions": ["read_data", "read_strategies"],
        "created_at": "2024-02-01",
    },
}


# ============ 认证相关 ============
class AuthRequest(BaseModel):
    api_key: str


class TokenResponse(BaseModel):
    token: str
    expires_in: int


def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """验证Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_agent(authorization: str = Header(...)) -> dict:
    """获取当前Agent信息（依赖注入）"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)

    api_key = payload.get("api_key")
    if api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {"api_key": api_key, **API_KEYS[api_key]}


@router.post("/auth", response_model=TokenResponse)
async def agent_authenticate(auth: AuthRequest):
    """
    Agent认证

    获取访问Token，用于后续API调用
    """
    if auth.api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")

    access_token = create_access_token(
        data={"api_key": auth.api_key},
        expires_delta=timedelta(hours=24)
    )

    return {
        "token": access_token,
        "expires_in": 86400  # 24小时
    }


# ============ 数据接口 ============
@router.get("/data/{symbol}")
async def get_market_data(
    symbol: str,
    start: str,
    end: str,
    interval: str = "1d",
    agent: dict = Depends(get_current_agent),
):
    """
    获取市场数据

    Args:
        symbol: 品种代码（如: RB, CU）
        start: 开始日期 (YYYY-MM-DD)
        end: 结束日期 (YYYY-MM-DD)
        interval: 数据周期 (1m/5m/15m/1h/1d)

    Returns:
        OHLCV数据
    """
    if "read_data" not in agent["permissions"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # TODO: 实际从数据管理器获取数据
    # from core.data.market_data_manager import MarketDataManager
    # manager = MarketDataManager()
    # data = await manager.get_data(symbol, start, end, interval)

    # 返回模拟数据
    return {
        "symbol": symbol,
        "interval": interval,
        "data": [
            {
                "timestamp": "2024-06-14T09:00:00",
                "open": 3850.0,
                "high": 3870.0,
                "low": 3840.0,
                "close": 3860.0,
                "volume": 12500,
            }
        ],
        "count": 1,
    }


@router.get("/data/realtime/{symbol}")
async def get_realtime_data(
    symbol: str,
    agent: dict = Depends(get_current_agent),
):
    """
    获取实时行情数据

    Args:
        symbol: 品种代码

    Returns:
        最新tick数据
    """
    if "read_data" not in agent["permissions"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {
        "symbol": symbol,
        "price": 3860.0,
        "volume": 1250,
        "timestamp": datetime.now().isoformat(),
        "bid": 3859.0,
        "ask": 3861.0,
    }


# ============ 策略接口 ============
@router.get("/strategies")
async def list_strategies(agent: dict = Depends(get_current_agent)):
    """
    获取所有策略列表

    Returns:
        策略列表及参数信息
    """
    if "read_strategies" not in agent["permissions"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # TODO: 从策略注册表获取
    # from signals.registry import list_strategies
    # strategies = list_strategies()

    return {
        "strategies": [
            {
                "id": "trend_ma_cross",
                "name": "双均线趋势",
                "category": "trend",
                "params": {"fast_period": 5, "slow_period": 20},
            },
            {
                "id": "rsi_reversal",
                "name": "RSI反转",
                "category": "mean_reversion",
                "params": {"period": 14, "overbought": 70, "oversold": 30},
            },
        ],
        "total": 2,
    }


@router.get("/strategies/{strategy_id}")
async def get_strategy_detail(
    strategy_id: str,
    agent: dict = Depends(get_current_agent),
):
    """获取策略详细信息"""
    if "read_strategies" not in agent["permissions"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {
        "id": strategy_id,
        "name": "双均线趋势",
        "description": "5日线上穿20日线买入，下穿卖出",
        "params": {"fast_period": 5, "slow_period": 20},
        "performance": {
            "sharpe": 2.15,
            "total_return": 0.35,
            "win_rate": 0.62,
            "max_drawdown": -0.10,
        },
    }


class ComputeSignalRequest(BaseModel):
    symbol: str
    strategy_names: List[str]
    timeframe: str = "1d"


@router.post("/signals/compute")
async def compute_signals(
    request: ComputeSignalRequest,
    agent: dict = Depends(get_current_agent),
):
    """
    计算策略信号

    Agent可以提交品种和策略列表，系统计算并返回信号
    """
    if "read_strategies" not in agent["permissions"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # TODO: 实际计算信号
    # from signals.engine import StrategyEngine
    # engine = StrategyEngine()
    # signals = engine.compute_all(data, request.symbol, request.strategy_names)

    return {
        "symbol": request.symbol,
        "timeframe": request.timeframe,
        "signals": [
            {
                "strategy": "trend_ma_cross",
                "direction": "BUY",
                "confidence": 0.85,
                "price": 3860.0,
                "reason": "5日线上穿20日线",
                "timestamp": datetime.now().isoformat(),
            }
        ],
    }


# ============ 因子接口 ============
@router.get("/factors")
async def list_factors(agent: dict = Depends(get_current_agent)):
    """获取所有Alpha因子列表"""
    if "read_data" not in agent["permissions"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {
        "factors": [
            {"id": "alpha001", "name": "Alpha001", "category": "price"},
            {"id": "alpha002", "name": "Alpha002", "category": "volume"},
        ],
        "total": 101,
    }


@router.get("/factors/{factor_id}")
async def get_factor_values(
    factor_id: str,
    symbol: str,
    start: str,
    end: str,
    agent: dict = Depends(get_current_agent),
):
    """
    获取因子值

    Args:
        factor_id: 因子ID (如: alpha001)
        symbol: 品种代码
        start: 开始日期
        end: 结束日期

    Returns:
        因子值时间序列
    """
    if "read_data" not in agent["permissions"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {
        "factor_id": factor_id,
        "symbol": symbol,
        "values": [
            {"timestamp": "2024-06-01", "value": 0.0234},
            {"timestamp": "2024-06-02", "value": 0.0189},
        ],
    }


# ============ 交易接口 ============
class OrderRequest(BaseModel):
    symbol: str
    direction: str  # BUY / SELL
    quantity: int
    price: Optional[float] = None
    order_type: str = "MARKET"


@router.post("/trading/simulate")
async def simulate_trade(
    order: OrderRequest,
    agent: dict = Depends(get_current_agent),
):
    """
    模拟交易

    Agent可以提交模拟订单，系统返回成交结果
    """
    if "simulate_trade" not in agent["permissions"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 生成订单ID
    order_id = f"SIM_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    return {
        "order_id": order_id,
        "status": "filled",
        "symbol": order.symbol,
        "direction": order.direction,
        "quantity": order.quantity,
        "filled_price": order.price or 3860.0,
        "filled_quantity": order.quantity,
        "filled_at": datetime.now().isoformat(),
        "commission": 0.0003 * order.quantity * (order.price or 3860.0),
    }


@router.get("/trading/positions")
async def get_positions(agent: dict = Depends(get_current_agent)):
    """获取当前持仓"""
    if "simulate_trade" not in agent["permissions"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {
        "positions": [
            {
                "symbol": "RB2501",
                "direction": "LONG",
                "quantity": 10,
                "avg_price": 3850.0,
                "current_price": 3860.0,
                "pnl": 100.0,
                "pnl_pct": 0.0026,
            }
        ],
        "total_value": 38600.0,
        "total_pnl": 100.0,
    }


# ============ 实用工具 ============
@router.get("/health")
async def health_check():
    """健康检查（无需认证）"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


@router.get("/usage")
async def get_usage_stats(agent: dict = Depends(get_current_agent)):
    """获取API使用统计"""
    return {
        "api_key": agent["api_key"],
        "requests_today": 127,
        "requests_month": 3856,
        "quota_limit": 10000,
        "quota_remaining": 6144,
    }
