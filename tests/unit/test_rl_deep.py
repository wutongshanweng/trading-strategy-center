"""Unit tests for deep RL, advanced RL, multi-agent RL, and offline RL."""

import numpy as np
import pytest


class TestDQNNetwork:
    def test_forward(self):
        from core.rl.deep.networks import DQNNetwork
        net = DQNNetwork(10, 5, 32)
        x = np.random.randn(1, 10).astype(np.float32)
        q = net.forward(x)
        assert q.shape == (1, 5)

    def test_params(self):
        from core.rl.deep.networks import DQNNetwork
        net = DQNNetwork(10, 5, 32)
        params = net.get_params()
        assert "W1" in params
        net2 = DQNNetwork(10, 5, 32)
        net2.set_params(params)
        x = np.random.randn(2, 10).astype(np.float32)
        np.testing.assert_array_almost_equal(net.forward(x), net2.forward(x))


class TestGaussianActor:
    def test_sample(self):
        from core.rl.deep.networks import GaussianActor
        actor = GaussianActor(10, 2, 32)
        x = np.random.randn(1, 10).astype(np.float32)
        action, log_prob = actor.sample(x)
        assert action.shape == (1, 2)
        assert log_prob.shape == (1, 1)
        assert np.all(np.abs(action) <= 1.0)


class TestTwinCritic:
    def test_forward(self):
        from core.rl.deep.networks import TwinCritic
        critic = TwinCritic(10, 2, 32)
        s = np.random.randn(1, 10).astype(np.float32)
        a = np.random.randn(1, 2).astype(np.float32)
        q = critic.forward(s, a)
        assert q.shape == (1,)


class TestReplayBuffer:
    def test_push_and_sample(self):
        from core.rl.deep.replay_buffer import ReplayBuffer
        buf = ReplayBuffer(100)
        for _ in range(50):
            buf.push(np.random.randn(10), 0, 1.0, np.random.randn(10), False)
        s, a, r, ns, d = buf.sample(32)
        assert s.shape == (32, 10)
        assert a.shape == (32,)
        assert r.shape == (32,)

    def test_capacity(self):
        from core.rl.deep.replay_buffer import ReplayBuffer
        buf = ReplayBuffer(10)
        for i in range(15):
            buf.push(np.array([i]), 0, 0.0, np.array([i]), False)
        assert len(buf) == 10


class TestPrioritizedReplayBuffer:
    def test_sample_and_update(self):
        from core.rl.deep.replay_buffer import PrioritizedReplayBuffer
        buf = PrioritizedReplayBuffer(100)
        for _ in range(50):
            buf.push(np.random.randn(10), 0, 1.0, np.random.randn(10), False)
        s, a, r, ns, d, idx, w = buf.sample(32)
        assert s.shape == (32, 10)
        buf.update_priorities(idx, np.ones(32) * 0.5)


class TestDQNTrainer:
    def test_train(self):
        from core.rl.deep.networks import DQNNetwork
        from core.rl.deep.replay_buffer import ReplayBuffer
        from core.rl.deep.trainers import DQNTrainer

        class DummyEnv:
            observation_space = type("S", (), {"shape": (10,)})()
            action_space = type("A", (), {"n": 5, "sample": lambda self: np.random.randint(5)})()
            def reset(self): return np.random.randn(10).astype(np.float32)
            def step(self, a): return np.random.randn(10).astype(np.float32), 1.0, np.random.random() > 0.9, False, {}

        env = DummyEnv()
        net = DQNNetwork(10, 5, 32)
        buf = ReplayBuffer(100)
        trainer = DQNTrainer(env, net, buf, eps_decay=10, batch_size=8)
        rewards = trainer.train(num_episodes=3, max_steps=10)
        assert len(rewards) == 3


class TestSAC:
    def test_select_action(self):
        from core.rl.advanced.sac import SAC
        sac = SAC(state_dim=10, action_dim=2, hidden_dim=32)
        action = sac.select_action(np.random.randn(10).astype(np.float32))
        assert action.shape == (2,)


class TestTD3:
    def test_select_action(self):
        from core.rl.advanced.td3 import TD3
        td3 = TD3(state_dim=10, action_dim=2, hidden_dim=32)
        action = td3.select_action(np.random.randn(10).astype(np.float32))
        assert action.shape == (2,)


class TestDDPG:
    def test_select_action(self):
        from core.rl.advanced.ddpg import DDPG
        ddpg = DDPG(state_dim=10, action_dim=2, hidden_dim=32)
        action = ddpg.select_action(np.random.randn(10).astype(np.float32))
        assert action.shape == (2,)


class TestMADDPG:
    def test_init_and_select(self):
        from core.rl.multi_agent.algorithms.maddpg import MADDPG
        m = MADDPG(num_agents=2, state_dims=[10, 10], action_dims=[5, 5], hidden_dim=32)
        assert m.num_agents == 2
        actions = m.select_actions([np.random.randn(10), np.random.randn(10)])
        assert len(actions) == 2
        assert actions[0].shape == (5,)


class TestCQL:
    def test_init_and_select(self):
        from core.rl.offline.conservative import CQL
        cql = CQL(state_dim=10, action_dim=2, hidden_dim=32)
        assert cql.alpha == 1.0
        a = cql.select_action(np.random.randn(10).astype(np.float32))
        assert a.shape == (2,)


class TestOfflineDataset:
    def test_sample(self):
        import tempfile, os
        from core.rl.offline.dataset import OfflineDataset
        d = tempfile.mkdtemp()
        data = {
            "states": np.random.randn(100, 10).astype(np.float32),
            "actions": np.random.randn(100, 2).astype(np.float32),
            "rewards": np.random.randn(100).astype(np.float32),
            "next_states": np.random.randn(100, 10).astype(np.float32),
            "dones": np.zeros(100, dtype=np.float32),
        }
        path = os.path.join(d, "data.npz")
        np.savez(path, **data)
        ds = OfflineDataset(path)
        batch = ds.sample(32)
        assert batch[0].shape == (32, 10)
        stats = ds.get_stats()
        assert stats["size"] == 100
