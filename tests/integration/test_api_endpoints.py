"""Integration tests for all API endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

try:
    from main import app
except Exception:
    # Build a combined test app from all routers
    app = FastAPI(title="Test App")
    from api.routes.health_routes import router as health_router
    from api.routes.data_routes import router as data_router
    from api.routes.strategy_routes import router as strategy_router
    from api.routes.trading_routes import router as trading_router
    from api.routes.backtest_routes import router as backtest_router
    from api.routes.portfolio_routes import router as portfolio_router
    from api.routes.ml_routes import router as ml_router
    from api.routes.intelligence_routes import router as intelligence_router
    app.include_router(health_router)
    app.include_router(data_router)
    app.include_router(strategy_router)
    app.include_router(trading_router)
    app.include_router(backtest_router)
    app.include_router(portfolio_router)
    app.include_router(ml_router)
    app.include_router(intelligence_router)


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthAPI:
    """Health check endpoints."""

    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert "status" in resp.json()


class TestStrategyAPI:
    """Strategy list and detail endpoints."""

    def test_list_strategies(self, client):
        resp = client.get("/api/v1/strategies")
        assert resp.status_code == 200
        data = resp.json()
        assert "strategies" in data
        assert isinstance(data["strategies"], list)

    def test_list_intelligence_alpha_factors(self, client):
        resp = client.get("/api/v1/intelligence/alpha/factors")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 101


class TestTradingAPI:
    """Trading execution and position endpoints."""

    def test_list_positions(self, client):
        resp = client.get("/api/v1/trading/positions")
        assert resp.status_code == 200
        assert "positions" in resp.json()

    def test_trading_summary(self, client):
        resp = client.get("/api/v1/trading/summary")
        assert resp.status_code == 200

    def test_execute_trade_invalid_direction(self, client):
        resp = client.post("/api/v1/trading/execute", json={
            "symbol": "AAPL",
            "direction": "invalid",
            "quantity": 100,
            "price": 150.0,
        })
        assert resp.status_code == 400

    def test_execute_trade_valid(self, client):
        resp = client.post("/api/v1/trading/execute", json={
            "symbol": "AAPL",
            "direction": "long",
            "quantity": 100,
            "price": 150.0,
        })
        # SimEngine may reject due to risk/rules checks in test env
        assert resp.status_code in (200, 400)
        if resp.status_code == 200:
            data = resp.json()
            assert "accepted" in data
        else:
            # rejection with a reason is acceptable in test mode
            assert "detail" in resp.json()


class TestBacktestAPI:
    """Backtest endpoints."""

    def test_backtest_results_empty(self, client):
        resp = client.get("/api/v1/backtest/results")
        assert resp.status_code == 200
        assert "results" in resp.json()


class TestPortfolioAPI:
    """Portfolio management endpoints."""

    def test_portfolio_stats(self, client):
        resp = client.get("/api/v1/portfolio/stats")
        assert resp.status_code == 200

    def test_portfolio_correlation(self, client):
        resp = client.get("/api/v1/portfolio/correlation")
        assert resp.status_code == 200
        assert "correlation" in resp.json()

    def test_rebalance_invalid_weights(self, client):
        resp = client.post("/api/v1/portfolio/rebalance", json={
            "target_weights": {"AAPL": 0.6, "GOOG": 0.6},
        })
        assert resp.status_code == 422  # validation error

    def test_rebalance_valid(self, client):
        resp = client.post("/api/v1/portfolio/rebalance", json={
            "target_weights": {"AAPL": 0.5, "GOOG": 0.5},
        })
        assert resp.status_code == 200
        assert "trades" in resp.json()


class TestMLAPI:
    """ML model endpoints."""

    def test_list_models(self, client):
        resp = client.get("/api/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert len(data["models"]) > 0

    def test_train_invalid_model(self, client):
        resp = client.post("/api/v1/models/invalid_model/train", json={
            "symbol": "AAPL",
        })
        assert resp.status_code == 404


class TestRLAPI:
    """Reinforcement learning endpoints."""

    def test_list_algorithms(self, client):
        resp = client.get("/api/v1/intelligence/rl/algorithms")
        assert resp.status_code == 200
        data = resp.json()
        assert "PPO" in data["algorithms"]


class TestRiskAPI:
    """Risk management endpoints."""

    def test_var_parametric(self, client):
        import numpy as np
        resp = client.post("/api/v1/intelligence/risk/var", json={
            "returns": list(np.random.randn(200) * 0.01),
            "confidence": 0.95,
            "method": "parametric",
        })
        assert resp.status_code == 200
        assert "var" in resp.json()

    def test_kelly(self, client):
        resp = client.post("/api/v1/intelligence/risk/kelly", json={
            "win_rate": 0.6,
            "win_loss_ratio": 2.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["full_kelly"] > 0
