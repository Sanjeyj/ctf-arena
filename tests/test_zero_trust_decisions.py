"""
Unit and Integration tests for Zero Trust Decisions.
Contains 10 test cases covering combined trust math, boundary evaluations, decision ledger, and wargame event hooks.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.trust_identity import TrustIdentity
from app.models.device_posture import DevicePosture
from app.models.trust_decision import TrustDecision
from app.services.identity_trust_service import IdentityTrustService
from app.services.device_posture_service import DevicePostureService
from app.services.zero_trust_decision_service import ZeroTrustDecisionService
from app.services.hook_service import HookService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def zt_setup(app):
    """Fixture for Zero Trust decision tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(TrustDecision).delete()
        db.session.query(TrustIdentity).delete()
        db.session.query(DevicePosture).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="ZT Org 1", slug="zt-org-1", plan_type="enterprise")
        o2 = Organization(name="ZT Org 2", slug="zt-org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        ident = IdentityTrustService.register_identity(1, "user", o1.id, 1.0, 0.0)
        dev = DevicePostureService.register_device("ZT-Device", "laptop", "windows", o1.id, 1.0, True, "active")

        try:
            UserRepository.create(
                username="zt_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="ZT Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "zt_admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "ident": ident,
            "dev": dev,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_trust_decision_model_fields(app, zt_setup):
    """Test 1: TrustDecision model initialization fields."""
    with app.app_context():
        dec = TrustDecision(
            identity_id=zt_setup["ident"].id,
            device_posture_id=zt_setup["dev"].id,
            resource_type="ctf_challenge",
            resource_id="101",
            requested_action="submit_flag",
            trust_score=85.5,
            decision="allow",
            explanation="Strong identity & posture verified.",
            organization_id=zt_setup["o1"].id
        )
        db.session.add(dec)
        db.session.commit()
        assert dec.id is not None
        assert dec.decision == "allow"
        assert dec.trust_score == 85.5


def test_trust_decision_repr(app, zt_setup):
    """Test 2: TrustDecision repr format."""
    with app.app_context():
        dec = TrustDecision(decision="deny_simulation", trust_score=35.0, organization_id=zt_setup["o1"].id)
        assert "deny_simulation" in repr(dec)
        assert "35.0" in repr(dec)


def test_trust_decision_to_dict(app, zt_setup):
    """Test 3: TrustDecision serialization."""
    with app.app_context():
        dec = TrustDecision(
            identity_id=1,
            device_posture_id=2,
            resource_type="ssh_login",
            resource_id="host_12",
            requested_action="login",
            trust_score=55.0,
            decision="require_step_up",
            organization_id=zt_setup["o1"].id
        )
        d = dec.to_dict()
        assert d["requested_action"] == "login"
        assert d["decision"] == "require_step_up"


def test_calculate_combined_trust_weights(app, zt_setup):
    """Test 4: Weighted combined trust score maps inputs correctly."""
    # Identity (100) * 0.4 = 40
    # Device (100) * 0.3 = 30
    # Policy compliance (100) * 0.2 = 20
    # Sensitivity (100) * 0.1 = 10
    # Total = 40 + 30 + 20 + 10 = 100.00
    val = ZeroTrustDecisionService.calculate_combined_trust(100.0, 100.0, 100.0, 100.0)
    assert val == 100.00


def test_decision_mapping_thresholds_allow(app, zt_setup):
    """Test 5: Trust score boundary >= 80 maps to allow."""
    assert ZeroTrustDecisionService.decide(80.0) == 'allow'
    assert ZeroTrustDecisionService.decide(85.5) == 'allow'


def test_decision_mapping_thresholds_monitoring(app, zt_setup):
    """Test 6: Trust score boundary 60 <= score < 80 maps to monitor."""
    assert ZeroTrustDecisionService.decide(60.0) == 'allow_with_monitoring'
    assert ZeroTrustDecisionService.decide(79.9) == 'allow_with_monitoring'


def test_decision_mapping_thresholds_stepup(app, zt_setup):
    """Test 7: Trust score boundary 40 <= score < 60 maps to step-up."""
    assert ZeroTrustDecisionService.decide(40.0) == 'require_step_up'
    assert ZeroTrustDecisionService.decide(59.9) == 'require_step_up'


def test_decision_mapping_thresholds_deny(app, zt_setup):
    """Test 8: Trust score boundary < 40 maps to deny."""
    assert ZeroTrustDecisionService.decide(39.9) == 'deny_simulation'
    assert ZeroTrustDecisionService.decide(0.0) == 'deny_simulation'


def test_zero_trust_evaluation_hooks(app, zt_setup):
    """Test 9: Trust decision evaluation triggers before and after hooks."""
    before_fired = False
    after_fired = False

    def on_before(**kwargs):
        nonlocal before_fired
        before_fired = True

    def on_after(**kwargs):
        nonlocal after_fired
        after_fired = True

    HookService.register_hook("before_trust_decision", on_before)
    HookService.register_hook("after_trust_decision", on_after)

    with app.app_context():
        ZeroTrustDecisionService.evaluate(
            zt_setup["ident"].id, zt_setup["dev"].id, "port", "80", "connect", zt_setup["o1"].id
        )

    assert before_fired is True
    assert after_fired is True


def test_api_evaluate_trust_decision(client, zt_setup):
    """Test 10: POST /api/v1/assurance/trust/evaluate REST endpoint."""
    resp = client.post(
        f'/api/v1/assurance/trust/evaluate?org_id={zt_setup["o1"].id}',
        json={
            'identity_id': zt_setup["ident"].id,
            'device_id': zt_setup["dev"].id,
            'resource_type': 'ctf_challenge',
            'resource_id': '5',
            'requested_action': 'submit_flag'
        },
        headers=zt_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["decision"] == "allow"
