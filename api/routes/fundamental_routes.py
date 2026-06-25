"""基本面 Agent API — 四维基本面评分接口。

GET /api/v1/fundamental/{symbol}     → 单品种四维评分
POST /api/v1/fundamental/batch      → 批量品种评分
GET /api/v1/fundamental/product-map → 品种基本面映射配置
GET /api/v1/fundamental/{symbol}/detail → 详细数据
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from loguru import logger

from analysis.fundamental.model import FundamentalAgent, analyze_fundamental
from analysis.fundamental.product_map import PRODUCT_FUNDAMENTALS

router = APIRouter(prefix="/api/v1/fundamental", tags=["基本面分析"])


# ============ 请求/响应模型 ============
class BatchRequest(BaseModel):
    symbols: List[str]


class FundamentalResponse(BaseModel):
    symbol: str
    product_name: str
    scores: Dict[str, float]
    combined: float
    direction: str
    details: Dict[str, str]
    explanation: str
    data_quality: str


class ProductMapResponse(BaseModel):
    products: Dict


# ============ API 端点 ============
@router.get("/{symbol}", response_model=FundamentalResponse)
async def get_fundamental(symbol: str):
    """获取单个品种的基本面四维评分。

    Args:
        symbol: 合约代码，如 RB2510, FG409

    Returns:
        基本面评分结果 (库存/成本/季节/需求 四维 + 综合)
    """
    try:
        result = analyze_fundamental(symbol)
        if "error" in result.get("detail", {}):
            raise HTTPException(status_code=500, detail=result["detail"]["error"])

        detail = result["detail"]
        return FundamentalResponse(
            symbol=symbol,
            product_name=detail.get("product_name", symbol),
            scores=detail.get("scores", {}),
            combined=result["score"],
            direction=result["direction"],
            details=detail.get("details", {}),
            explanation=detail.get("explanation", ""),
            data_quality=detail.get("data_quality", "medium"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[fundamental] API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=List[FundamentalResponse])
async def batch_fundamental(request: BatchRequest):
    """批量获取多个品种的基本面评分。

    Args:
        request.body.symbols: 合约代码列表

    Returns:
        各品种基本面评分列表
    """
    try:
        agent = FundamentalAgent()
        results = agent.analyze_batch(request.symbols)

        responses = []
        for symbol, score in results.items():
            responses.append(FundamentalResponse(
                symbol=symbol,
                product_name=score.product_name,
                scores={
                    "inventory": score.inventory_score,
                    "cost": score.cost_score,
                    "seasonal": score.seasonal_score,
                    "demand": score.demand_score,
                },
                combined=score.combined,
                direction="偏多" if score.combined > 0.1 else "偏空" if score.combined < -0.1 else "中性",
                details={
                    "inventory": score.inventory_detail,
                    "cost": score.cost_detail,
                    "seasonal": score.seasonal_detail,
                    "demand": score.demand_detail,
                },
                explanation=score.detail,
                data_quality=score.data_quality,
            ))
        return responses
    except Exception as e:
        logger.error(f"[fundamental] Batch API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product-map", response_model=ProductMapResponse)
async def get_product_map():
    """获取所有品种的基本面映射配置。

    Returns:
        品种 → (库存源/成本链/需求指标/季节性) 映射
    """
    return ProductMapResponse(products=PRODUCT_FUNDAMENTALS)


@router.get("/{symbol}/detail")
async def get_fundamental_detail(symbol: str):
    """获取品种基本面的详细数据。

    Args:
        symbol: 合约代码

    Returns:
        详细数据 (库存值/成本链价格/季节性统计/需求指标值)
    """
    try:
        agent = FundamentalAgent()
        score = agent.analyze(symbol)

        result = {
            "symbol": symbol,
            "product_name": score.product_name,
            "inventory": None,
            "cost": None,
            "seasonal": None,
            "demand": None,
        }

        if score.inventory_result:
            result["inventory"] = {
                "score": score.inventory_result.score,
                "detail": score.inventory_result.detail,
                "data_quality": score.inventory_result.data_quality,
                "current_value": score.inventory_result.current_value,
                "percentile": score.inventory_result.percentile,
                "trend": score.inventory_result.trend,
            }

        if score.cost_result:
            result["cost"] = {
                "score": score.cost_result.score,
                "detail": score.cost_result.detail,
                "data_quality": score.cost_result.data_quality,
                "upstream_prices": score.cost_result.upstream_prices,
                "total_cost_change": score.cost_result.total_cost_change,
            }

        if score.seasonal_result:
            result["seasonal"] = {
                "score": score.seasonal_result.score,
                "detail": score.seasonal_result.detail,
                "data_quality": score.seasonal_result.data_quality,
                "current_month": score.seasonal_result.current_month,
                "bullish_months": score.seasonal_result.bullish_months,
                "bearish_months": score.seasonal_result.bearish_months,
                "win_rate": score.seasonal_result.win_rate,
                "avg_return": score.seasonal_result.avg_return,
            }

        if score.demand_result:
            result["demand"] = {
                "score": score.demand_result.score,
                "detail": score.demand_result.detail,
                "data_quality": score.demand_result.data_quality,
                "indicators": score.demand_result.indicators,
                "overall_trend": score.demand_result.overall_trend,
            }

        return result
    except Exception as e:
        logger.error(f"[fundamental] Detail API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
