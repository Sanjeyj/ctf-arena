"""
Unit and Integration tests for Phase 31 — Governance Policies.
Contains 10 test cases covering ControlPolicy model, create policy, observe/warn/deny enforcement modes, hooks triggering, and REST APIs.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.control_policy import ControlPolicy
from app.services.control_policy_service import ControlPolicyService
from app.services.hook_service import HookService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def pol_setup(app):
    """Fixture for policy tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(ControlPolicy).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Pol Org", slug="pol-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="pol_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Pol Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "pol_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_control_policy_creation(app, pol_setup):
    """Test 1: ControlPolicy model fields."""
    with app.app_context():
        pol = ControlPolicy(
            policy_name="SOC Policy",
            policy_type="soc",
            rule_json='{"min_severity": "high"}',
            enforcement_mode="warn",
            status="active",
            version="1.1.0",
            organization_id=pol_setup["org"].id
        )
        db.session.add(pol)
        db.session.commit()
        assert pol.id is not None
        assert pol.policy_name == "SOC Policy"
        assert pol.enforcement_mode == "warn"


def test_control_policy_repr(app, pol_setup):
    """Test 2: ControlPolicy repr format."""
    with app.app_context():
        pol = ControlPolicy(policy_name="CTI Check", status="inactive", organization_id=pol_setup["org"].id)
        assert "CTI Check" in repr(pol)
        assert "inactive" in repr(pol)


def test_control_policy_to_dict(app, pol_setup):
    """Test 3: ControlPolicy serialization."""
    with app.app_context():
        pol = ControlPolicy(
            policy_name="Cloud Policy",
            policy_type="cloud",
            rule_json='{"allowed_regions": ["us-east-1"]}',
            enforcement_mode="deny_simulation",
            organization_id=pol_setup["org"].id
        )
        d = pol.to_dict()
        assert d["policy_name"] == "Cloud Policy"
        assert d["rule"] == {"allowed_regions": ["us-east-1"]}
        assert d["enforcement_mode"] == "deny_simulation"


def test_control_policy_service_create(app, pol_setup):
    """Test 4: Service creates policy rule."""
    with app.app_context():
        pol = ControlPolicyService.create_policy(
            "Service Pol", "soc", pol_setup["org"].id, {"readiness": 0.8}, "require_approval"
        )
        assert pol.id is not None
        assert pol.policy_name == "Service Pol"
        assert pol.enforcement_mode == "require_approval"


def test_control_policy_evaluate_compliant(app, pol_setup):
    """Test 5: Evaluation passes with compliant context."""
    with app.app_context():
        pol = ControlPolicyService.create_policy("Min readiness", "overall", pol_setup["org"].id, {"min_val": 0.8})
        res = ControlPolicyService.evaluate(pol.id, {"min_val": 0.8}, pol_setup["org"].id)
        assert res["decision"] == "allow"
        assert len(res["violations"]) == 0


def test_control_policy_evaluate_observe(app, pol_setup):
    """Test 6: Observe mode decision under violations."""
    with app.app_context():
        pol = ControlPolicyService.create_policy("Min readiness", "overall", pol_setup["org"].id, {"min_val": 0.8}, "observe")
        res = ControlPolicyService.evaluate(pol.id, {"min_val": 0.5}, pol_setup["org"].id)
        assert res["decision"] == "observe"
        assert len(res["violations"]) == 1


def test_control_policy_evaluate_warn(app, pol_setup):
    """Test 7: Warn mode decision under violations."""
    with app.app_context():
        pol = ControlPolicyService.create_policy("Min readiness", "overall", pol_setup["org"].id, {"min_val": 0.8}, "warn")
        res = ControlPolicyService.evaluate(pol.id, {"min_val": 0.5}, pol_setup["org"].id)
        assert res["decision"] == "warn"


def test_control_policy_evaluate_deny(app, pol_setup):
    """Test 8: Deny mode decision under violations."""
    with app.app_context():
        pol = ControlPolicyService.create_policy("Min readiness", "overall", pol_setup["org"].id, {"min_val": 0.8}, "deny_simulation")
        res = ControlPolicyService.evaluate(pol.id, {"min_val": 0.5}, pol_setup["org"].id)
        assert res["decision"] == "deny_simulation"


def test_control_policy_hooks_triggering(app, pol_setup):
    """Test 9: Hooks fire before and after policy evaluations."""
    before_fired = False
    after_fired = False

    def on_before(**kwargs):
        nonlocal before_fired
        before_fired = True

    def on_after(**kwargs):
        nonlocal after_fired
        after_fired = True

    HookService.register_hook("before_policy_evaluation", on_before)
    HookService.register_hook("after_policy_evaluation", on_after)

    with app.app_context():
        pol = ControlPolicyService.create_policy("Hook Pol", "overall", pol_setup["org"].id, {"min_val": 0.8})
        ControlPolicyService.evaluate(pol.id, {"min_val": 0.8}, pol_setup["org"].id)

    assert before_fired is True
    assert after_fired is True


def test_api_create_policy(client, pol_setup):
    """Test 10: POST /api/v1/control-plane/policies REST endpoint."""
    resp = client.post(
        f'/api/v1/control-plane/policies?org_id={pol_setup["org"].id}',
        json={
            'policy_name': 'API policy',
            'policy_type': 'soc',
            'rule': {'alert_limit': 10},
            'enforcement_mode': 'warn'
        },
        headers=pol_setup["headers"]
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["policy_name"] == "API policy"
    assert data["enforcement_mode"] == "warn"
