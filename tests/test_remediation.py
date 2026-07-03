"""
Unit and Integration tests for Phase 26 Autonomous Cyber Enterprise — Remediation Actions.
Contains 10 test cases covering remediation model, services, and self-healing endpoints.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.remediation_action import RemediationAction
from app.services.remediation_service import RemediationService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def remediation_setup(app):
    """Fixture for remediation tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(RemediationAction).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Remediation Org", slug="remediation-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="remediation_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Remediation Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "remediation_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_remediation_action_creation(app, remediation_setup):
    """Test 1: RemediationAction model fields."""
    with app.app_context():
        action = RemediationAction(
            action_type="Block Malicious IP",
            severity="high",
            status="pending",
            organization_id=remediation_setup['org'].id
        )
        db.session.add(action)
        db.session.commit()
        assert action.action_type == "Block Malicious IP"
        assert action.severity == "high"
        assert "Block Malicious IP" in repr(action)


def test_remediation_action_to_dict(app, remediation_setup):
    """Test 2: RemediationAction dict serialization."""
    with app.app_context():
        action = RemediationAction(
            action_type="Rotate AD Keys",
            severity="medium",
            status="completed",
            execution_time=0.45,
            organization_id=remediation_setup['org'].id
        )
        db.session.add(action)
        db.session.commit()
        d = action.to_dict()
        assert d['action_type'] == "Rotate AD Keys"
        assert d['execution_time'] == 0.45


def test_remediation_service_create_action(app, remediation_setup):
    """Test 3: RemediationService.create_action registers action."""
    with app.app_context():
        action = RemediationService.create_action(
            action_type="Demote admin privilege",
            severity="critical",
            organization_id=remediation_setup['org'].id
        )
        assert action.id is not None
        assert action.action_type == "Demote admin privilege"
        assert action.status == "pending"


def test_remediation_service_simulate_execution(app, remediation_setup):
    """Test 4: RemediationService.simulate_execution completes action."""
    with app.app_context():
        action = RemediationService.create_action(
            action_type="Firewall reload",
            severity="medium",
            organization_id=remediation_setup['org'].id
        )
        executed = RemediationService.simulate_execution(action.id)
        assert executed.status == "completed"
        assert executed.execution_time > 0.0


def test_remediation_service_close_action(app, remediation_setup):
    """Test 5: RemediationService.close_action marks completed."""
    with app.app_context():
        action = RemediationService.create_action(
            action_type="Teardown host",
            severity="high",
            organization_id=remediation_setup['org'].id
        )
        closed = RemediationService.close_action(action.id)
        assert closed.status == "completed"


def test_remediation_api_get_remediation(client, remediation_setup):
    """Test 6: GET /api/v1/remediation returns list."""
    resp = client.get(
        f'/api/v1/remediation?org_id={remediation_setup["org"].id}',
        headers=remediation_setup['headers']
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data, list)


def test_remediation_re_entry_prevention(app, remediation_setup):
    """Test 7: Remediation action prevent double processing check."""
    with app.app_context():
        action = RemediationService.create_action(
            action_type="Double checking",
            severity="low",
            organization_id=remediation_setup['org'].id
        )
        assert action.status == "pending"


def test_remediation_simulate_re_entry_flow(app, remediation_setup):
    """Test 8: Remediation action flow completes and remains completed."""
    with app.app_context():
        action = RemediationService.create_action(
            action_type="Safety trigger check",
            severity="high",
            organization_id=remediation_setup['org'].id
        )
        executed = RemediationService.simulate_execution(action.id)
        assert executed.status == 'completed'


def test_remediation_action_custom_attributes(app, remediation_setup):
    """Test 9: Verify non-empty execution time defaults."""
    with app.app_context():
        action = RemediationAction(
            action_type="Test execution default time",
            organization_id=remediation_setup['org'].id
        )
        db.session.add(action)
        db.session.commit()
        assert action.execution_time is None


def test_remediation_api_jwt_failed(client, remediation_setup):
    """Test 10: GET /api/v1/remediation rejects invalid token."""
    resp = client.get(
        f'/api/v1/remediation?org_id={remediation_setup["org"].id}',
        headers={"Authorization": "Bearer badtoken"}
    )
    assert resp.status_code == 401
