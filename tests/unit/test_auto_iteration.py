"""自动迭代调度 (B 阶段) — 单测。

用临时配置文件, 不触真实 data。测配置读写 + should_run_now 判定。
"""

from datetime import datetime, timedelta

import core.adaptive.auto_iteration as auto


def _redirect(tmp_path):
    auto._CONFIG_FILE = tmp_path / "auto_cfg.json"
    auto._LOG_FILE = tmp_path / "auto_log.json"


class TestConfig:
    def test_default_disabled(self, tmp_path):
        _redirect(tmp_path)
        cfg = auto.get_config()
        assert cfg["enabled"] is False
        assert cfg["interval_hours"] == 24

    def test_update_persists(self, tmp_path):
        _redirect(tmp_path)
        auto.update_config({"enabled": True, "interval_hours": 12})
        cfg = auto.get_config()
        assert cfg["enabled"] is True and cfg["interval_hours"] == 12

    def test_update_ignores_unknown_keys(self, tmp_path):
        _redirect(tmp_path)
        auto.update_config({"enabled": True, "hacker": "x"})
        assert "hacker" not in auto.get_config()


class TestShouldRun:
    def test_disabled_never_runs(self, tmp_path):
        _redirect(tmp_path)
        auto.update_config({"enabled": False})
        assert auto.should_run_now() is False

    def test_enabled_no_last_run_runs(self, tmp_path):
        _redirect(tmp_path)
        auto.update_config({"enabled": True})
        assert auto.should_run_now() is True

    def test_enabled_recent_run_waits(self, tmp_path):
        _redirect(tmp_path)
        auto.update_config({"enabled": True, "interval_hours": 24})
        # 写一个 1 小时前的 last_run
        cfg = auto.get_config()
        cfg["last_run"] = (datetime.now() - timedelta(hours=1)).isoformat()
        import json
        auto._CONFIG_FILE.write_text(json.dumps(cfg), encoding="utf-8")
        assert auto.should_run_now() is False

    def test_enabled_stale_run_triggers(self, tmp_path):
        _redirect(tmp_path)
        auto.update_config({"enabled": True, "interval_hours": 24})
        cfg = auto.get_config()
        cfg["last_run"] = (datetime.now() - timedelta(hours=30)).isoformat()
        import json
        auto._CONFIG_FILE.write_text(json.dumps(cfg), encoding="utf-8")
        assert auto.should_run_now() is True
