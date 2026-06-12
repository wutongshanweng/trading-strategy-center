"""
端到端集成测试 - 智能升级模块
Tests the full intelligence pipeline: data → factors → regime → RL → resonance → signal
"""
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.alpha import FactorLibrary, FactorEvaluator, FactorCombiner
from core.alpha.alpha101 import Alpha001, Alpha002, Alpha003
from core.rl import TradingEnvironment, PPOAgent, RL_CONFIG
from core.adaptive import (
    BayesianOptimizer,
    RegimeAwareOptimizer,
    WalkForwardValidator,
    ParameterStore,
    OptimizationScheduler,
)
from core.adaptive.bayesian_optimizer import ParameterSpace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv(n: int = 300, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic OHLCV data."""
    rng = np.random.RandomState(seed)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    close = 100.0
    prices = []
    for _ in range(n):
        close *= 1 + rng.normal(0.0005, 0.015)
        prices.append(close)
    prices = np.array(prices)
    return pd.DataFrame(
        {
            "open": prices * (1 + rng.uniform(-0.01, 0.01, n)),
            "high": prices * (1 + rng.uniform(0, 0.02, n)),
            "low": prices * (1 - rng.uniform(0, 0.02, n)),
            "close": prices,
            "volume": rng.randint(1000, 50000, n).astype(float),
        },
        index=dates,
    )


# ===================================================================
# 1. Alpha Factor Pipeline
# ===================================================================

class TestAlphaFactorPipeline:
    """End-to-end test for alpha factor computation, evaluation, and combination."""

    def test_full_alpha_pipeline(self):
        data = _make_ohlcv(200)
        forward_returns = data["close"].pct_change().shift(-1)

        # 1. Build factor library
        library = FactorLibrary()
        library.register("alpha001", lambda d, **kw: Alpha001().compute(d), category="momentum")
        library.register("alpha002", lambda d, **kw: Alpha002().compute(d), category="volume")
        library.register("alpha003", lambda d, **kw: Alpha003().compute(d), category="volatility")
        assert len(library.list_factors()) == 3

        # 2. Compute all factors
        factors_df = library.compute_all(data)
        assert isinstance(factors_df, pd.DataFrame)
        assert set(factors_df.columns) == {"alpha001", "alpha002", "alpha003"}
        assert len(factors_df) == len(data)

        # 3. Evaluate factors
        evaluator = FactorEvaluator(forward_returns=forward_returns)
        for col in factors_df.columns:
            report = evaluator.generate_report(col, factors_df[col].dropna())
            assert report.factor_name == col
            assert isinstance(report.ic_mean, float)
            assert isinstance(report.ir, float)

        # 4. Combine factors
        combiner = FactorCombiner(factors_df)
        combined = combiner.equal_weight()
        assert isinstance(combined, pd.Series)
        assert len(combined) == len(data)

        # 5. Normalize
        normalized = combiner.normalize_factors(method="zscore")
        assert abs(normalized.mean().mean()) < 0.01

    def test_alpha101_classes(self):
        data = _make_ohlcv(100)
        for AlphaCls in [Alpha001, Alpha002, Alpha003]:
            alpha = AlphaCls()
            result = alpha.compute(data)
            assert isinstance(result, pd.Series)
            assert len(result) == len(data)
            assert alpha.name is not None
            assert alpha.category is not None

    def test_ic_weight_combination(self):
        data = _make_ohlcv(100)
        library = FactorLibrary()
        library.register("momentum", lambda d, **kw: d["close"].pct_change(20))
        library.register("volatility", lambda d, **kw: d["close"].pct_change().rolling(20).std())
        factors_df = library.compute_all(data).dropna()

        combiner = FactorCombiner(factors_df)
        ic_values = {"momentum": 0.05, "volatility": -0.03}
        result = combiner.ic_weight(ic_values=ic_values)
        assert isinstance(result, pd.Series)
        assert len(result) == len(factors_df)

    def test_regime_weight_combination(self):
        data = _make_ohlcv(100)
        library = FactorLibrary()
        library.register("momentum", lambda d, **kw: d["close"].pct_change(20))
        library.register("volatility", lambda d, **kw: d["close"].pct_change().rolling(20).std())
        factors_df = library.compute_all(data).dropna()

        regimes = pd.Series(np.where(factors_df["momentum"] > 0, "bull", "bear"), index=factors_df.index)
        combiner = FactorCombiner(factors_df)
        result = combiner.regime_weight(regimes=regimes)
        assert isinstance(result, pd.Series)


# ===================================================================
# 2. RL Environment + Agent Pipeline
# ===================================================================

class TestRLPipeline:
    """End-to-end test for RL environment interaction and agent learning."""

    def test_env_agent_interaction(self):
        data = _make_ohlcv(200)
        env = TradingEnvironment(data, lookback_window=20)
        agent = PPOAgent(
            state_dim=env.observation_space_size,
            action_dim=env.action_space_size,
            hidden_dim=64,
        )

        # Collect experiences
        obs = env.reset(seed=42)
        for _ in range(100):
            action, log_prob, value = agent.select_action(obs, training=True)
            next_obs, reward, done, info = env.step(action)
            agent.store_experience(obs, action, reward, next_obs, done, log_prob, value)
            obs = next_obs
            if done:
                obs = env.reset()

        assert agent.buffer_size == 100

        # Update agent
        metrics = agent.update(num_epochs=2, batch_size=32)
        assert "policy_loss" in metrics
        assert "value_loss" in metrics
        assert agent.buffer_size == 0

    def test_rl_config_consistency(self):
        env_cfg = RL_CONFIG["environment"]
        agent_cfg = RL_CONFIG["agent"]
        train_cfg = RL_CONFIG["training"]
        data_cfg = RL_CONFIG["data"]

        assert env_cfg["initial_balance"] > 0
        assert 0 < env_cfg["commission_rate"] < 1
        assert agent_cfg["gamma"] > 0
        assert train_cfg["num_episodes"] > 0
        assert data_cfg["lookback_window"] > 0

    def test_agent_save_load_during_training(self, tmp_path):
        data = _make_ohlcv(200)
        env = TradingEnvironment(data, lookback_window=20)
        agent = PPOAgent(
            state_dim=env.observation_space_size,
            action_dim=env.action_space_size,
            hidden_dim=64,
        )

        # Train briefly
        obs = env.reset(seed=42)
        for _ in range(50):
            action, log_prob, value = agent.select_action(obs)
            next_obs, reward, done, info = env.step(action)
            agent.store_experience(obs, action, reward, next_obs, done, log_prob, value)
            obs = next_obs
            if done:
                obs = env.reset()
        agent.update(num_epochs=1, batch_size=32)

        # Save
        save_path = str(tmp_path / "rl_model")
        agent.save(save_path)
        assert (tmp_path / "rl_model" / "model.npz").exists()

        # Load into new agent
        agent2 = PPOAgent(
            state_dim=env.observation_space_size,
            action_dim=env.action_space_size,
            hidden_dim=64,
        )
        agent2.load(save_path)
        np.testing.assert_array_almost_equal(agent.policy.W1, agent2.policy.W1)

    def test_full_training_loop(self):
        """Run a short training loop to verify no crashes."""
        data = _make_ohlcv(200)
        env = TradingEnvironment(data, lookback_window=20)
        agent = PPOAgent(
            state_dim=env.observation_space_size,
            action_dim=env.action_space_size,
            hidden_dim=64,
        )

        for episode in range(3):
            obs = env.reset(seed=episode)
            episode_reward = 0.0
            done = False
            steps = 0
            while not done and steps < 100:
                action, log_prob, value = agent.select_action(obs)
                next_obs, reward, done, info = env.step(action)
                agent.store_experience(obs, action, reward, next_obs, done, log_prob, value)
                obs = next_obs
                episode_reward += reward
                steps += 1
            agent.update(num_epochs=1, batch_size=32)


# ===================================================================
# 3. Adaptive Optimization Pipeline
# ===================================================================

class TestAdaptivePipeline:
    """End-to-end test for Bayesian optimization and parameter management."""

    def test_bayesian_optimization(self):
        def objective(params):
            return -(params["x"] - 5.0) ** 2 - (params["y"] - 3.0) ** 2

        param_space = [
            ParameterSpace("x", 0, 10),
            ParameterSpace("y", 0, 10),
        ]
        optimizer = BayesianOptimizer(
            param_space, objective, n_initial=5, random_state=42
        )
        best_params, best_score = optimizer.optimize(n_iterations=15)

        assert best_params is not None
        assert best_score is not None
        assert best_params["x"] > 3
        assert best_params["y"] > 1
        assert best_score > -20

    def test_regime_aware_optimization(self):
        def objective(params, regime):
            base = -(params["x"] - 5.0) ** 2
            if regime == "bull":
                return base + 1
            return base

        param_space = [ParameterSpace("x", 0, 10)]
        optimizer = RegimeAwareOptimizer(
            param_space, objective, n_initial=3, random_state=42
        )

        # Optimize for different regimes
        result_bull = optimizer.optimize(pd.Series([1, 2, 3]), n_iterations=10)
        assert result_bull["regime"] is not None
        assert result_bull["best_params"] is not None

    def test_parameter_store_workflow(self, tmp_path):
        store = ParameterStore(str(tmp_path / "params"))

        # Save versions
        store.save("strategy_A", {"lr": 0.01, "depth": 5}, score=0.85)
        store.save("strategy_A", {"lr": 0.02, "depth": 3}, score=0.92)
        store.save("strategy_B", {"lr": 0.005}, score=0.78)

        # Load latest
        latest = store.load_latest("strategy_A")
        assert latest.version == 2
        assert latest.score == 0.92

        # Get best
        best = store.get_best("strategy_A", higher_is_better=True)
        assert best.score == 0.92

        # List versions
        versions = store.list_versions("strategy_A")
        assert len(versions) == 2

    def test_walk_forward_validation(self):
        validator = WalkForwardValidator(train_ratio=0.7, n_splits=2, expanding=True)
        splits = validator.split(1000)
        assert len(splits) == 2
        for (train_start, train_end), (test_start, test_end) in splits:
            assert train_start == 0
            assert test_start >= train_end

    def test_optimization_scheduler(self, tmp_path):
        store = ParameterStore(str(tmp_path / "params"))
        scheduler = OptimizationScheduler(parameter_store=store)
        assert scheduler is not None
        assert scheduler.parameter_store is store


# ===================================================================
# 4. Market State Detection
# ===================================================================

class TestMarketStatePipeline:
    """End-to-end test for regime detection and state machine."""

    def test_hmm_regime_detection(self):
        from market_state.regime_detector_v2 import HMMDetector, RegimeV2

        data = _make_ohlcv(500, seed=123)
        returns = data["close"].pct_change().dropna()
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()

        detector = HMMDetector(n_regimes=4, covariance_type="diag", n_iter=100)
        detector.fit(returns)

        regimes = detector.predict(returns)
        assert len(regimes) == len(returns)
        for r in regimes:
            assert r in [reg.value for reg in RegimeV2]

    def test_regime_probabilities(self):
        from market_state.regime_detector_v2 import HMMDetector

        data = _make_ohlcv(500, seed=456)
        returns = data["close"].pct_change().dropna()
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()

        detector = HMMDetector(n_regimes=4, covariance_type="diag", n_iter=100)
        detector.fit(returns)

        proba = detector.predict_proba(returns)
        assert isinstance(proba, pd.DataFrame)
        assert len(proba) == len(returns)
        # Probabilities should sum to ~1
        row_sums = proba.sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=0.01)

    def test_change_point_detection(self):
        from market_state.regime_detector_v2 import HMMDetector

        data = _make_ohlcv(500, seed=789)
        returns = data["close"].pct_change().dropna()
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()

        detector = HMMDetector(n_regimes=4, covariance_type="diag", n_iter=100)
        detector.fit(returns)

        change_points = detector.detect_change_point(returns, threshold=0.3)
        assert isinstance(change_points, list)

    def test_old_regime_detector(self):
        from market_state.regime_detector import MarketRegimeDetector

        data = _make_ohlcv(200)
        detector = MarketRegimeDetector()
        info = detector.detect(data)
        assert info.regime is not None
        assert 0 <= info.confidence <= 1


# ===================================================================
# 5. Full Intelligence Pipeline (End-to-End)
# ===================================================================

class TestFullIntelligencePipeline:
    """Integration test: data → factors → regime → RL → resonance → signal."""

    def test_data_to_factors_to_signal(self):
        """Test the pipeline from raw data to combined factor signal."""
        data = _make_ohlcv(200)

        # Step 1: Compute alpha factors
        library = FactorLibrary()
        library.register("alpha001", lambda d, **kw: Alpha001().compute(d), category="momentum")
        library.register("alpha002", lambda d, **kw: Alpha002().compute(d), category="volume")
        library.register("alpha003", lambda d, **kw: Alpha003().compute(d), category="volatility")
        factors_df = library.compute_all(data)

        # Step 2: Evaluate factors
        forward_returns = data["close"].pct_change().shift(-1)
        evaluator = FactorEvaluator(forward_returns=forward_returns)
        ic_values = {}
        for col in factors_df.columns:
            ic_series = evaluator.calculate_ic(factors_df[col].dropna())
            ic_values[col] = float(ic_series.mean()) if not ic_series.empty else 0.0

        # Step 3: Combine factors with IC weighting
        combiner = FactorCombiner(factors_df)
        combined_signal = combiner.ic_weight(ic_values=ic_values)
        assert isinstance(combined_signal, pd.Series)
        assert len(combined_signal) > 0

    def test_data_to_regime_to_adaptive(self):
        """Test regime detection feeds into adaptive optimization."""
        data = _make_ohlcv(500, seed=101)
        returns = data["close"].pct_change().dropna()
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()

        # Detect regime
        from market_state.regime_detector_v2 import HMMDetector
        detector = HMMDetector(n_regimes=4, covariance_type="diag", n_iter=100)
        detector.fit(returns)
        regimes = detector.predict(returns)
        current_regime = regimes[-1] if regimes else "QUIET"

        # Use regime in adaptive optimization
        def objective(params, regime):
            return -(params["x"] - 5.0) ** 2

        param_space = [ParameterSpace("x", 0, 10)]
        optimizer = RegimeAwareOptimizer(
            param_space, objective, n_initial=3, random_state=42
        )
        suggestion = optimizer.suggest_next(current_regime)
        assert "x" in suggestion
        assert 0 <= suggestion["x"] <= 10

    def test_rl_environment_with_real_data(self):
        """Test RL agent training with realistic market data."""
        data = _make_ohlcv(300)

        env = TradingEnvironment(
            data,
            initial_balance=100000.0,
            commission_rate=0.001,
            slippage=0.0001,
            lookback_window=20,
        )
        agent = PPOAgent(
            state_dim=env.observation_space_size,
            action_dim=env.action_space_size,
            hidden_dim=128,
            learning_rate=3e-4,
        )

        # Training loop
        total_rewards = []
        for episode in range(5):
            obs = env.reset(seed=episode)
            episode_reward = 0.0
            done = False
            steps = 0
            while not done and steps < 200:
                action, log_prob, value = agent.select_action(obs)
                next_obs, reward, done, info = env.step(action)
                agent.store_experience(obs, action, reward, next_obs, done, log_prob, value)
                obs = next_obs
                episode_reward += reward
                steps += 1
            total_rewards.append(episode_reward)
            agent.update(num_epochs=2, batch_size=64)

        # Verify training produced valid results
        assert len(total_rewards) == 5
        for r in total_rewards:
            assert isinstance(r, float)

    def test_factor_regime_combined(self):
        """Test combining factors with regime-aware weighting."""
        data = _make_ohlcv(200)

        # Compute factors
        library = FactorLibrary()
        library.register("momentum", lambda d, **kw: d["close"].pct_change(20))
        library.register("volatility", lambda d, **kw: d["close"].pct_change().rolling(20).std())
        factors_df = library.compute_all(data).dropna()

        # Create synthetic regimes
        regimes = pd.Series(
            np.where(factors_df["momentum"] > 0, "bull", "bear"),
            index=factors_df.index,
        )

        # Regime-aware combination
        regime_weights = {
            "bull": {"momentum": 0.7, "volatility": 0.3},
            "bear": {"momentum": 0.3, "volatility": 0.7},
        }
        combiner = FactorCombiner(factors_df)
        result = combiner.regime_weight(regimes=regimes, regime_weights=regime_weights)
        assert isinstance(result, pd.Series)
        assert len(result) == len(factors_df)

    def test_parameter_store_with_optimization(self, tmp_path):
        """Test parameter store integration with optimizer."""
        store = ParameterStore(str(tmp_path / "params"))

        # Run optimization and store results
        def objective(params):
            return -(params["x"] - 5.0) ** 2

        param_space = [ParameterSpace("x", 0, 10)]
        optimizer = BayesianOptimizer(
            param_space, objective, n_initial=3, random_state=42
        )

        for _ in range(10):
            params = optimizer.suggest_next()
            score = objective(params)
            optimizer.update(params, score)
            store.save("optimized_strategy", params, score)

        # Verify stored results
        versions = store.list_versions("optimized_strategy")
        assert len(versions) == 10
        best = store.get_best("optimized_strategy", higher_is_better=True)
        assert best.score > -50


# ===================================================================
# 6. Cross-Module Integration
# ===================================================================

class TestCrossModuleIntegration:
    """Test interactions between different modules."""

    def test_alpha_to_rl_pipeline(self):
        """Alpha factors as RL environment features."""
        data = _make_ohlcv(200)

        # Compute alpha factors
        alpha = Alpha001()
        momentum = alpha.compute(data)
        data["momentum"] = momentum

        # Use enriched data in RL
        env = TradingEnvironment(data, lookback_window=20)
        agent = PPOAgent(
            state_dim=env.observation_space_size,
            action_dim=env.action_space_size,
            hidden_dim=64,
        )

        obs = env.reset(seed=42)
        action, _, _ = agent.select_action(obs)
        next_obs, reward, done, info = env.step(action)
        assert next_obs.shape == (env.observation_space_size,)

    def test_regime_to_factor_weights(self):
        """Regime detection informs factor weighting."""
        data = _make_ohlcv(500, seed=202)
        returns = data["close"].pct_change().dropna()
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()

        # Detect regime
        from market_state.regime_detector_v2 import HMMDetector, RegimeV2
        detector = HMMDetector(n_regimes=4, covariance_type="diag", n_iter=100)
        detector.fit(returns)
        regimes = detector.predict(returns)
        current_regime = regimes[-1]

        # Map HMM regime to simpler regime for factor weighting
        regime_map = {
            RegimeV2.QUIET.value: "neutral",
            RegimeV2.TRENDING.value: "trending",
            RegimeV2.VOLATILE.value: "volatile",
            RegimeV2.CRISIS.value: "crisis",
        }
        simple_regime = regime_map.get(current_regime, "neutral")

        # Adjust factor weights based on regime
        library = FactorLibrary()
        library.register("momentum", lambda d, **kw: d["close"].pct_change(20))
        library.register("volatility", lambda d, **kw: d["close"].pct_change().rolling(20).std())
        factors_df = library.compute_all(data).dropna()

        regime_weights = {
            "neutral": {"momentum": 0.5, "volatility": 0.5},
            "trending": {"momentum": 0.8, "volatility": 0.2},
            "volatile": {"momentum": 0.2, "volatility": 0.8},
            "crisis": {"momentum": 0.3, "volatility": 0.7},
        }
        combiner = FactorCombiner(factors_df)
        # Create regimes aligned with factors_df index
        full_regimes = pd.Series(
            [simple_regime] * len(factors_df), index=factors_df.index
        )
        result = combiner.regime_weight(
            regimes=full_regimes,
            regime_weights=regime_weights,
        )
        assert isinstance(result, pd.Series)

    def test_full_system_integration(self):
        """Complete integration test covering all modules."""
        data = _make_ohlcv(500, seed=303)

        # 1. Alpha factors
        library = FactorLibrary()
        library.register("alpha001", lambda d, **kw: Alpha001().compute(d))
        library.register("alpha002", lambda d, **kw: Alpha002().compute(d))
        library.register("alpha003", lambda d, **kw: Alpha003().compute(d))
        factors_df = library.compute_all(data)

        # 2. Factor evaluation
        forward_returns = data["close"].pct_change().shift(-1)
        evaluator = FactorEvaluator(forward_returns=forward_returns)
        reports = {}
        for col in factors_df.columns:
            reports[col] = evaluator.generate_report(col, factors_df[col].dropna())

        # 3. Factor combination
        combiner = FactorCombiner(factors_df)
        combined = combiner.equal_weight()

        # 4. Regime detection
        from market_state.regime_detector_v2 import HMMDetector
        returns = data["close"].pct_change().dropna()
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
        detector = HMMDetector(n_regimes=4, covariance_type="diag", n_iter=100)
        detector.fit(returns)
        regimes = detector.predict(returns)

        # 5. RL with enriched data
        data["combined_signal"] = combined
        env = TradingEnvironment(data.dropna(), lookback_window=20)
        agent = PPOAgent(
            state_dim=env.observation_space_size,
            action_dim=env.action_space_size,
            hidden_dim=64,
        )

        obs = env.reset(seed=42)
        for _ in range(50):
            action, log_prob, value = agent.select_action(obs)
            next_obs, reward, done, info = env.step(action)
            agent.store_experience(obs, action, reward, next_obs, done, log_prob, value)
            obs = next_obs
            if done:
                obs = env.reset()

        metrics = agent.update(num_epochs=1, batch_size=32)
        assert "policy_loss" in metrics

        # 6. Verify all components worked
        assert len(reports) == 3
        assert len(combined) > 0
        assert len(regimes) == len(returns)
        assert agent.buffer_size == 0
