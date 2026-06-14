"""Unit tests for the intelligence API routes."""

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

try:
    from main import app
except Exception:
    # If full app import fails (missing arch etc), create a lightweight test app
    from api.routes.intelligence_routes import router as intelligence_router
    app = FastAPI()
    app.include_router(intelligence_router)


@pytest.fixture
def client():
    return TestClient(app)


class TestRiskAPI:
    def test_var_historical(self, client):
        resp = client.post("/api/v1/intelligence/risk/var", json={
            "returns": list(np.random.randn(200) * 0.01),
            "confidence": 0.95,
            "method": "historical",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "var" in data
        assert data["var"] > 0

    def test_var_parametric(self, client):
        resp = client.post("/api/v1/intelligence/risk/var", json={
            "returns": list(np.random.randn(200) * 0.01),
            "confidence": 0.95,
            "method": "parametric",
        })
        assert resp.status_code == 200

    def test_cvar(self, client):
        resp = client.post("/api/v1/intelligence/risk/cvar", json={
            "returns": list(np.random.randn(200) * 0.01),
            "confidence": 0.95,
        })
        assert resp.status_code == 200
        assert "cvar" in resp.json()

    def test_stress_test(self, client):
        resp = client.post("/api/v1/intelligence/risk/stress-test", json={
            "portfolio": {"AAPL": {"value": 100000, "beta": 1.2}}
        })
        assert resp.status_code == 200
        assert len(resp.json()["scenarios"]) > 0

    def test_kelly(self, client):
        resp = client.post("/api/v1/intelligence/risk/kelly", json={
            "win_rate": 0.6, "win_loss_ratio": 2.0
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["full_kelly"] > 0


class TestRLAPI:
    def test_list_algorithms(self, client):
        resp = client.get("/api/v1/intelligence/rl/algorithms")
        assert resp.status_code == 200
        assert "PPO" in resp.json()["algorithms"]

    def test_train_dqn(self, client):
        resp = client.post("/api/v1/intelligence/rl/dqn/train?num_episodes=3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["rewards"]) == 3


class TestMonitoringAPI:
    def test_collect_metrics(self, client):
        resp = client.post("/api/v1/intelligence/monitoring/collect")
        assert resp.status_code == 200
        assert "system_status" in resp.json()

    def test_get_metrics(self, client):
        client.post("/api/v1/intelligence/monitoring/collect")
        resp = client.get("/api/v1/intelligence/monitoring/metrics")
        assert resp.status_code == 200

    def test_check_alerts(self, client):
        resp = client.post("/api/v1/intelligence/monitoring/alerts/check",
                          json={"metrics": {"cpu": 90, "memory": 10}})
        assert resp.status_code == 200
        assert resp.json()["count"] == 2


class TestAlphaAPI:
    @pytest.fixture(autouse=True)
    def _ensure_factors(self):
        """Ensure FactorRegistry is fully populated before each Alpha API test.

        This prevents test-isolation failures when running the full suite:
        other tests may inadvertently clear the registry class-level state.
        """
        from core.alpha.alpha101.factor_registry import FactorRegistry
        if len(FactorRegistry.list_all()) < 101:
            FactorRegistry.reset()
            FactorRegistry.ensure_initialized()
        return

    def test_list_factors(self, client):
        resp = client.get("/api/v1/intelligence/alpha/factors")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 101, f"Expected >=101 factors, got {data['count']}"

    def test_compute_factors(self, client):
        resp = client.post("/api/v1/intelligence/alpha/compute",
                          json={"factor_names": ["alpha001", "alpha002"], "n_rows": 50})
        assert resp.status_code == 200
        assert resp.json()["count"] == 2
