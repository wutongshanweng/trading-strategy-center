"""Unit tests for the monitoring & alerting system."""

import tempfile
import os
import numpy as np
import pytest


class TestMetricsCollector:
    def test_collect(self):
        from monitoring.dashboard.metrics_collector import MetricsCollector
        mc = MetricsCollector()
        mc.register("cpu", lambda: 45.0)
        mc.collect()
        assert mc.get("cpu") == 45.0

    def test_get_all(self):
        from monitoring.dashboard.metrics_collector import MetricsCollector
        mc = MetricsCollector()
        mc.register("a", lambda: 1.0)
        mc.register("b", lambda: 2.0)
        mc.collect()
        assert mc.get_all() == {"a": 1.0, "b": 2.0}


class TestTimeSeriesDB:
    def test_insert_and_query(self):
        from monitoring.dashboard.time_series_db import TimeSeriesDB
        db = TimeSeriesDB(os.path.join(tempfile.mkdtemp(), "test.db"))
        db.insert("cpu", 45.0, {"host": "vps1"})
        db.insert("cpu", 46.0, {"host": "vps1"})
        rows = db.query("cpu", limit=10)
        assert len(rows) == 2
        db.close()


class TestAnomalyDetection:
    def test_zscore(self):
        from monitoring.alerting.anomaly_detection import AnomalyDetection
        ad = AnomalyDetection(method="zscore")
        data = np.concatenate([np.random.randn(100), [100]])
        anomalies = ad.detect(data)
        assert len(anomalies) > 0

    def test_iqr(self):
        from monitoring.alerting.anomaly_detection import AnomalyDetection
        ad = AnomalyDetection(method="iqr")
        data = np.concatenate([np.random.randn(100), [100]])
        anomalies = ad.detect(data)
        assert len(anomalies) > 0


class TestThresholdRules:
    def test_above(self):
        from monitoring.alerting.threshold_rules import ThresholdRules
        tr = ThresholdRules()
        tr.add_rule("high_cpu", "cpu", 80, "above", "warning")
        alerts = tr.evaluate({"cpu": 90})
        assert len(alerts) == 1
        alerts = tr.evaluate({"cpu": 50})
        assert len(alerts) == 0

    def test_below(self):
        from monitoring.alerting.threshold_rules import ThresholdRules
        tr = ThresholdRules()
        tr.add_rule("low_battery", "battery", 20, "below", "critical")
        alerts = tr.evaluate({"battery": 10})
        assert len(alerts) == 1


class TestAlertManager:
    def test_create_and_resolve(self):
        from monitoring.alerting.alert_manager import AlertManager
        am = AlertManager()
        alert = am.create_alert("test", "cpu", 90, 80, "warning")
        assert len(am.get_active()) == 1
        am.resolve(alert["id"])
        assert len(am.get_active()) == 0
        assert len(am.get_history()) == 1


class TestFeishuChannel:
    def test_init(self):
        from monitoring.channels.feishu import FeishuChannel
        fc = FeishuChannel("https://test.webhook")
        assert fc.webhook_url == "https://test.webhook"


class TestEmailChannel:
    def test_init(self):
        from monitoring.channels.email_channel import EmailChannel
        ec = EmailChannel("smtp.test.com", 587, "user", "pass")
        assert ec.host == "smtp.test.com"


class TestReturnAttribution:
    def test_brinson(self):
        from monitoring.performance.return_attribution import ReturnAttribution
        ra = ReturnAttribution()
        result = ra.brinson(
            port_weights={"A": 0.6, "B": 0.4},
            bench_weights={"A": 0.5, "B": 0.5},
            port_returns={"A": 0.1, "B": 0.05},
            bench_returns={"A": 0.08, "B": 0.04},
        )
        assert "allocation" in result
        assert "selection" in result


class TestPerformanceReport:
    def test_daily(self):
        from monitoring.performance.performance_report import PerformanceReport
        pr = PerformanceReport()
        report = pr.daily({
            "date": "2026-01-01", "pnl": 1000, "sharpe": 1.5,
            "max_drawdown": 0.05,
            "positions": [{"symbol": "AAPL", "pnl": 600}],
        })
        assert "date" in report
        assert "summary" in report
