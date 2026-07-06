"""
Unit and Integration tests for Phase 31 — Change Management.
Contains 10 test cases covering ChangeRecord model, request changes, risk assessment, wargames simulations, hooks triggering, and REST APIs.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.change_record import ChangeRecord
from app.services.change_management_service import ChangeManagementService
from app.services.hook_service import HookService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def chg_setup(app):
    """Fixture for change management tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(ChangeRecord).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Chg Org", slug="chg-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="chg_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Chg Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "chg_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_change_record_creation(app, chg_setup):
    """Test 1: ChangeRecord model fields."""
    with app.app_context():
        rec = ChangeRecord(
            change_type="feature_enable",
            resource_type="platform_feature_flag",
            resource_id="10",
            requested_by="Alice",
            approval_status="requested",
            risk_score=0.25,
            rollback_plan="Disable flag.",
            status="planned",
            organization_id=chg_setup["org"].id
        )
        db.session.add(rec)
        db.session.commit()
        assert rec.id is not None
        assert rec.change_type == "feature_enable"
        assert rec.requested_by == "Alice"


def test_change_record_repr(app, chg_setup):
    """Test 2: ChangeRecord repr format."""
    with app.app_context():
        rec = ChangeRecord(change_type="policy_update", status="simulated", organization_id=chg_setup["org"].id)
        assert "policy_update" in repr(rec)
        assert "simulated" in repr(rec)


def test_change_record_to_dict(app, chg_setup):
    """Test 3: ChangeRecord serialization."""
    with app.app_context():
        rec = ChangeRecord(
            change_type="model_swap",
            resource_type="model_governance_record",
            resource_id="1",
            requested_by="Bob",
            approval_status="approved",
            status="completed",
            organization_id=chg_setup["org"].id
        )
        d = rec.to_dict()
        assert d["change_type"] == "model_swap"
        assert d["status"] == "completed"
        assert d["requested_by"] == "Bob"


def test_change_service_request(app, chg_setup):
    """Test 4: Service requests a change."""
    with app.app_context():
        rec = ChangeManagementService.request_change("feature_enable", "platform_feature_flag", "3", "Dave", chg_setup["org"].id, "Rollback info")
        assert rec.id is not None
        assert rec.requested_by == "Dave"
        assert rec.status == "planned"


def test_change_service_assess_risk(app, chg_setup):
    """Test 5: Service assesses risk score based on type."""
    with app.app_context():
        r1 = ChangeManagementService.request_change("feature_enable", "platform_feature_flag", "3", "Dave", chg_setup["org"].id)
        r2 = ChangeManagementService.request_change("policy_update", "control_policy", "5", "Dave", chg_setup["org"].id)

        risk1 = ChangeManagementService.assess_risk(r1.id, chg_setup["org"].id)
        risk2 = ChangeManagementService.assess_risk(r2.id, chg_setup["org"].id)

        assert risk1 == 0.2
        assert risk2 == 0.7


def test_change_service_approve(app, chg_setup):
    """Test 6: Service approves change record."""
    with app.app_context():
        rec = ChangeManagementService.request_change("feature_enable", "platform_feature_flag", "3", "Dave", chg_setup["org"].id)
        approved = ChangeManagementService.approve(rec.id, chg_setup["org"].id)
        assert approved.approval_status == "approved"


def test_change_service_simulate(app, chg_setup):
    """Test 7: Service simulates change rollout."""
    with app.app_context():
        rec = ChangeManagementService.request_change("feature_enable", "platform_feature_flag", "3", "Dave", chg_setup["org"].id)
        simulated = ChangeManagementService.simulate(rec.id, chg_setup["org"].id)
        assert simulated.status == "simulated"


def test_change_service_rollback(app, chg_setup):
    """Test 8: Service rolls back change rollout."""
    with app.app_context():
        rec = ChangeManagementService.request_change("feature_enable", "platform_feature_flag", "3", "Dave", chg_setup["org"].id)
        rolled = ChangeManagementService.rollback(rec.id, chg_setup["org"].id)
        assert rolled.status == "rolled_back"


def test_change_service_hooks(app, chg_setup):
    """Test 9: Hooks fire before and after change simulations."""
    before_fired = False
    after_fired = False

    def on_before(**kwargs):
        nonlocal before_fired
        before_fired = True

    def on_after(**kwargs):
        nonlocal after_fired
        after_fired = True

    HookService.register_hook("before_change_simulation", on_before)
    HookService.register_hook("after_change_simulation", on_after)

    with app.app_context():
        rec = ChangeManagementService.request_change("feature_enable", "platform_feature_flag", "3", "Dave", chg_setup["org"].id)
        ChangeManagementService.simulate(rec.id, chg_setup["org"].id)

    assert before_fired is True
    assert after_fired is True


def test_api_simulate_change(client, chg_setup):
    """Test 10: POST /api/v1/control-plane/changes/<id>/simulate REST endpoint."""
    with client.application.app_context():
        rec = ChangeManagementService.request_change("feature_enable", "platform_feature_flag", "3", "Dave", chg_setup["org"].id)
        change_id = rec.id

    resp = client.post(
        f'/api/v1/control-plane/changes/{change_id}/simulate?org_id={chg_setup["org"].id}',
        headers=chg_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "simulated"
    assert data["risk_score"] == 0.2
