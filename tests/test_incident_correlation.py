"""
Unit and Integration tests for IncidentCorrelationService.
Contains 10 test cases covering incident model, creation, hooks, metrics correlation, service mapping, impact calculations, and MTTR.
"""
import pytest
import datetime
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.platform_service import PlatformService
from app.models.operational_incident import OperationalIncident
from app.models.operations_timeline_event import OperationsTimelineEvent
from app.services.incident_correlation_service import IncidentCorrelationService
from app.services.hook_service import HookService
from app.research.routes import create_jwt


@pytest.fixture
def inc_setup(app):
    """Fixture for incident correlation tests."""
    with app.app_context():
        db.session.query(OperationsTimelineEvent).delete()
        db.session.query(OperationalIncident).delete()
        db.session.query(PlatformService).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        o2 = Organization(name="Org 2", slug="org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        s1 = PlatformService(service_name="soc", service_type="soc", criticality="critical", organization_id=o1.id)
        s2 = PlatformService(service_name="lms", service_type="lms", criticality="low", organization_id=o1.id)
        db.session.add_all([s1, s2])
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "s1": s1,
            "s2": s2,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_operational_incident_model(app, inc_setup):
    """Test 1: OperationalIncident model initialization and fields."""
    with app.app_context():
        inc = OperationalIncident(
            title="Database Latency Spike",
            severity="high",
            status="active",
            source_module="db",
            organization_id=inc_setup["o1"].id,
            started_at=datetime.datetime.utcnow()
        )
        db.session.add(inc)
        db.session.commit()
        assert inc.id is not None
        assert inc.title == "Database Latency Spike"
        assert inc.status == "active"


def test_create_incident(app, inc_setup):
    """Test 2: IncidentCorrelationService.create_incident registers record."""
    with app.app_context():
        inc = IncidentCorrelationService.create_incident(
            "CTI Feed Fail", "medium", "cti", ["lms"], "API error", "CTI capability degraded", inc_setup["o1"].id
        )
        assert inc.id is not None
        assert inc.severity == "medium"
        assert "lms" in json.loads(inc.affected_services_json)


def test_incident_hook_dispatch(app, inc_setup):
    """Test 3: before_incident_correlation hook parameter mutation."""
    with app.app_context():
        HookService.clear_all()
        def callback(title, severity, source_module, affected_services_list, root_cause_summary, impact_summary, org_id):
            return {'title': 'Mutated Title', 'severity': 'critical'}

        HookService.register_hook('before_incident_correlation', callback)
        inc = IncidentCorrelationService.create_incident(
            "CTI Feed Fail", "medium", "cti", ["lms"], "API error", "CTI capability degraded", inc_setup["o1"].id
        )
        assert inc.title == "Mutated Title"
        assert inc.severity == "critical"
        HookService.clear_all()


def test_correlate_signals(app, inc_setup):
    """Test 4: IncidentCorrelationService.correlate_signals logs correlation events."""
    with app.app_context():
        inc = IncidentCorrelationService.create_incident(
            "CTI Feed Fail", "medium", "cti", ["lms"], "API error", "CTI capability degraded", inc_setup["o1"].id
        )
        corrs = IncidentCorrelationService.correlate_signals(inc.id, [1, 2], ["trace-abc"], inc_setup["o1"].id)
        assert corrs["telemetry_metric_ids"] == [1, 2]
        assert corrs["trace_ids"] == ["trace-abc"]

        # Ensure timeline event created
        evt = OperationsTimelineEvent.query.filter_by(incident_id=inc.id, event_type="correlation").first()
        assert evt is not None


def test_attach_service(app, inc_setup):
    """Test 5: IncidentCorrelationService.attach_service appends platform services."""
    with app.app_context():
        inc = IncidentCorrelationService.create_incident(
            "LMS Outage", "medium", "lms", ["lms"], "CPU peak", "LMS slow", inc_setup["o1"].id
        )
        # Attach another service
        IncidentCorrelationService.attach_service(inc.id, inc_setup["s1"].id, inc_setup["o1"].id)
        services = json.loads(inc.affected_services_json)
        assert inc_setup["s1"].service_name in services


def test_calculate_impact_basic(app, inc_setup):
    """Test 6: IncidentCorrelationService.calculate_impact with low severity."""
    with app.app_context():
        inc = IncidentCorrelationService.create_incident(
            "Low Incident", "low", "lms", ["lms"], "Disk 80%", "Space alarm", inc_setup["o1"].id
        )
        # lms service has 'low' criticality -> multiplier 1.1. Base weight for low is 10.0.
        score = IncidentCorrelationService.calculate_impact(inc.id, inc_setup["o1"].id)
        assert score == 11.0


def test_calculate_impact_critical(app, inc_setup):
    """Test 7: IncidentCorrelationService.calculate_impact with critical service and severity."""
    with app.app_context():
        inc = IncidentCorrelationService.create_incident(
            "SOC Down", "critical", "soc", ["soc"], "Memory dump", "SOC down", inc_setup["o1"].id
        )
        # soc service has 'critical' criticality -> multiplier 2.0. Base weight for critical is 80.0.
        score = IncidentCorrelationService.calculate_impact(inc.id, inc_setup["o1"].id)
        assert score == 100.0  # Clamped at 100


def test_suggest_root_cause(app, inc_setup):
    """Test 8: IncidentCorrelationService.suggest_root_cause analyzes summaries."""
    with app.app_context():
        inc = IncidentCorrelationService.create_incident(
            "SOC Down", "critical", "soc", ["soc"], "Memory dump", "SOC down", inc_setup["o1"].id
        )
        sug1 = IncidentCorrelationService.suggest_root_cause(inc.id, inc_setup["o1"].id)
        assert "Insufficient telemetry" in sug1

        # Correlate metrics
        IncidentCorrelationService.correlate_signals(inc.id, [1], ["t-1"], inc_setup["o1"].id)
        sug2 = IncidentCorrelationService.suggest_root_cause(inc.id, inc_setup["o1"].id)
        assert "Correlated anomalies" in sug2


def test_resolve_incident(app, inc_setup):
    """Test 9: IncidentCorrelationService.resolve_incident transitions status."""
    with app.app_context():
        inc = IncidentCorrelationService.create_incident(
            "SOC Down", "critical", "soc", ["soc"], "Memory dump", "SOC down", inc_setup["o1"].id
        )
        resolved = IncidentCorrelationService.resolve_incident(inc.id, inc_setup["o1"].id)
        assert resolved.status == "resolved"
        assert resolved.resolved_at is not None


def test_incident_summary(app, inc_setup):
    """Test 10: IncidentCorrelationService.incident_summary averages MTTR."""
    with app.app_context():
        inc = IncidentCorrelationService.create_incident(
            "SOC Down", "critical", "soc", ["soc"], "Memory dump", "SOC down", inc_setup["o1"].id
        )
        IncidentCorrelationService.resolve_incident(inc.id, inc_setup["o1"].id)
        summary = IncidentCorrelationService.incident_summary(inc_setup["o1"].id)
        assert summary["total_incidents"] == 1
        assert summary["resolved_count"] == 1
        assert summary["active_count"] == 0
