"""
Unit and Integration tests for Telemetry Fabric.
Contains 10 test cases covering TelemetrySource, TelemetryMetric, ingestion, query, hooks, and tenant isolation.
"""
import pytest
import datetime
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.telemetry_source import TelemetrySource
from app.models.telemetry_metric import TelemetryMetric
from app.services.telemetry_service import TelemetryService
from app.research.routes import create_jwt
from app.services.hook_service import HookService


@pytest.fixture
def tel_setup(app):
    """Fixture for telemetry fabric tests."""
    with app.app_context():
        db.session.query(TelemetryMetric).delete()
        db.session.query(TelemetrySource).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        o2 = Organization(name="Org 2", slug="org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_telemetry_source_model(app, tel_setup):
    """Test 1: TelemetrySource initialization and fields."""
    with app.app_context():
        src = TelemetrySource(
            name="Log Agent",
            source_type="agent",
            module_name="lms",
            collection_interval=30,
            organization_id=tel_setup["o1"].id
        )
        db.session.add(src)
        db.session.commit()
        assert src.id is not None
        assert src.name == "Log Agent"
        assert src.status == "active"
        assert src.health_score == 1.0


def test_telemetry_metric_model(app, tel_setup):
    """Test 2: TelemetryMetric model initialization and fields."""
    with app.app_context():
        src = TelemetrySource(
            name="Log Agent",
            source_type="agent",
            module_name="lms",
            organization_id=tel_setup["o1"].id
        )
        db.session.add(src)
        db.session.commit()

        m = TelemetryMetric(
            source_id=src.id,
            metric_name="cpu_load",
            metric_type="gauge",
            metric_value=0.45,
            unit="ratio",
            recorded_at=datetime.datetime.utcnow(),
            organization_id=tel_setup["o1"].id
        )
        db.session.add(m)
        db.session.commit()
        assert m.id is not None
        assert m.metric_name == "cpu_load"
        assert m.metric_value == 0.45


def test_register_source(app, tel_setup):
    """Test 3: TelemetryService register_source."""
    with app.app_context():
        src = TelemetryService.register_source("API Gateway", "metric_collector", "soc", tel_setup["o1"].id, 15)
        assert src.id is not None
        assert src.name == "API Gateway"
        assert src.collection_interval == 15


def test_ingest_metric(app, tel_setup):
    """Test 4: TelemetryService ingest_metric."""
    with app.app_context():
        src = TelemetryService.register_source("API Gateway", "metric_collector", "soc", tel_setup["o1"].id, 15)
        m = TelemetryService.ingest_metric(src.id, "latency", "histogram", 150.0, tel_setup["o1"].id, "ms", {"env": "prod"})
        assert m.id is not None
        assert m.metric_value == 150.0
        assert json.loads(m.dimensions_json) == {"env": "prod"}


def test_normalize_metric(app, tel_setup):
    """Test 5: TelemetryService normalize_metric percentage scaling."""
    with app.app_context():
        v1 = TelemetryService.normalize_metric(85.0, "%")
        assert v1 == 0.85
        v2 = TelemetryService.normalize_metric(0.85, "%")
        assert v2 == 0.85
        v3 = TelemetryService.normalize_metric(150.0, "ms")
        assert v3 == 150.0


def test_query_metrics(app, tel_setup):
    """Test 6: TelemetryService query_metrics window filter."""
    with app.app_context():
        src = TelemetryService.register_source("Agent", "agent", "cti", tel_setup["o1"].id)
        t1 = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
        t2 = datetime.datetime.utcnow() + datetime.timedelta(seconds=10)

        TelemetryService.ingest_metric(src.id, "heartbeat", "counter", 1.0, tel_setup["o1"].id)
        results = TelemetryService.query_metrics(src.id, "heartbeat", t1, t2, tel_setup["o1"].id)
        assert len(results) == 1


def test_source_health(app, tel_setup):
    """Test 7: TelemetryService source_health evaluation."""
    with app.app_context():
        src = TelemetryService.register_source("Agent", "agent", "cti", tel_setup["o1"].id, collection_interval=10)
        # Manually alter last collection to simulated past
        src.last_collection_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=25)
        db.session.commit()

        src = TelemetryService.source_health(src.id, tel_setup["o1"].id)
        assert src.status == "degraded"
        assert src.health_score == 0.5


def test_telemetry_summary(app, tel_setup):
    """Test 8: TelemetryService telemetry_summary aggregates."""
    with app.app_context():
        src = TelemetryService.register_source("Agent", "agent", "cti", tel_setup["o1"].id)
        TelemetryService.ingest_metric(src.id, "memory", "gauge", 0.75, tel_setup["o1"].id)

        summary = TelemetryService.telemetry_summary(tel_setup["o1"].id)
        assert summary["total_sources"] == 1
        assert summary["total_metrics"] == 1
        assert summary["avg_health"] == 1.0


def test_telemetry_hook_dispatch(app, tel_setup):
    """Test 9: before_telemetry_ingest hook controlled mutation."""
    with app.app_context():
        HookService.clear_all()
        def callback(source_id, metric_name, metric_type, metric_value, unit, dimensions_json, org_id):
            return {'metric_value': 999.0}

        HookService.register_hook('before_telemetry_ingest', callback)
        src = TelemetryService.register_source("Agent", "agent", "cti", tel_setup["o1"].id)
        m = TelemetryService.ingest_metric(src.id, "load", "gauge", 5.0, tel_setup["o1"].id)
        assert m.metric_value == 999.0
        HookService.clear_all()


def test_telemetry_tenant_isolation(app, tel_setup):
    """Test 10: Ingesting to other tenant source is rejected or isolated."""
    with app.app_context():
        src1 = TelemetryService.register_source("Agent 1", "agent", "cti", tel_setup["o1"].id)
        src2 = TelemetryService.register_source("Agent 2", "agent", "cti", tel_setup["o2"].id)

        # Ingest with wrong tenant org_id should return None
        m = TelemetryService.ingest_metric(src1.id, "temp", "gauge", 20.0, tel_setup["o2"].id)
        assert m is None
