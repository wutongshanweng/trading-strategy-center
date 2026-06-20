"""ML 模型注册中心 / sklearn 包装 / 超参搜索 / 集成 测试。"""

import numpy as np

from ml.registry import ModelRegistry
from ml.models.sklearn_wrapper import SklearnModel
from ml.hyperopt import HyperoptSearcher
from ml.ensemble import ModelEnsemble


def _xy(n=120, d=6):
    rng = np.random.default_rng(0)
    X = rng.normal(size=(n, d))
    y = X[:, 0] * 0.5 + rng.normal(scale=0.1, size=n)
    return X, y


class TestModelRegistry:
    def test_save_load_roundtrip(self, tmp_path):
        reg = ModelRegistry(str(tmp_path))
        X, y = _xy()
        model = SklearnModel("rf", {"n_estimators": 20}).fit(X, y)
        meta = reg.save(model._model, "rf_test",
                        {"framework": "sklearn", "metric_name": "ic",
                         "metric_value": 0.5, "symbol": "T"})
        assert meta.version == 1
        loaded, lmeta = reg.load("rf_test")
        assert lmeta.metric_value == 0.5
        # 预测一致
        assert np.allclose(loaded.predict(X[:3]), model.predict(X[:3]))

    def test_version_increment(self, tmp_path):
        reg = ModelRegistry(str(tmp_path))
        X, y = _xy()
        m = SklearnModel("ridge").fit(X, y)
        v1 = reg.save(m._model, "v", {"metric_value": 0.1})
        v2 = reg.save(m._model, "v", {"metric_value": 0.2})
        assert v1.version == 1 and v2.version == 2
        assert len(reg.list_models()) == 1  # 同名只一条索引

    def test_list_and_best(self, tmp_path):
        reg = ModelRegistry(str(tmp_path))
        X, y = _xy()
        m = SklearnModel("ridge").fit(X, y)
        reg.save(m._model, "a", {"metric_name": "ic", "metric_value": 0.3})
        reg.save(m._model, "b", {"metric_name": "ic", "metric_value": 0.6})
        best = reg.get_best_by_metric("ic")
        assert best[0][0] == "b"


class TestSklearnModel:
    def test_six_model_types(self):
        X, y = _xy()
        for mt in ["rf", "xgb", "lgbm", "ridge", "svr", "mlp"]:
            m = SklearnModel(mt, {"n_estimators": 20, "max_iter": 50}).fit(X, y)
            preds = m.predict(X[:5])
            assert len(preds) == 5  # 验收项 5


class TestHyperopt:
    def _train_fn(self, params):
        # 简单凸函数: 越接近 5 越好
        return -((params["x"] - 5) ** 2)

    def test_random(self):
        bp, bs = HyperoptSearcher().search(
            self._train_fn, {"x": (0, 10, "float")}, n_trials=20, method="random")
        assert bp is not None and bs <= 0

    def test_grid(self):
        bp, bs = HyperoptSearcher().search(
            self._train_fn, {"x": (0, 10, "int")}, method="grid")
        assert bp["x"] == 5  # 网格应找到最优整数点

    def test_optuna(self):
        bp, bs = HyperoptSearcher().search(
            self._train_fn, {"x": (0, 10, "float")}, n_trials=20, method="optuna")
        assert bp is not None  # 验收项 3


class TestEnsemble:
    def test_voting_shape(self):
        X, y = _xy()
        m1 = SklearnModel("rf", {"n_estimators": 20}).fit(X, y)
        m2 = SklearnModel("ridge").fit(X, y)
        ens = ModelEnsemble("voting")
        ens.add_model(m1, 0.6)
        ens.add_model(m2, 0.4)
        pred = ens.predict(X)
        assert len(pred) == len(X)  # 验收项 4

    def test_stacking(self):
        X, y = _xy()
        m1 = SklearnModel("rf", {"n_estimators": 20}).fit(X, y)
        m2 = SklearnModel("ridge").fit(X, y)
        ens = ModelEnsemble("stacking")
        ens.add_model(m1)
        ens.add_model(m2)
        ens.fit(X, y)
        assert len(ens.predict(X)) == len(X)
