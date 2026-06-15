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
