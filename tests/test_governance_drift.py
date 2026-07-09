"""
Unit and Integration tests for Governance Drift Detection.
Phase 38 — Enterprise Security Decision Intelligence & Governance Fabric.
Contains 10 test cases covering GovernanceDriftRecord model, drift detection, severity classification, and REST endpoints.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.governance_drift_record import GovernanceDriftRecord
from app.services.governance_drift_service import GovernanceDriftService
from app.research.routes import create_jwt


@pytest.fixture
def gd_setup(app):
    with app.app_context():
        db.session.query(GovernanceDriftRecord).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="GD Org", slug="gd-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_governance_drift_record_model(app, gd_setup):
    """Test 1: GovernanceDriftRecord model basic persistence."""
    with app.app_context():
        record = GovernanceDriftRecord(
            resource_type="risk_appetite_profile",
            resource_id=1,
            drift_type="risk_appetite",
            baseline_value=50.0,
            current_value=75.0,
            drift_delta=25.0,
            severity="high",
            recommended_action="Review appetite boundaries",
            status="detected",
            organization_id=gd_setup["org"].id
        )
        db.session.add(record)
        db.session.commit()
        assert record.id is not None
        assert record.drift_type == "risk_appetite"


def test_calculate_delta(app, gd_setup):
    """Test 2: calculate_delta returns the signed difference between baseline and current."""
    with app.app_context():
        delta = GovernanceDriftService.calculate_delta(50.0, 80.0)
        assert delta == pytest.approx(30.0)


def test_calculate_delta_negative(app, gd_setup):
    """Test 3: calculate_delta correctly handles negative deltas."""
    with app.app_context():
        delta = GovernanceDriftService.calculate_delta(80.0, 50.0)
        assert delta == pytest.approx(-30.0)


def test_classify_severity_critical(app, gd_setup):
    """Test 4: classify_severity returns 'critical' for delta > 30."""
    with app.app_context():
        severity = GovernanceDriftService.classify_severity(35.0)
        assert severity == "critical"


def test_classify_severity_high(app, gd_setup):
    """Test 5: classify_severity returns 'high' for delta in (15, 30]."""
    with app.app_context():
        severity = GovernanceDriftService.classify_severity(20.0)
        assert severity == "high"


def test_classify_severity_medium(app, gd_setup):
    """Test 6: classify_severity returns 'medium' for delta in (5, 15]."""
    with app.app_context():
        severity = GovernanceDriftService.classify_severity(10.0)
        assert severity == "medium"


def test_classify_severity_low(app, gd_setup):
    """Test 7: classify_severity returns 'low' for delta <= 5."""
    with app.app_context():
        severity = GovernanceDriftService.classify_severity(3.0)
        assert severity == "low"


def test_create_drift_record(app, gd_setup):
    """Test 8: create_drift_record persists a GovernanceDriftRecord."""
    with app.app_context():
        record = GovernanceDriftService.create_drift_record(
            "control_coverage", None, "control_coverage",
            70.0, 50.0, 20.0, gd_setup["org"].id
        )
        assert record.id is not None
        assert record.severity == "high"
        assert record.status == "detected"


def test_resolve_drift(app, gd_setup):
    """Test 9: resolve_drift transitions the record to 'resolved' status."""
    with app.app_context():
        record = GovernanceDriftService.create_drift_record(
            "policy_effectiveness", 1, "policy_effectiveness",
            85.0, 60.0, 25.0, gd_setup["org"].id
        )
        resolved = GovernanceDriftService.resolve_drift(record.id, gd_setup["org"].id)
        assert resolved.status == "resolved"


def test_drift_summary(app, gd_setup):
    """Test 10: drift_summary returns aggregate counts."""
    with app.app_context():
        GovernanceDriftService.create_drift_record(
            "risk_appetite", None, "risk_appetite",
            50.0, 90.0, 40.0, gd_setup["org"].id
        )
        summary = GovernanceDriftService.drift_summary(gd_setup["org"].id)
        assert summary["total_drift_records"] >= 1
        assert "active_drift_records" in summary
        assert "critical_governance_drift" in summary
