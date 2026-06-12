import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.rl.environments import TradingEnvironment, TradeState
from core.rl.agents import PPOAgent, SimpleNetwork
from core.rl.config import RL_CONFIG


def _make_market_data(n: int = 200) -> pd.DataFrame:
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    volume = np.random.randint(1000, 10000, n).astype(float)
    return pd.DataFrame(
        {"close": close, "volume": volume},
        index=dates,
    )


class TestRLConfig:
    def test_config_exists(self):
        assert isinstance(RL_CONFIG, dict)

    def test_environment_config(self):
        assert "environment" in RL_CONFIG
        env_config = RL_CONFIG["environment"]
        assert "initial_balance" in env_config
        assert "commission_rate" in env_config
        assert "slippage" in env_config

    def test_agent_config(self):
        assert "agent" in RL_CONFIG
        agent_config = RL_CONFIG["agent"]
        assert "learning_rate" in agent_config
        assert "gamma" in agent_config
        assert "clip_epsilon" in agent_config

    def test_training_config(self):
        assert "training" in RL_CONFIG
        training_config = RL_CONFIG["training"]
        assert "num_episodes" in training_config
        assert "batch_size" in training_config

    def test_data_config(self):
        assert "data" in RL_CONFIG
        data_config = RL_CONFIG["data"]
        assert "lookback_window" in data_config
        assert "feature_columns" in data_config


class TestTradingEnvironment:
    def test_init(self):
        data = _make_market_data()
        env = TradingEnvironment(data)
        assert env.initial_balance == 100000.0
        assert env.commission_rate == 0.001

    def test_action_space_size(self):
        data = _make_market_data()
        env = TradingEnvironment(data)
        assert env.action_space_size == 3

    def test_observation_space_size(self):
        data = _make_market_data()
        env = TradingEnvironment(data, lookback_window=10)
        expected = 10 * len(data.columns) + 3
        assert env.observation_space_size == expected

    def test_reset(self):
        data = _make_market_data()
        env = TradingEnvironment(data)
        obs = env.reset(seed=42)

        assert isinstance(obs, np.ndarray)
        assert obs.dtype == np.float32
        assert len(obs) == env.observation_space_size

    def test_reset_returns_fresh_state(self):
        data = _make_market_data()
        env = TradingEnvironment(data)

        obs1 = env.reset(seed=42)
        obs2 = env.reset(seed=43)

        assert not np.array_equal(obs1, obs2)

    def test_step_buy(self):
        data = _make_market_data()
        env = TradingEnvironment(data)
        env.reset(seed=42)

        obs, reward, done, info = env.step(1)

        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, float)
        assert isinstance(done, bool)
        assert isinstance(info, dict)
        assert "balance" in info
        assert "position" in info

    def test_step_sell(self):
        data = _make_market_data()
        env = TradingEnvironment(data)
        env.reset(seed=42)

        env.step(1)
        obs, reward, done, info = env.step(2)

        assert isinstance(obs, np.ndarray)
        assert "balance" in info

    def test_step_hold(self):
        data = _make_market_data()
        env = TradingEnvironment(data)
        env.reset(seed=42)

        obs, reward, done, info = env.step(0)

        assert isinstance(obs, np.ndarray)
        assert info["position"] == 0.0

    def test_step_before_reset_raises(self):
        data = _make_market_data()
        env = TradingEnvironment(data)

        with pytest.raises(RuntimeError):
            env.step(0)

    def test_episode_terminates(self):
        data = _make_market_data(n=50)
        env = TradingEnvironment(data, lookback_window=10)
        env.reset(seed=42)

        done = False
        steps = 0
        while not done and steps < 100:
            _, _, done, _ = env.step(0)
            steps += 1

        assert done or steps >= 100

    def test_portfolio_value(self):
        data = _make_market_data()
        env = TradingEnvironment(data)
        env.reset(seed=42)

        portfolio_value = env._get_portfolio_value()
        assert portfolio_value == env.initial_balance

    def test_custom_config(self):
        data = _make_market_data()
        env = TradingEnvironment(
            data,
            initial_balance=50000.0,
            commission_rate=0.002,
            slippage=0.001,
            max_position=0.5,
        )
        assert env.initial_balance == 50000.0
        assert env.commission_rate == 0.002

    def test_observation_shape(self):
        data = _make_market_data()
        env = TradingEnvironment(data, lookback_window=20)
        obs = env.reset(seed=42)

        assert obs.shape == (env.observation_space_size,)


class TestSimpleNetwork:
    def test_init(self):
        net = SimpleNetwork(input_dim=10, output_dim=3)
        assert net.input_dim == 10
        assert net.output_dim == 3
        assert net.W1.shape == (10, 256)
        assert net.W2.shape == (256, 3)

    def test_forward(self):
        net = SimpleNetwork(input_dim=10, output_dim=3)
        x = np.random.randn(10)
        output = net.forward(x)

        assert output.shape == (3,)

    def test_forward_batch(self):
        net = SimpleNetwork(input_dim=10, output_dim=3)
        x = np.random.randn(5, 10)
        output = net.forward(x)

        assert output.shape == (5, 3)

    def test_get_set_params(self):
        net = SimpleNetwork(input_dim=10, output_dim=3)
        params = net.get_params()

        assert "W1" in params
        assert "b1" in params
        assert "W2" in params
        assert "b2" in params

        net2 = SimpleNetwork(input_dim=10, output_dim=3)
        net2.set_params(params)

        np.testing.assert_array_equal(net.W1, net2.W1)


class TestPPOAgent:
    def test_init(self):
        agent = PPOAgent(state_dim=10, action_dim=3)
        assert agent.state_dim == 10
        assert agent.action_dim == 3
        assert agent.buffer_size == 0

    def test_select_action(self):
        agent = PPOAgent(state_dim=10, action_dim=3)
        state = np.random.randn(10)

        action, log_prob, value = agent.select_action(state)

        assert action in [0, 1, 2]
        assert isinstance(log_prob, float)
        assert isinstance(value, float)

    def test_select_action_training(self):
        agent = PPOAgent(state_dim=10, action_dim=3)
        state = np.random.randn(10)

        actions = [agent.select_action(state, training=True)[0] for _ in range(100)]
        assert len(set(actions)) > 1

    def test_select_action_eval(self):
        agent = PPOAgent(state_dim=10, action_dim=3)
        state = np.random.randn(10)

        actions = [agent.select_action(state, training=False)[0] for _ in range(100)]
        assert len(set(actions)) == 1

    def test_store_experience(self):
        agent = PPOAgent(state_dim=10, action_dim=3)
        state = np.random.randn(10)
        next_state = np.random.randn(10)

        agent.store_experience(state, 1, 0.1, next_state, False, -0.5, 0.5)
        assert agent.buffer_size == 1

    def test_buffer_multiple(self):
        agent = PPOAgent(state_dim=10, action_dim=3)

        for _ in range(10):
            state = np.random.randn(10)
            next_state = np.random.randn(10)
            agent.store_experience(state, 0, 0.0, next_state, False)

        assert agent.buffer_size == 10

    def test_compute_gae(self):
        agent = PPOAgent(state_dim=10, action_dim=3)
        rewards = [1.0, 1.0, 1.0]
        values = [0.5, 0.6, 0.7]
        dones = [False, False, True]

        advantages, returns = agent.compute_gae(rewards, values, dones)

        assert len(advantages) == 3
        assert len(returns) == 3

    def test_update(self):
        agent = PPOAgent(state_dim=10, action_dim=3)

        for _ in range(100):
            state = np.random.randn(10)
            next_state = np.random.randn(10)
            agent.store_experience(state, 0, 0.1, next_state, False)

        metrics = agent.update(num_epochs=2, batch_size=32)

        assert "policy_loss" in metrics
        assert "value_loss" in metrics
        assert "entropy" in metrics
        assert agent.buffer_size == 0

    def test_save_and_load(self, tmp_path):
        agent = PPOAgent(state_dim=10, action_dim=3, hidden_dim=64)
        state = np.random.randn(10)
        agent.select_action(state)

        save_path = str(tmp_path / "model")
        agent.save(save_path)

        assert (tmp_path / "model" / "model.npz").exists()
        assert (tmp_path / "model" / "config.json").exists()

        agent2 = PPOAgent(state_dim=10, action_dim=3, hidden_dim=64)
        agent2.load(save_path)

        assert agent2._update_count == agent._update_count

        np.testing.assert_array_almost_equal(
            agent.policy.W1, agent2.policy.W1
        )

    def test_softmax(self):
        agent = PPOAgent(state_dim=10, action_dim=3)
        logits = np.array([1.0, 2.0, 3.0])
        probs = agent._softmax(logits)

        assert abs(probs.sum() - 1.0) < 1e-10
        assert all(p >= 0 for p in probs)

    def test_custom_config(self):
        agent = PPOAgent(
            state_dim=20,
            action_dim=5,
            hidden_dim=128,
            learning_rate=1e-3,
            gamma=0.95,
            gae_lambda=0.9,
            clip_epsilon=0.1,
        )

        assert agent.state_dim == 20
        assert agent.action_dim == 5
        assert agent.hidden_dim == 128
        assert agent.learning_rate == 1e-3
        assert agent.gamma == 0.95
        assert agent.gae_lambda == 0.9
        assert agent.clip_epsilon == 0.1

    def test_update_insufficient_buffer(self):
        agent = PPOAgent(state_dim=10, action_dim=3)

        state = np.random.randn(10)
        next_state = np.random.randn(10)
        agent.store_experience(state, 0, 0.0, next_state, False)

        metrics = agent.update(batch_size=64)
        assert metrics["policy_loss"] == 0.0
