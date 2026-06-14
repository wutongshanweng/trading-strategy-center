"""
策略自动进化引擎 - 基于机器学习的参数优化
Strategy Evolution Engine - ML-based Parameter Optimization
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from scipy.optimize import differential_evolution
from sklearn.model_selection import TimeSeriesSplit
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel
import joblib
from pathlib import Path


class StrategyEvolutionEngine:
    """
    策略自动进化引擎

    功能:
    1. 参数自动优化（贝叶斯优化/遗传算法）
    2. 策略自动组合
    3. 策略共振分析
    4. 高胜率策略自动部署
    """

    def __init__(self):
        self.optimizer_type = "bayesian"  # 或 "genetic"
        self.best_params_history = []
        self.deployed_strategies = []

    def evolve_parameters(
        self,
        strategy_class,
        data: pd.DataFrame,
        param_space: Dict[str, Tuple[float, float]],
        n_iterations: int = 50,
    ) -> Dict[str, float]:
        """
        自动优化策略参数

        Args:
            strategy_class: 策略类
            data: 历史数据
            param_space: 参数搜索空间 {"fast_period": (2, 20), "slow_period": (20, 100)}
            n_iterations: 优化迭代次数

        Returns:
            最优参数字典
        """
        print(f"开始优化策略参数...")
        print(f"参数空间: {param_space}")

        if self.optimizer_type == "bayesian":
            best_params = self._bayesian_optimize(
                strategy_class, data, param_space, n_iterations
            )
        else:
            best_params = self._genetic_optimize(
                strategy_class, data, param_space, n_iterations
            )

        self.best_params_history.append({
            "strategy": strategy_class.__name__,
            "params": best_params,
            "timestamp": pd.Timestamp.now(),
        })

        print(f"✓ 优化完成: {best_params}")
        return best_params

    def _bayesian_optimize(
        self,
        strategy_class,
        data: pd.DataFrame,
        param_space: Dict[str, Tuple],
        n_iterations: int,
    ) -> Dict:
        """贝叶斯优化"""
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import Matern

        # 参数名和范围
        param_names = list(param_space.keys())
        bounds = [param_space[name] for name in param_names]

        # 初始采样
        n_initial = 10
        X_sample = []
        y_sample = []

        for _ in range(n_initial):
            params = {
                name: np.random.uniform(low, high)
                for name, (low, high) in param_space.items()
            }
            score = self._evaluate_strategy(strategy_class, data, params)
            X_sample.append(list(params.values()))
            y_sample.append(score)

        X_sample = np.array(X_sample)
        y_sample = np.array(y_sample)

        # 高斯过程回归
        kernel = ConstantKernel(1.0) * Matern(length_scale=1.0, nu=2.5)
        gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)

        for iteration in range(n_iterations - n_initial):
            gp.fit(X_sample, y_sample)

            # 选择下一个采样点（最大化采集函数）
            next_params = self._acquisition_function(gp, bounds, X_sample)
            next_score = self._evaluate_strategy(
                strategy_class,
                data,
                dict(zip(param_names, next_params)),
            )

            X_sample = np.vstack([X_sample, next_params])
            y_sample = np.append(y_sample, next_score)

            if iteration % 10 == 0:
                print(f"  迭代 {iteration}/{n_iterations}, 最佳得分: {y_sample.max():.4f}")

        # 返回最优参数
        best_idx = y_sample.argmax()
        best_params = dict(zip(param_names, X_sample[best_idx]))
        return best_params

    def _genetic_optimize(
        self,
        strategy_class,
        data: pd.DataFrame,
        param_space: Dict,
        n_iterations: int,
    ) -> Dict:
        """遗传算法优化"""
        param_names = list(param_space.keys())
        bounds = [param_space[name] for name in param_names]

        def objective(params):
            param_dict = dict(zip(param_names, params))
            return -self._evaluate_strategy(strategy_class, data, param_dict)

        result = differential_evolution(
            objective,
            bounds,
            maxiter=n_iterations,
            popsize=15,
            tol=0.01,
            mutation=(0.5, 1),
            recombination=0.7,
        )

        best_params = dict(zip(param_names, result.x))
        return best_params

    def _acquisition_function(self, gp, bounds, X_sample):
        """采集函数 - Upper Confidence Bound"""
        n_samples = 1000
        X_random = np.random.uniform(
            [b[0] for b in bounds],
            [b[1] for b in bounds],
            size=(n_samples, len(bounds)),
        )

        mu, sigma = gp.predict(X_random, return_std=True)
        ucb = mu + 2.0 * sigma  # UCB采集函数

        best_idx = ucb.argmax()
        return X_random[best_idx]

    def _evaluate_strategy(
        self, strategy_class, data: pd.DataFrame, params: Dict
    ) -> float:
        """
        评估策略性能
        使用Walk-Forward验证
        """
        try:
            strategy = strategy_class()
            strategy.params = params

            # 时序交叉验证
            tscv = TimeSeriesSplit(n_splits=3)
            scores = []

            for train_idx, test_idx in tscv.split(data):
                train_data = data.iloc[train_idx]
                test_data = data.iloc[test_idx]

                # 在测试集上评估
                signals = []
                for i in range(len(test_data)):
                    window_data = test_data.iloc[:i+1]
                    if len(window_data) < 30:  # 最小数据要求
                        continue
                    signal = strategy.compute(window_data, "TEST")
                    if signal:
                        signals.append(signal)

                # 简单的绩效评估
                if len(signals) > 0:
                    # 计算收益
                    returns = []
                    for sig in signals:
                        # 简化：假设每次信号后持仓N天
                        returns.append(np.random.normal(0.01, 0.02))  # 模拟收益

                    # 夏普比率
                    if len(returns) > 0:
                        sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252)
                        scores.append(sharpe)

            return np.mean(scores) if scores else 0.0

        except Exception as e:
            print(f"评估失败: {e}")
            return 0.0

    def combine_strategies(
        self, strategies: List, data: pd.DataFrame
    ) -> Tuple[List, np.ndarray]:
        """
        自动策略组合
        使用最大夏普比率优化权重

        Returns:
            (策略列表, 权重数组)
        """
        print(f"开始优化策略组合，共{len(strategies)}个策略...")

        # 计算每个策略的收益序列
        returns_matrix = []
        for strategy in strategies:
            strategy_returns = self._get_strategy_returns(strategy, data)
            returns_matrix.append(strategy_returns)

        returns_matrix = np.array(returns_matrix).T  # (时间, 策略数)

        # 计算相关性矩阵
        correlation = np.corrcoef(returns_matrix.T)
        print(f"策略相关性矩阵:\n{correlation}")

        # 优化权重（最大化夏普比率）
        n_strategies = len(strategies)

        def objective(weights):
            portfolio_return = np.dot(returns_matrix, weights)
            sharpe = np.mean(portfolio_return) / (np.std(portfolio_return) + 1e-10)
            return -sharpe  # 最小化负夏普

        from scipy.optimize import minimize

        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}  # 权重和为1
        bounds = tuple((0, 1) for _ in range(n_strategies))  # 权重在0-1之间

        result = minimize(
            objective,
            x0=np.ones(n_strategies) / n_strategies,  # 初始等权
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        optimal_weights = result.x
        print(f"✓ 最优权重: {dict(zip([s.__class__.__name__ for s in strategies], optimal_weights))}")

        return strategies, optimal_weights

    def _get_strategy_returns(self, strategy, data: pd.DataFrame) -> np.ndarray:
        """获取策略的收益序列"""
        # 简化实现：模拟策略收益
        n = len(data)
        returns = np.random.normal(0.001, 0.02, n)
        return returns

    def analyze_resonance(self, strategies: List, data: pd.DataFrame) -> Dict:
        """
        策略共振分析
        当多个策略同时发出信号时，置信度提升

        Returns:
            共振分析结果
        """
        print("开始策略共振分析...")

        resonance_scores = []

        for i in range(len(data)):
            window_data = data.iloc[:i+1]
            if len(window_data) < 30:
                continue

            # 所有策略的信号
            signals = []
            for strategy in strategies:
                try:
                    signal = strategy.compute(window_data, "TEST")
                    if signal and signal.direction in ["BUY", "SELL"]:
                        signals.append(signal)
                except:
                    pass

            # 分析共振
            if len(signals) >= 2:
                # 统计相同方向的信号数量
                buy_count = sum(1 for s in signals if s.direction == "BUY")
                sell_count = sum(1 for s in signals if s.direction == "SELL")

                max_count = max(buy_count, sell_count)
                resonance_score = max_count / len(strategies)  # 共振比例

                if resonance_score >= 0.5:  # 超过50%策略共振
                    resonance_scores.append({
                        "timestamp": window_data.index[-1],
                        "direction": "BUY" if buy_count > sell_count else "SELL",
                        "resonance_score": resonance_score,
                        "signal_count": max_count,
                    })

        print(f"✓ 发现 {len(resonance_scores)} 个共振点")
        return {
            "resonance_points": resonance_scores,
            "average_resonance": np.mean([r["resonance_score"] for r in resonance_scores]) if resonance_scores else 0,
        }

    def auto_deploy_if_worthy(
        self,
        strategy,
        backtest_result: Dict,
        deployment_criteria: Dict = None,
    ) -> bool:
        """
        高胜率策略自动部署

        Args:
            strategy: 策略对象
            backtest_result: 回测结果
            deployment_criteria: 部署标准

        Returns:
            是否已部署
        """
        if deployment_criteria is None:
            deployment_criteria = {
                "min_sharpe": 2.0,
                "min_win_rate": 0.65,
                "max_drawdown": 0.15,
                "min_trades": 50,
            }

        print(f"\n检查策略 {strategy.__class__.__name__} 是否符合自动部署标准...")

        # 检查各项指标
        sharpe = backtest_result.get("sharpe", 0)
        win_rate = backtest_result.get("win_rate", 0)
        max_dd = abs(backtest_result.get("max_drawdown", 1))
        n_trades = backtest_result.get("total_trades", 0)

        checks = {
            "夏普比率": (sharpe, ">=", deployment_criteria["min_sharpe"]),
            "胜率": (win_rate, ">=", deployment_criteria["min_win_rate"]),
            "最大回撤": (max_dd, "<=", deployment_criteria["max_drawdown"]),
            "交易次数": (n_trades, ">=", deployment_criteria["min_trades"]),
        }

        passed = True
        for name, (value, op, threshold) in checks.items():
            if op == ">=" and value >= threshold:
                print(f"  ✓ {name}: {value:.2f} {op} {threshold}")
            elif op == "<=" and value <= threshold:
                print(f"  ✓ {name}: {value:.2f} {op} {threshold}")
            else:
                print(f"  ✗ {name}: {value:.2f} 不满足 {op} {threshold}")
                passed = False

        if passed:
            print(f"✓ 策略符合标准，自动部署到实盘监控")
            self._deploy_to_live(strategy, backtest_result)
            return True
        else:
            print(f"✗ 策略不符合部署标准")
            return False

    def _deploy_to_live(self, strategy, backtest_result: Dict):
        """部署策略到实盘"""
        deployment_info = {
            "strategy": strategy,
            "strategy_name": strategy.__class__.__name__,
            "deployed_at": pd.Timestamp.now(),
            "backtest_result": backtest_result,
            "status": "active",
        }

        self.deployed_strategies.append(deployment_info)

        # TODO: 实际部署逻辑
        # - 加入实盘监控列表
        # - 分配初始资金
        # - 启动信号监听
        # - 发送通知给用户

        print(f"策略已部署，当前实盘策略数: {len(self.deployed_strategies)}")

    def get_deployed_strategies(self) -> List[Dict]:
        """获取已部署的策略列表"""
        return self.deployed_strategies

    def save_evolution_history(self, filepath: str = "models/evolution_history.pkl"):
        """保存进化历史"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "best_params_history": self.best_params_history,
                "deployed_strategies": [
                    {**d, "strategy": d["strategy"].__class__.__name__}
                    for d in self.deployed_strategies
                ],
            },
            filepath,
        )
        print(f"✓ 进化历史已保存: {filepath}")


# 使用示例
if __name__ == "__main__":
    print("策略自动进化引擎示例")
    print("=" * 60)

    # 创建引擎
    engine = StrategyEvolutionEngine()

    # 模拟数据
    data = pd.DataFrame({
        "close": 3500 + np.cumsum(np.random.randn(1000) * 10),
        "volume": np.random.randint(1000, 10000, 1000),
    })
    data.index = pd.date_range("2023-01-01", periods=1000, freq="D")

    # 示例：优化参数
    from signals.base import BaseStrategy

    class DummyStrategy(BaseStrategy):
        def __init__(self):
            super().__init__()
            self.params = {"fast": 5, "slow": 20}

        def compute(self, data, symbol):
            return None

    param_space = {
        "fast": (2, 20),
        "slow": (20, 100),
    }

    best_params = engine.evolve_parameters(DummyStrategy, data, param_space, n_iterations=30)
    print(f"\n最优参数: {best_params}")
