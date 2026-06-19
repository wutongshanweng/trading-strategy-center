"""
Factor Research API Routes
因子研究相关的API路由
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from research.factor_lab.factor_analyzer import FactorAnalyzer
from core.alpha.alpha101.factor_registry import FactorRegistry

router = APIRouter(prefix="/api/factor", tags=["factor"])


class ICAnalysisRequest(BaseModel):
    """IC分析请求"""
    factor_id: str
    symbol: str = "000001.SZ"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    method: str = "pearson"


class LayeredBacktestRequest(BaseModel):
    """分层回测请求"""
    factor_id: str
    symbols: List[str] = ["000001.SZ", "000002.SZ", "600000.SH"]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    n_quantiles: int = 5


class FactorCombineRequest(BaseModel):
    """因子组合请求"""
    factor_ids: List[str]
    symbols: List[str] = ["000001.SZ", "000002.SZ"]
    method: str = "ic_weight"  # ic_weight, equal_weight, optimize


# Mock data generator for demonstration
def generate_mock_data(symbol: str, days: int = 252):
    """生成模拟数据"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

    # 生成价格数据
    np.random.seed(hash(symbol) % 1000)
    returns = np.random.randn(days) * 0.02
    prices = 100 * (1 + returns).cumprod()

    price_df = pd.DataFrame({
        'close': prices,
        'open': prices * (1 + np.random.randn(days) * 0.005),
        'high': prices * (1 + np.abs(np.random.randn(days)) * 0.01),
        'low': prices * (1 - np.abs(np.random.randn(days)) * 0.01),
        'volume': np.random.randint(1000000, 10000000, days)
    }, index=dates)

    return price_df


def calculate_mock_factor(factor_id: str, price_df: pd.DataFrame) -> pd.Series:
    """计算模拟因子值"""
    # 简化的因子计算逻辑
    if 'trend' in factor_id.lower() or int(factor_id.replace('alpha', '')) % 4 == 0:
        # 趋势类因子 - 使用移动平均
        factor = price_df['close'].rolling(20).mean() - price_df['close'].rolling(5).mean()
    elif 'volume' in factor_id.lower() or int(factor_id.replace('alpha', '')) % 4 == 1:
        # 成交量类因子
        factor = price_df['volume'].rolling(20).mean() / price_df['volume'].rolling(5).mean()
    elif 'volatility' in factor_id.lower() or int(factor_id.replace('alpha', '')) % 4 == 2:
        # 波动率类因子
        factor = price_df['close'].pct_change().rolling(20).std()
    else:
        # 价格类因子
        factor = price_df['close'].pct_change(20)

    return factor.fillna(0)


@router.post("/ic-analysis")
async def ic_analysis(request: ICAnalysisRequest) -> Dict[str, Any]:
    """
    IC分析 - 计算IC时间序列、分布、衰减
    """
    try:
        # 生成模拟数据
        days = 252 if not request.start_date else 500
        price_df = generate_mock_data(request.symbol, days)

        # 计算因子值
        factor_values = calculate_mock_factor(request.factor_id, price_df)

        # 计算未来收益
        returns = price_df['close'].pct_change(1).shift(-1)

        analyzer = FactorAnalyzer()

        # 1. IC时间序列（滚动窗口计算）
        window_size = 20
        ic_series = []
        dates = []

        for i in range(window_size, len(factor_values)):
            window_factor = factor_values.iloc[i-window_size:i]
            window_returns = returns.iloc[i-window_size:i]

            ic = analyzer.calculate_ic(window_factor, window_returns, method=request.method)
            if not np.isnan(ic):
                ic_series.append(float(ic))
                dates.append(factor_values.index[i].strftime('%Y-%m-%d'))

        # 2. IC分布统计
        ic_array = np.array(ic_series)
        ic_mean = float(np.mean(ic_array))
        ic_std = float(np.std(ic_array))
        ic_ir = ic_mean / ic_std if ic_std > 0 else 0

        # IC分布直方图数据
        hist, bin_edges = np.histogram(ic_array, bins=30)
        distribution = [
            {"bin": f"{bin_edges[i]:.4f}", "count": int(hist[i])}
            for i in range(len(hist))
        ]

        # 3. IC衰减分析
        decay_periods = 20
        ic_decay = analyzer.ic_decay(factor_values, price_df['close'], max_periods=decay_periods)
        decay_data = [
            {"period": int(i+1), "ic": float(ic_decay.iloc[i]) if not np.isnan(ic_decay.iloc[i]) else 0}
            for i in range(len(ic_decay))
        ]

        return {
            "success": True,
            "factor_id": request.factor_id,
            "symbol": request.symbol,
            "ic_time_series": {
                "dates": dates,
                "values": ic_series,
                "statistics": {
                    "mean": ic_mean,
                    "std": ic_std,
                    "ir": ic_ir,
                    "positive_ratio": float(np.sum(ic_array > 0) / len(ic_array))
                }
            },
            "ic_distribution": distribution,
            "ic_decay": decay_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IC分析失败: {str(e)}")


@router.post("/layered-backtest")
async def layered_backtest(request: LayeredBacktestRequest) -> Dict[str, Any]:
    """
    分层回测 - 5层收益对比、多空组合、换手率
    """
    try:
        analyzer = FactorAnalyzer()
        all_results = []

        for symbol in request.symbols:
            # 生成数据
            price_df = generate_mock_data(symbol, 252)
            factor_values = calculate_mock_factor(request.factor_id, price_df)
            returns = price_df['close'].pct_change(1).shift(-1)

            # 分层回测
            layered_result = analyzer.layered_backtest(
                factor_values, returns, n_quantiles=request.n_quantiles
            )

            all_results.append({
                "symbol": symbol,
                "layers": layered_result
            })

        # 汇总所有标的的分层结果
        quantile_labels = [f"Q{i+1}" for i in range(request.n_quantiles)]
        layer_summary = []

        for q in quantile_labels:
            mean_returns = [r["layers"][q]["mean_return"] for r in all_results if q in r["layers"]]
            layer_summary.append({
                "quantile": q,
                "mean_return": float(np.mean(mean_returns)),
                "std_return": float(np.std(mean_returns)),
                "sharpe": float(np.mean([r["layers"][q]["sharpe"] for r in all_results if q in r["layers"]]))
            })

        # 多空组合分析
        long_short_returns = [r["layers"]["long_short"]["mean_return"] for r in all_results if "long_short" in r["layers"]]
        long_short = {
            "mean_return": float(np.mean(long_short_returns)),
            "std_return": float(np.std(long_short_returns)),
            "sharpe": float(np.mean([r["layers"]["long_short"]["sharpe"] for r in all_results if "long_short" in r["layers"]])),
            "win_rate": float(np.sum(np.array(long_short_returns) > 0) / len(long_short_returns))
        }

        # 换手率统计（模拟）
        turnover_stats = {
            "daily_turnover": 0.15 + np.random.rand() * 0.1,
            "weekly_turnover": 0.35 + np.random.rand() * 0.15,
            "monthly_turnover": 0.65 + np.random.rand() * 0.2
        }

        return {
            "success": True,
            "factor_id": request.factor_id,
            "n_quantiles": request.n_quantiles,
            "layer_summary": layer_summary,
            "long_short": long_short,
            "turnover": turnover_stats,
            "detailed_results": all_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分层回测失败: {str(e)}")


@router.post("/factor-combine")
async def factor_combine(request: FactorCombineRequest) -> Dict[str, Any]:
    """
    因子组合 - 相关性矩阵、IC加权、优化权重
    """
    try:
        # 生成数据
        price_df = generate_mock_data(request.symbols[0], 252)

        # 计算多个因子值
        factor_data = {}
        for factor_id in request.factor_ids:
            factor_data[factor_id] = calculate_mock_factor(factor_id, price_df)

        factor_df = pd.DataFrame(factor_data)

        # 1. 相关性矩阵
        corr_matrix = factor_df.corr()
        correlation_matrix = []
        for i, factor1 in enumerate(request.factor_ids):
            row = []
            for j, factor2 in enumerate(request.factor_ids):
                row.append({
                    "factor1": factor1,
                    "factor2": factor2,
                    "correlation": float(corr_matrix.iloc[i, j])
                })
            correlation_matrix.append(row)

        # 2. IC加权组合
        returns = price_df['close'].pct_change(1).shift(-1)
        analyzer = FactorAnalyzer()

        ic_values = {}
        for factor_id in request.factor_ids:
            ic = analyzer.calculate_ic(factor_data[factor_id], returns)
            ic_values[factor_id] = abs(ic) if not np.isnan(ic) else 0

        total_ic = sum(ic_values.values())
        ic_weights = {
            factor_id: ic / total_ic if total_ic > 0 else 1.0 / len(request.factor_ids)
            for factor_id, ic in ic_values.items()
        }

        # 3. 优化权重（使用简化的最大化IC-IR方法）
        if request.method == "optimize":
            # 模拟优化过程
            optimized_weights = {}
            base_weight = 1.0 / len(request.factor_ids)
            for i, factor_id in enumerate(request.factor_ids):
                # 添加一些随机扰动
                weight = base_weight + (np.random.rand() - 0.5) * 0.2
                optimized_weights[factor_id] = max(0.05, min(0.5, weight))

            # 归一化
            total = sum(optimized_weights.values())
            optimized_weights = {k: v/total for k, v in optimized_weights.items()}
        else:
            optimized_weights = ic_weights

        # 4. 组合因子性能
        combined_factor = sum(
            factor_data[fid] * optimized_weights[fid]
            for fid in request.factor_ids
        )
        combined_ic = analyzer.calculate_ic(combined_factor, returns)

        weights_list = [
            {
                "factor_id": fid,
                "ic_weight": float(ic_weights[fid]),
                "optimized_weight": float(optimized_weights[fid]),
                "ic_value": float(ic_values[fid])
            }
            for fid in request.factor_ids
        ]

        return {
            "success": True,
            "method": request.method,
            "correlation_matrix": correlation_matrix,
            "weights": weights_list,
            "combined_performance": {
                "ic": float(combined_ic) if not np.isnan(combined_ic) else 0,
                "ir": float(combined_ic / 0.05) if not np.isnan(combined_ic) else 0,  # 简化IR
                "diversification_ratio": float(1 - corr_matrix.mean().mean())
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"因子组合失败: {str(e)}")


@router.get("/factors/list")
async def list_factors(
    category: Optional[str] = Query(None, description="因子分类: 价格/成交量/波动率/趋势")
) -> Dict[str, Any]:
    """
    获取因子列表
    """
    try:
        # 生成101个Alpha因子
        factors = []
        categories = ["价格", "成交量", "波动率", "趋势"]

        for i in range(1, 102):
            factor_id = f"alpha{str(i).zfill(3)}"
            factor_category = categories[i % 4]

            if category and factor_category != category:
                continue

            factors.append({
                "id": factor_id,
                "name": f"Alpha{i}",
                "category": factor_category,
                "description": f"WorldQuant Alpha Factor {i}",
                "ic": round(np.random.randn() * 0.05 + 0.02, 4),
                "ir": round(abs(np.random.randn()) * 0.5 + 0.8, 2)
            })

        return {
            "success": True,
            "count": len(factors),
            "factors": factors
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取因子列表失败: {str(e)}")


# ════════════════════════════════════════════════════════════════
# Phase 2: 遗传挖掘 / 健康监控 / 行业中性化 / 研究报告 (接真实仓库数据)
# ════════════════════════════════════════════════════════════════

def _warehouse_ohlcv(symbol: str, limit: int = 500) -> Optional[pd.DataFrame]:
    """从 DuckDB 仓库取单标的 D1 OHLCV; 无数据返回 None。"""
    try:
        from data_center.storage.duckdb_store import get_store
        store = get_store()
        sid = store.query("SELECT symbol_id FROM symbols WHERE code = ?", [symbol.upper()])
        if sid.empty:
            return None
        symbol_id = int(sid.iloc[0]["symbol_id"])
        df = store.query(
            "SELECT datetime, open, high, low, close, volume FROM kline "
            "WHERE symbol_id=? AND timeframe='D1' ORDER BY datetime DESC LIMIT ?",
            [symbol_id, limit],
        )
        if df.empty:
            return None
        df = df.sort_values("datetime").set_index("datetime")
        for c in ("open", "high", "low", "close", "volume"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        return df.dropna(subset=["close"])
    except Exception:
        return None


def _get_ohlcv(symbol: str, days: int = 500) -> tuple[pd.DataFrame, str]:
    """优先真实仓库数据, 无则回退 mock。返回 (df, source)。"""
    real = _warehouse_ohlcv(symbol, days)
    if real is not None and len(real) >= 30:
        return real, "warehouse"
    return generate_mock_data(symbol, days), "mock"


class MineRequest(BaseModel):
    symbol: str = "600019.SH"
    n_factors: int = 10
    population_size: int = 40
    generations: int = 10
    days: int = 500


@router.post("/mine")
async def mine_factors(req: MineRequest) -> Dict[str, Any]:
    """遗传编程因子挖掘 (复用 GeneticProgramming + FitnessFunction)。"""
    try:
        from core.alpha.mining import GeneticProgramming, FitnessFunction
        df, source = _get_ohlcv(req.symbol, req.days)
        gp = GeneticProgramming(
            population_size=req.population_size, generations=req.generations, max_depth=3)
        returns = df["close"].pct_change()
        best = gp.evolve(df, FitnessFunction(), returns, top_k=req.n_factors)
        fit = FitnessFunction()
        out = []
        for i, expr in enumerate(best, 1):
            score = fit.evaluate(expr, df, returns)
            fv = expr.compute(df).dropna()
            rv = returns.loc[fv.index].dropna()
            common = fv.index.intersection(rv.index)
            ic = float(fv.loc[common].corr(rv.loc[common])) if len(common) > 5 else 0.0
            out.append({
                "name": f"GF_{i:03d}", "expression": expr.name,
                "fitness": round(score, 4),
                "ic": round(ic if not np.isnan(ic) else 0.0, 4),
            })
        return {"success": True, "symbol": req.symbol, "data_source": source,
                "count": len(out), "factors": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"因子挖掘失败: {str(e)}")


@router.post("/health-check")
async def factor_health(req: ICAnalysisRequest) -> Dict[str, Any]:
    """因子健康检测 (三态: HEALTHY/WARNING/DECAYED)。"""
    try:
        from core.alpha.management import FactorDecayDetector
        df, source = _get_ohlcv(req.symbol)
        factor = calculate_mock_factor(req.factor_id, df)
        fwd = df["close"].pct_change().shift(-1)
        ic_series = factor.rolling(20, min_periods=10).corr(fwd)
        rep = FactorDecayDetector().check(req.factor_id, ic_series, factor, fwd)
        return {"success": True, "data_source": source,
                "factor_id": req.factor_id, "health": rep.health.value,
                "current_ic": rep.current_ic, "ic_trend": rep.ic_trend,
                "ic_mean_short": rep.ic_mean_short, "ic_mean_long": rep.ic_mean_long,
                "icir": rep.icir, "monotonicity": rep.monotonicity,
                "alert_level": rep.alert_level, "reasons": rep.reasons}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检测失败: {str(e)}")


class ReportRequest(BaseModel):
    symbols: List[str] = ["600019.SH", "601899.SH", "600585.SH"]
    factor_ids: List[str] = ["alpha001", "alpha002", "alpha003", "alpha004"]
    top_n: int = 20


@router.post("/report")
async def factor_report(req: ReportRequest) -> Dict[str, Any]:
    """全因子研究报告: 排名 + 冗余 + 推荐组合 (用首个标的的多因子横截面近似时序)。"""
    try:
        from core.alpha.management import FactorReportGenerator
        symbol = req.symbols[0] if req.symbols else "600019.SH"
        df, source = _get_ohlcv(symbol)
        fwd = df["close"].pct_change().shift(-1)
        factors = {fid: calculate_mock_factor(fid, df) for fid in req.factor_ids}
        fdf = pd.DataFrame(factors).reindex(df.index)
        gen = FactorReportGenerator()
        rep = gen.generate(fdf, fwd, top_n=req.top_n)
        return {"success": True, "data_source": source, "report": gen.to_dict(rep)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")


class NeutralizeRequest(BaseModel):
    values: Dict[str, float]          # {标的: 因子值}
    industries: Dict[str, str]        # {标的: 行业}
    method: str = "mean"              # mean / zscore / regression


@router.post("/neutralize")
async def neutralize_factor(req: NeutralizeRequest) -> Dict[str, Any]:
    """行业中性化 — 输入因子值 + 行业标签, 返回中性化后的值及暴露对比。"""
    try:
        from core.alpha.management import IndustryNeutralizer
        codes = list(req.values.keys())
        fv = pd.Series([req.values[c] for c in codes], index=codes)
        ind = pd.Series([req.industries.get(c, "未知") for c in codes], index=codes)
        n = IndustryNeutralizer()
        fn = {"mean": n.neutralize_by_mean, "zscore": n.neutralize_by_zscore,
              "regression": n.neutralize_by_regression}.get(req.method, n.neutralize_by_mean)
        neu = fn(fv, ind)
        return {"success": True, "method": req.method,
                "exposure_before": round(n.max_industry_exposure(fv, ind), 4),
                "exposure_after": round(n.max_industry_exposure(neu, ind), 4),
                "neutralized": {c: round(float(neu[c]), 6) for c in codes if pd.notna(neu[c])}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"行业中性化失败: {str(e)}")
