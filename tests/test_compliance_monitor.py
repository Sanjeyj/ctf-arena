"""
Unit and Integration tests for Phase 26 Autonomous Cyber Enterprise — Compliance Monitor.
Contains 10 test cases covering compliance models, drift detection, and calculation services.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.compliance_monitor import ComplianceMonitor
from app.services.compliance_monitor_service import ComplianceMonitorService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def compliance_setup(app):
    """Fixture for compliance monitoring tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(ComplianceMonitor).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Compliance Org", slug="compliance-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="compliance_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Compliance Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "compliance_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_compliance_monitor_creation(app, compliance_setup):
    """Test 1: ComplianceMonitor model fields."""
    with app.app_context():
        mon = ComplianceMonitor(
            framework="SOC2",
            score=98.5,
            drift_status="stable",
            organization_id=compliance_setup['org'].id
        )
        db.session.add(mon)
        db.session.commit()
        assert mon.framework == "SOC2"
        assert mon.score == 98.5
        assert "SOC2" in repr(mon)


def test_compliance_monitor_to_dict(app, compliance_setup):
    """Test 2: ComplianceMonitor dict serialization."""
    with app.app_context():
        mon = ComplianceMonitor(
            framework="ISO27001",
            score=90.0,
            drift_status="drift_detected",
            organization_id=compliance_setup['org'].id
        )
        db.session.add(mon)
        db.session.commit()
        d = mon.to_dict()
        assert d['framework'] == "ISO27001"
        assert d['drift_status'] == "drift_detected"


def test_compliance_service_evaluate_new(app, compliance_setup):
    """Test 3: ComplianceMonitorService.evaluate_framework registers a new entry."""
    with app.app_context():
        mon = ComplianceMonitorService.evaluate_framework("HIPAA", compliance_setup['org'].id)
        assert mon.id is not None
        assert mon.framework == "HIPAA"
        assert mon.score == 100.0


def test_compliance_service_evaluate_existing(app, compliance_setup):
    """Test 4: ComplianceMonitorService.evaluate_framework locates existing entry."""
    with app.app_context():
        org_id = compliance_setup['org'].id
        mon_first = ComplianceMonitorService.evaluate_framework("NIST", org_id)
        mon_second = ComplianceMonitorService.evaluate_framework("NIST", org_id)
        assert mon_first.id == mon_second.id


def test_compliance_service_detect_drift_stable(app, compliance_setup):
    """Test 5: ComplianceMonitorService.detect_drift stable status."""
    with app.app_context():
        org_id = compliance_setup['org'].id
        mon = ComplianceMonitorService.evaluate_framework("PCI-DSS", org_id)
        mon.score = 95.0
        db.session.commit()

        res = ComplianceMonitorService.detect_drift("PCI-DSS", org_id)
        assert res['drift_status'] == "stable"


def test_compliance_service_detect_drift_detected(app, compliance_setup):
    """Test 6: ComplianceMonitorService.detect_drift active drift detected."""
    with app.app_context():
        org_id = compliance_setup['org'].id
        mon = ComplianceMonitorService.evaluate_framework("GDPR", org_id)
        mon.score = 85.0
        db.session.commit()

        res = ComplianceMonitorService.detect_drift("GDPR", org_id)
        assert res['drift_status'] == "drift_detected"


def test_compliance_service_calculate_score_stable(app, compliance_setup):
    """Test 7: ComplianceMonitorService.calculate_score stable checks."""
    with app.app_context():
        org_id = compliance_setup['org'].id
        score = ComplianceMonitorService.calculate_score("SOX", org_id)
        assert score == 95.0


def test_compliance_service_calculate_score_drifted(app, compliance_setup):
    """Test 8: ComplianceMonitorService.calculate_score drifts penalties."""
    with app.app_context():
        org_id = compliance_setup['org'].id
        ComplianceMonitorService.evaluate_framework("SOX", org_id)
        ComplianceMonitorService.detect_drift("SOX", org_id)
        
        # Manually force drift to test penalty calculations
        mon = ComplianceMonitor.query.filter_by(framework="SOX", organization_id=org_id).first()
        mon.drift_status = "drift_detected"
        db.session.commit()

        score = ComplianceMonitorService.calculate_score("SOX", org_id)
        assert score == 80.0


def test_compliance_monitor_drift_status_default(app, compliance_setup):
    """Test 9: ComplianceMonitor model default status is stable."""
    with app.app_context():
        mon = ComplianceMonitor(framework="FEDRAMP", organization_id=compliance_setup['org'].id)
        db.session.add(mon)
        db.session.commit()
        assert mon.drift_status == "stable"


def test_compliance_service_calculate_score_none(app, compliance_setup):
    """Test 10: ComplianceMonitorService.calculate_score can instantiate and score."""
    with app.app_context():
        score = ComplianceMonitorService.calculate_score("CMMC", compliance_setup['org'].id)
        assert score == 95.0
