"""API routes for LLM-powered market analysis and strategy generation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.llm.market_analyzer import MarketAnalyzer
from core.llm.strategy_generator import StrategyGenerator

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])

_analyzer = MarketAnalyzer()
_generator = StrategyGenerator()


# ---- Request Models ----


class MarketAnalysisRequest(BaseModel):
    returns: List[float] = Field(default_factory=list, description="近期收益率序列")
    volatility: float = 0.0
    trend_strength: float = 0.0
    regime_labels: Optional[List[str]] = None


class TradingPlanRequest(BaseModel):
    market_summary: Dict[str, Any] = Field(default_factory=dict)
    current_positions: List[Dict[str, Any]] = Field(default_factory=list)
    risk_budget: float = 0.02


class StrategyGenerateRequest(BaseModel):
    description: str = Field(..., description="策略的自然语言描述")
    constraints: Optional[Dict[str, Any]] = None


class StrategyOptimizeRequest(BaseModel):
    strategy_code: str
    backtest_metrics: Dict[str, float] = Field(default_factory=dict)
    optimization_target: str = "sharpe_ratio"


class ExplainSignalRequest(BaseModel):
    signal: Dict[str, Any] = Field(default_factory=dict)
    market_context: Dict[str, Any] = Field(default_factory=dict)


class CrossAssetRequest(BaseModel):
    correlations: Dict[str, float] = Field(default_factory=dict)
    sector_performance: Dict[str, float] = Field(default_factory=dict)


class BacktestInterpretRequest(BaseModel):
    metrics: Dict[str, float] = Field(default_factory=dict)
    strategy_name: str = ""


# ---- Market Analysis Routes ----


@router.post("/market/analyze", summary="分析当前市场状态")
async def analyze_market(req: MarketAnalysisRequest):
    """Use LLM to analyze market regime based on quantitative indicators."""
    result = _analyzer.analyze_regime(
        returns=req.returns or [0.0],
        volatility=req.volatility,
        trend_strength=req.trend_strength,
        regime_labels=req.regime_labels,
    )
    return result


@router.post("/market/trading-plan", summary="生成交易计划")
async def generate_trading_plan(req: TradingPlanRequest):
    """Generate a trading plan based on market analysis and current positions."""
    result = _analyzer.generate_trading_plan(
        market_summary=req.market_summary,
        current_positions=req.current_positions,
        risk_budget=req.risk_budget,
    )
    return result


@router.post("/market/cross-asset", summary="跨资产分析")
async def cross_asset_analysis(req: CrossAssetRequest):
    """Analyze cross-asset relationships and sector rotation."""
    result = _analyzer.cross_asset_analysis(
        correlations=req.correlations,
        sector_performance=req.sector_performance,
    )
    return result


@router.post("/backtest/interpret", summary="解读回测结果")
async def interpret_backtest(req: BacktestInterpretRequest):
    """Interpret backtest results with LLM narrative analysis."""
    result = _analyzer.interpret_backtest(
        metrics=req.metrics,
        strategy_name=req.strategy_name,
    )
    return {"analysis": result}


# ---- Strategy Generation Routes ----


@router.post("/strategy/generate", summary="生成交易策略")
async def generate_strategy(req: StrategyGenerateRequest):
    """Generate a complete trading strategy from natural language description."""
    result = _generator.generate_strategy(
        description=req.description,
        constraints=req.constraints,
    )
    return result


@router.post("/strategy/optimize", summary="优化策略参数")
async def optimize_strategy(req: StrategyOptimizeRequest):
    """Suggest parameter optimizations based on backtest results."""
    result = _generator.optimize_strategy(
        strategy_code=req.strategy_code,
        backtest_metrics=req.backtest_metrics,
        optimization_target=req.optimization_target,
    )
    return result


@router.post("/signal/explain", summary="解释交易信号")
async def explain_signal(req: ExplainSignalRequest):
    """Generate a human-readable explanation of a trading signal."""
    result = _generator.explain_signal(
        signal=req.signal,
        market_context=req.market_context,
    )
    return {"explanation": result}


@router.get("/providers", summary="列出可用 LLM 提供商")
async def list_providers():
    """List all configured LLM providers."""
    from core.llm.llm_client import LLMClient
    client = LLMClient()
    providers = client.list_providers()
    return {"providers": providers}


# ---- Phase4: 策略建议器 (Agent → LLM) ----

class StrategyAdviceRequest(BaseModel):
    question: str = Field(..., description="自然语言策略问题")
    context: Dict[str, Any] = Field(default_factory=dict, description="市态/品种等上下文")


class StrategyDraftRequest(BaseModel):
    description: str = Field(..., description="策略的自然语言描述")


@router.post("/strategy/advise", summary="LLM 策略建议 (基于策略目录)")
async def strategy_advise(req: StrategyAdviceRequest):
    """让 LLM 基于当前策略库 + 市场上下文给出建议 (无 LLM 时本地降级)。"""
    from core.llm.strategy_advisor import LLMStrategyAdvisor
    advice = LLMStrategyAdvisor().ask(req.question, req.context)
    return {"question": req.question, "advice": advice}


@router.post("/strategy/draft", summary="LLM 据描述生成策略代码草稿")
async def strategy_draft(req: StrategyDraftRequest):
    """据自然语言描述生成策略代码草稿 (无 LLM 时返回模板)。"""
    from core.llm.strategy_advisor import LLMStrategyAdvisor
    return LLMStrategyAdvisor().generate_strategy(req.description)
