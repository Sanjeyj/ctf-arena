"""
Unit and Integration tests for Control Validations.
Contains 10 test cases covering ControlValidation model, validation runs, effectiveness scoring, regression detection, hooks wargaming dispatch, and REST APIs.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.control_validation import ControlValidation
from app.models.evidence_record import EvidenceRecord
from app.services.control_validation_service import ControlValidationService
from app.services.evidence_service import EvidenceService
from app.services.hook_service import HookService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def val_setup(app):
    """Fixture for control validation tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(ControlValidation).delete()
        db.session.query(EvidenceRecord).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="V Org 1", slug="v-org-1", plan_type="enterprise")
        o2 = Organization(name="V Org 2", slug="v-org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        ev = EvidenceService.collect("policy_check", "control_plane", "policy", "1", "Control checked.", o1.id)

        try:
            UserRepository.create(
                username="val_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Val Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "val_admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "ev": ev,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_control_validation_model_fields(app, val_setup):
    """Test 1: ControlValidation model fields."""
    with app.app_context():
        import datetime
        now = datetime.datetime.utcnow()
        val = ControlValidation(
            control_reference="NIST-AC-2",
            validation_type="automated",
            expected_result="authorized",
            actual_result="authorized",
            effectiveness_score=1.0,
            status="passed",
            tested_at=now,
            evidence_record_id=val_setup["ev"].id,
            organization_id=val_setup["o1"].id
        )
        db.session.add(val)
        db.session.commit()
        assert val.id is not None
        assert val.control_reference == "NIST-AC-2"
        assert val.effectiveness_score == 1.0


def test_control_validation_repr(app, val_setup):
    """Test 2: ControlValidation repr format."""
    with app.app_context():
        val = ControlValidation(control_reference="NIST-IA-5", status="failed", organization_id=val_setup["o1"].id)
        assert "NIST-IA-5" in repr(val)
        assert "failed" in repr(val)


def test_control_validation_to_dict(app, val_setup):
    """Test 3: ControlValidation serialization."""
    with app.app_context():
        import datetime
        now = datetime.datetime.utcnow()
        val = ControlValidation(
            control_reference="NIST-SC-7",
            validation_type="manual",
            expected_result="firewall_active",
            actual_result="firewall_inactive",
            effectiveness_score=0.2,
            status="failed",
            tested_at=now,
            organization_id=val_setup["o1"].id
        )
        d = val.to_dict()
        assert d["control_reference"] == "NIST-SC-7"
        assert d["status"] == "failed"
        assert d["tested_at"] == now.isoformat()


def test_control_validation_service_passed(app, val_setup):
    """Test 4: Validate control registers passed outcome for high score."""
    with app.app_context():
        val = ControlValidationService.validate_control(
            "NIST-AC-3", "automated", "pass", "pass", 0.95, val_setup["o1"].id, val_setup["ev"].id
        )
        assert val.id is not None
        assert val.status == "passed"


def test_control_validation_service_partial(app, val_setup):
    """Test 5: Validate control registers partial outcome for medium score."""
    with app.app_context():
        val = ControlValidationService.validate_control(
            "NIST-AC-3", "automated", "pass", "warning", 0.75, val_setup["o1"].id
        )
        assert val.status == "partially_effective"


def test_control_validation_service_failed(app, val_setup):
    """Test 6: Validate control registers failed outcome for low score."""
    with app.app_context():
        val = ControlValidationService.validate_control(
            "NIST-AC-3", "automated", "pass", "fail", 0.30, val_setup["o1"].id
        )
        assert val.status == "failed"


def test_control_validation_regression_detection(app, val_setup):
    """Test 7: Regression helper identifies scores drop between consecutive validation runs."""
    with app.app_context():
        # First run: high effectiveness
        ControlValidationService.validate_control("NIST-SC-8", "automated", "pass", "pass", 0.95, val_setup["o1"].id)
        # Second run: lower effectiveness (triggers regression)
        ControlValidationService.validate_control("NIST-SC-8", "automated", "pass", "warning", 0.60, val_setup["o1"].id)

        assert ControlValidationService.detect_regression("NIST-SC-8", val_setup["o1"].id) is True


def test_control_validation_no_regression(app, val_setup):
    """Test 8: Regression helper returns False if score did not drop."""
    with app.app_context():
        # First run: low effectiveness
        ControlValidationService.validate_control("NIST-SC-8", "automated", "pass", "warning", 0.60, val_setup["o1"].id)
        # Second run: higher effectiveness
        ControlValidationService.validate_control("NIST-SC-8", "automated", "pass", "pass", 0.95, val_setup["o1"].id)

        assert ControlValidationService.detect_regression("NIST-SC-8", val_setup["o1"].id) is False


def test_control_validation_hooks(app, val_setup):
    """Test 9: Hooks fire before and after control validations."""
    before_fired = False
    after_fired = False

    def on_before(**kwargs):
        nonlocal before_fired
        before_fired = True

    def on_after(**kwargs):
        nonlocal after_fired
        after_fired = True

    HookService.register_hook("before_control_validation", on_before)
    HookService.register_hook("after_control_validation", on_after)

    with app.app_context():
        ControlValidationService.validate_control(
            "NIST-SC-20", "automated", "pass", "pass", 1.0, val_setup["o1"].id
        )

    assert before_fired is True
    assert after_fired is True


def test_api_validate_control(client, val_setup):
    """Test 10: POST /api/v1/assurance/controls/validate REST endpoint."""
    resp = client.post(
        f'/api/v1/assurance/controls/validate?org_id={val_setup["o1"].id}',
        json={
            'control_reference': 'NIST-AC-4',
            'validation_type': 'automated',
            'expected_result': 'pass',
            'actual_result': 'pass',
            'effectiveness_score': 0.95
        },
        headers=val_setup["headers"]
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["control_reference"] == "NIST-AC-4"
    assert data["status"] == "passed"
