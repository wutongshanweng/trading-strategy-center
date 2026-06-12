import json
import time
from pathlib import Path

import numpy as np
import pytest

from core.adaptive.bayesian_optimizer import BayesianOptimizer, ParameterSpace, TrialResult
from core.adaptive.parameter_store import ParameterStore, ParameterVersion


class TestParameterSpace:
    def test_create_space(self):
        space = ParameterSpace(name="lr", low=0.001, high=1.0, log_scale=True)
        assert space.name == "lr"
        assert space.low == 0.001
        assert space.high == 1.0
        assert space.log_scale is True

    def test_default_log_scale(self):
        space = ParameterSpace(name="n_estimators", low=10, high=1000)
        assert space.log_scale is False


class TestBayesianOptimizer:
    def test_init(self):
        spaces = [ParameterSpace("x", 0, 10)]
        objective = lambda p: p["x"] ** 2
        opt = BayesianOptimizer(spaces, objective)
        assert opt.param_space["x"].name == "x"
        assert opt.trials == []

    def test_normalize_in_range(self):
        opt = BayesianOptimizer(
            [ParameterSpace("x", 0, 10)], lambda p: 0
        )
        assert opt._normalize(5, opt.param_space["x"]) == 0.5
        assert opt._normalize(0, opt.param_space["x"]) == 0.0
        assert opt._normalize(10, opt.param_space["x"]) == 1.0

    def test_log_scale_normalize(self):
        opt = BayesianOptimizer(
            [ParameterSpace("x", 0.001, 1000, log_scale=True)], lambda p: 0
        )
        val = opt._normalize(1, opt.param_space["x"])
        assert 0 < val < 1

    def test_denormalize_roundtrip(self):
        opt = BayesianOptimizer(
            [ParameterSpace("x", 0, 10)], lambda p: 0
        )
        for norm in [0.0, 0.25, 0.5, 0.75, 1.0]:
            denorm = opt._denormalize(norm, opt.param_space["x"])
            renorm = opt._normalize(denorm, opt.param_space["x"])
            assert abs(renorm - norm) < 1e-10

    def test_random_params_in_bounds(self):
        opt = BayesianOptimizer(
            [ParameterSpace("x", 2, 8), ParameterSpace("y", 0, 1)],
            lambda p: 0,
            random_state=42,
        )
        for _ in range(50):
            params = opt._random_params()
            assert 2 <= params["x"] <= 8
            assert 0 <= params["y"] <= 1

    def test_latin_hypercube_in_bounds(self):
        opt = BayesianOptimizer(
            [ParameterSpace("x", 2, 8), ParameterSpace("y", 0, 1)],
            lambda p: 0,
            random_state=42,
        )
        samples = opt._sample_latin_hypercube(10)
        assert len(samples) == 10
        for s in samples:
            assert 2 <= s["x"] <= 8
            assert 0 <= s["y"] <= 1

    def test_suggest_next_random_when_few_trials(self):
        opt = BayesianOptimizer(
            [ParameterSpace("x", 0, 10)],
            lambda p: 0,
            n_initial=5,
            random_state=42,
        )
        for _ in range(4):
            params = opt._random_params()
            opt.update(params, 0)

        suggestion = opt.suggest_next()
        assert "x" in suggestion
        assert 0 <= suggestion["x"] <= 10

    def test_suggest_next_uses_acquisition_after_initial(self):
        opt = BayesianOptimizer(
            [ParameterSpace("x", 0, 10)],
            lambda p: -(p["x"] - 5) ** 2,
            n_initial=3,
            random_state=42,
        )
        for _ in range(3):
            params = opt._random_params()
            score = -(params["x"] - 5) ** 2
            opt.update(params, score)

        suggestion = opt.suggest_next()
        assert "x" in suggestion
        assert 0 <= suggestion["x"] <= 10

    def test_update_returns_trial_result(self):
        opt = BayesianOptimizer(
            [ParameterSpace("x", 0, 10)], lambda p: 0
        )
        result = opt.update({"x": 5.0}, 1.0)
        assert isinstance(result, TrialResult)
        assert result.params["x"] == 5.0
        assert result.score == 1.0
        assert len(result.trial_id) == 36

    def test_update_tracks_best(self):
        opt = BayesianOptimizer(
            [ParameterSpace("x", 0, 10)], lambda p: 0
        )
        opt.update({"x": 1.0}, 10.0)
        opt.update({"x": 2.0}, 20.0)
        opt.update({"x": 3.0}, 5.0)

        best_params, best_score = opt.best
        assert best_params["x"] == 2.0
        assert best_score == 20.0

    def test_optimize_finds_maximum(self):
        def objective(params):
            return -(params["x"] - 7.5) ** 2

        opt = BayesianOptimizer(
            [ParameterSpace("x", 0, 10)],
            objective,
            n_initial=5,
            random_state=42,
        )
        best_params, best_score = opt.optimize(n_iterations=15)

        assert best_params is not None
        assert best_score is not None
        assert best_params["x"] > 5
        assert best_score > -10

    def test_get_history(self):
        opt = BayesianOptimizer(
            [ParameterSpace("x", 0, 10)], lambda p: 0
        )
        opt.update({"x": 1.0}, 1.0)
        opt.update({"x": 2.0}, 2.0)

        history = opt.get_history()
        assert len(history) == 2
        assert history[0]["params"]["x"] == 1.0
        assert history[1]["score"] == 2.0


class TestParameterStore:
    def test_init_creates_directory(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        assert (tmp_path / "store").exists()

    def test_save_and_load_latest(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        store.save("test_strategy", {"lr": 0.01}, 0.85)
        store.save("test_strategy", {"lr": 0.02}, 0.90)

        latest = store.load_latest("test_strategy")
        assert latest is not None
        assert latest.version == 2
        assert latest.params["lr"] == 0.02
        assert latest.score == 0.90

    def test_load_nonexistent_returns_none(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        assert store.load_latest("nonexistent") is None

    def test_load_version(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        store.save("s1", {"a": 1}, 0.5)
        store.save("s1", {"a": 2}, 0.6)
        store.save("s1", {"a": 3}, 0.7)

        v2 = store.load_version("s1", 2)
        assert v2.version == 2
        assert v2.params["a"] == 2

    def test_load_version_nonexistent(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        store.save("s1", {"a": 1}, 0.5)
        assert store.load_version("s1", 99) is None

    def test_list_versions(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        store.save("s1", {"a": 1}, 0.5)
        store.save("s1", {"a": 2}, 0.6)

        versions = store.list_versions("s1")
        assert len(versions) == 2
        assert versions[0].version == 1
        assert versions[1].version == 2

    def test_get_best_higher_is_better(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        store.save("s1", {"a": 1}, 0.5)
        store.save("s1", {"a": 2}, 0.9)
        store.save("s1", {"a": 3}, 0.7)

        best = store.get_best("s1", higher_is_better=True)
        assert best.score == 0.9
        assert best.params["a"] == 2

    def test_get_best_lower_is_better(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        store.save("s1", {"a": 1}, 10.0)
        store.save("s1", {"a": 2}, 2.0)
        store.save("s1", {"a": 3}, 5.0)

        best = store.get_best("s1", higher_is_better=False)
        assert best.score == 2.0

    def test_delete_version(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        store.save("s1", {"a": 1}, 0.5)
        store.save("s1", {"a": 2}, 0.6)
        store.save("s1", {"a": 3}, 0.7)

        assert store.delete_version("s1", 2) is True
        versions = store.list_versions("s1")
        assert len(versions) == 2
        assert versions[0].version == 1
        assert versions[1].version == 3

    def test_delete_nonexistent_returns_false(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        store.save("s1", {"a": 1}, 0.5)
        assert store.delete_version("s1", 99) is False

    def test_clear(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        store.save("s1", {"a": 1}, 0.5)
        store.save("s1", {"a": 2}, 0.6)

        store.clear("s1")
        assert store.list_versions("s1") == []
        assert store.load_latest("s1") is None

    def test_persistence_across_instances(self, tmp_path):
        path = str(tmp_path / "store")
        store1 = ParameterStore(path)
        store1.save("s1", {"lr": 0.01}, 0.85)

        store2 = ParameterStore(path)
        latest = store2.load_latest("s1")
        assert latest is not None
        assert latest.params["lr"] == 0.01

    def test_version_numbering(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        v1 = store.save("s1", {"a": 1}, 0.5)
        v2 = store.save("s1", {"a": 2}, 0.6)
        v3 = store.save("s1", {"a": 3}, 0.7)

        assert v1.version == 1
        assert v2.version == 2
        assert v3.version == 3

    def test_metadata_stored(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        store.save("s1", {"a": 1}, 0.5, metadata={"source": "test"})

        latest = store.load_latest("s1")
        assert latest.metadata is not None
        assert latest.metadata["source"] == "test"

    def test_export_strategy(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        store.save("s1", {"a": 1}, 0.5)
        store.save("s1", {"a": 2}, 0.9)

        export = store.export_strategy("s1")
        assert export is not None
        assert export["strategy_name"] == "s1"
        assert export["total_versions"] == 2
        assert export["best_version"]["score"] == 0.9
        assert len(export["history"]) == 2

    def test_export_empty_strategy(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        assert store.export_strategy("nonexistent") is None

    def test_multiple_strategies_isolated(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        store.save("s1", {"a": 1}, 0.5)
        store.save("s2", {"a": 2}, 0.6)

        v1 = store.load_latest("s1")
        v2 = store.load_latest("s2")

        assert v1.params["a"] == 1
        assert v2.params["a"] == 2

    def test_timestamp_set(self, tmp_path):
        store = ParameterStore(str(tmp_path / "store"))
        before = time.time()
        version = store.save("s1", {"a": 1}, 0.5)
        after = time.time()

        assert before <= version.timestamp <= after


class TestWalkForwardValidator:
    def test_split_expanding(self):
        from core.adaptive.walk_forward_validator import WalkForwardValidator
        
        validator = WalkForwardValidator(train_ratio=0.7, n_splits=3, expanding=True)
        splits = validator.split(1000)
        
        assert len(splits) == 3
        for (train_start, train_end), (test_start, test_end) in splits:
            assert train_start == 0
            assert train_end == 700
            assert test_start == 700
            assert test_end > test_start
    
    def test_split_sliding(self):
        from core.adaptive.walk_forward_validator import WalkForwardValidator
        
        validator = WalkForwardValidator(train_ratio=0.7, n_splits=3, expanding=False)
        splits = validator.split(1000)
        
        assert len(splits) == 3
        for i, ((train_start, train_end), (test_start, test_end)) in enumerate(splits):
            assert train_start == i * 100
            assert train_end == train_start + 700
            assert test_start == train_end
            assert test_end == test_start + 100
    
    def test_split_min_train_size(self):
        from core.adaptive.walk_forward_validator import WalkForwardValidator
        
        validator = WalkForwardValidator(train_ratio=0.7, n_splits=5, min_train_size=500)
        splits = validator.split(1000)
        
        for (train_start, train_end), (test_start, test_end) in splits:
            assert train_end - train_start >= 500
    
    def test_split_too_few_observations(self):
        from core.adaptive.walk_forward_validator import WalkForwardValidator
        
        validator = WalkForwardValidator(train_ratio=0.7, n_splits=5)
        splits = validator.split(100)
        
        assert len(splits) == 0
    
    def test_validate_with_mock_optimizer(self):
        import pandas as pd
        from core.adaptive.walk_forward_validator import WalkForwardValidator
        
        class MockOptimizer:
            def __init__(self, param_space, objective, random_state=None):
                self.param_space = param_space
                self.objective = objective
                self.random_state = random_state
            
            def optimize(self, n_iterations):
                return {"x": 0.5}, 0.8
        
        def objective(params, data):
            return 0.8
        
        validator = WalkForwardValidator(train_ratio=0.7, n_splits=2)
        data = pd.DataFrame({"price": range(1000)})
        
        report = validator.validate(
            data=data,
            objective=objective,
            optimizer_class=MockOptimizer,
            param_space=[],
            n_optimization_iter=10
        )
        
        assert report.n_windows == 2
        assert report.mean_oos_score == 0.8
        assert report.std_oos_score == 0.0
    
    def test_check_robustness(self):
        from core.adaptive.walk_forward_validator import WalkForwardValidator, ValidationReport, WindowResult
        
        validator = WalkForwardValidator()
        
        # Robust report
        robust_report = ValidationReport(
            n_windows=3,
            mean_oos_score=0.8,
            std_oos_score=0.1,
            mean_degradation=-0.1,
            overfit_ratio=0.2,
            windows=[]
        )
        assert validator.check_robustness(robust_report) is True
        
        # Non-robust report (high degradation)
        non_robust_report = ValidationReport(
            n_windows=3,
            mean_oos_score=0.8,
            std_oos_score=0.1,
            mean_degradation=-0.4,
            overfit_ratio=0.2,
            windows=[]
        )
        assert validator.check_robustness(non_robust_report) is False
        
        # Non-robust report (high overfit ratio)
        high_overfit_report = ValidationReport(
            n_windows=3,
            mean_oos_score=0.8,
            std_oos_score=0.1,
            mean_degradation=-0.1,
            overfit_ratio=0.5,
            windows=[]
        )
        assert validator.check_robustness(high_overfit_report) is False
    
    def test_detect_overfitting(self):
        from core.adaptive.walk_forward_validator import WalkForwardValidator, ValidationReport, WindowResult
        
        validator = WalkForwardValidator()
        
        # Not overfitting
        not_overfit_report = ValidationReport(
            n_windows=3,
            mean_oos_score=0.8,
            std_oos_score=0.1,
            mean_degradation=-0.1,
            overfit_ratio=0.2,
            windows=[]
        )
        assert validator.detect_overfitting(not_overfit_report) is False
        
        # Overfitting (high degradation)
        overfit_report = ValidationReport(
            n_windows=3,
            mean_oos_score=0.8,
            std_oos_score=0.1,
            mean_degradation=-0.4,
            overfit_ratio=0.2,
            windows=[]
        )
        assert validator.detect_overfitting(overfit_report) is True
        
        # Overfitting (high overfit ratio)
        high_ratio_report = ValidationReport(
            n_windows=3,
            mean_oos_score=0.8,
            std_oos_score=0.1,
            mean_degradation=-0.1,
            overfit_ratio=0.5,
            windows=[]
        )
        assert validator.detect_overfitting(high_ratio_report) is True


class TestParameterStoreDB:
    def test_save_to_db(self, tmp_path):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from core.db.models import Base, ParameterVersion as DBParameterVersion
        from core.adaptive.parameter_store import ParameterStore
        
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        with Session(engine) as session:
            store = ParameterStore(db_session=session)
            version = store.save("test_strategy", {"lr": 0.01}, 0.85)
            
            assert version.version == 1
            assert version.params["lr"] == 0.01
            assert version.score == 0.85
            
            db_version = session.query(DBParameterVersion).first()
            assert db_version is not None
            assert db_version.strategy_name == "test_strategy"
            assert db_version.params == {"lr": 0.01}
            assert db_version.score == 0.85
    
    def test_load_from_db(self, tmp_path):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from core.db.models import Base, ParameterVersion as DBParameterVersion
        from core.adaptive.parameter_store import ParameterStore
        
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        with Session(engine) as session:
            # Save to DB
            db_version = DBParameterVersion(
                strategy_name="test_strategy",
                version=1,
                params={"lr": 0.01},
                score=0.85,
                timestamp=time.time()
            )
            session.add(db_version)
            session.commit()
            
            # Load from DB
            store = ParameterStore(db_session=session)
            latest = store.load_latest("test_strategy")
            
            assert latest is not None
            assert latest.version == 1
            assert latest.params["lr"] == 0.01
            assert latest.score == 0.85
    
    def test_rollback_version(self, tmp_path):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from core.db.models import Base, ParameterVersion as DBParameterVersion
        from core.adaptive.parameter_store import ParameterStore
        
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        with Session(engine) as session:
            store = ParameterStore(db_session=session)
            
            # Save multiple versions
            store.save("s1", {"a": 1}, 0.5)
            store.save("s1", {"a": 2}, 0.6)
            store.save("s1", {"a": 3}, 0.7)
            
            # Rollback to version 1
            success = store.rollback("s1", 1)
            assert success is True
            
            # Check that version 2 and 3 are deleted
            versions = store.list_versions("s1")
            assert len(versions) == 1
            assert versions[0].version == 1
            assert versions[0].params["a"] == 1
