"""
Unit and Integration tests for Phase 31 — Feature Flags.
Contains 10 test cases covering PlatformFeatureFlag model, enablement, disablement, deterministic cryptographic rollouts, and endpoint evaluations.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.platform_feature_flag import PlatformFeatureFlag
from app.services.feature_flag_service import FeatureFlagService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def ff_setup(app):
    """Fixture for feature flag tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(PlatformFeatureFlag).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="FF Org", slug="ff-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="ff_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="FF Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "ff_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_feature_flag_creation(app, ff_setup):
    """Test 1: PlatformFeatureFlag model fields."""
    with app.app_context():
        flag = PlatformFeatureFlag(
            flag_key="beta_feature",
            description="Beta test module",
            enabled=True,
            rollout_percentage=50,
            environment="production",
            organization_id=ff_setup["org"].id
        )
        db.session.add(flag)
        db.session.commit()
        assert flag.id is not None
        assert flag.flag_key == "beta_feature"
        assert flag.enabled is True
        assert flag.rollout_percentage == 50


def test_feature_flag_repr(app, ff_setup):
    """Test 2: PlatformFeatureFlag repr format."""
    with app.app_context():
        flag = PlatformFeatureFlag(flag_key="flag1", enabled=False, organization_id=ff_setup["org"].id)
        assert "flag1" in repr(flag)
        assert "False" in repr(flag)


def test_feature_flag_to_dict(app, ff_setup):
    """Test 3: PlatformFeatureFlag serialization."""
    with app.app_context():
        flag = PlatformFeatureFlag(
            flag_key="flag2",
            enabled=True,
            rollout_percentage=100,
            environment="staging",
            organization_id=ff_setup["org"].id
        )
        d = flag.to_dict()
        assert d["flag_key"] == "flag2"
        assert d["enabled"] is True
        assert d["rollout_percentage"] == 100
        assert d["environment"] == "staging"


def test_feature_flag_service_create(app, ff_setup):
    """Test 4: Service creates flag successfully."""
    with app.app_context():
        flag = FeatureFlagService.create_flag("service_flag", ff_setup["org"].id, enabled=True, rollout_percentage=80)
        assert flag.id is not None
        assert flag.flag_key == "service_flag"
        assert flag.rollout_percentage == 80


def test_feature_flag_service_enable(app, ff_setup):
    """Test 5: Service enables flag status."""
    with app.app_context():
        flag = FeatureFlagService.create_flag("flag_to_enable", ff_setup["org"].id, enabled=False)
        enabled = FeatureFlagService.enable(flag.id, ff_setup["org"].id)
        assert enabled.enabled is True


def test_feature_flag_service_disable(app, ff_setup):
    """Test 6: Service disables flag status."""
    with app.app_context():
        flag = FeatureFlagService.create_flag("flag_to_disable", ff_setup["org"].id, enabled=True)
        disabled = FeatureFlagService.disable(flag.id, ff_setup["org"].id)
        assert disabled.enabled is False


def test_feature_flag_service_evaluate_not_found(app, ff_setup):
    """Test 7: Evaluating non-existent flag returns False."""
    with app.app_context():
        assert FeatureFlagService.evaluate("non_existent", "user1", ff_setup["org"].id) is False


def test_feature_flag_service_evaluate_disabled(app, ff_setup):
    """Test 8: Evaluating disabled flag returns False."""
    with app.app_context():
        FeatureFlagService.create_flag("disabled_flag", ff_setup["org"].id, enabled=False)
        assert FeatureFlagService.evaluate("disabled_flag", "user1", ff_setup["org"].id) is False


def test_feature_flag_service_evaluate_deterministic_rollout(app, ff_setup):
    """Test 9: Deterministic rollout evaluation uses stable SHA-256 logic."""
    with app.app_context():
        # Set a 50% rollout percentage flag
        FeatureFlagService.create_flag("rollout_flag", ff_setup["org"].id, enabled=True, rollout_percentage=50)

        # Check user A vs user B
        resA = FeatureFlagService.evaluate("rollout_flag", "userA", ff_setup["org"].id)
        resB = FeatureFlagService.evaluate("rollout_flag", "userB", ff_setup["org"].id)

        # Same inputs must always yield the same outputs
        assert FeatureFlagService.evaluate("rollout_flag", "userA", ff_setup["org"].id) == resA
        assert FeatureFlagService.evaluate("rollout_flag", "userB", ff_setup["org"].id) == resB


def test_api_evaluate_flag(client, ff_setup):
    """Test 10: POST /api/v1/control-plane/flags/<id>/evaluate REST endpoint."""
    with client.application.app_context():
        flag = FeatureFlagService.create_flag("api_flag", ff_setup["org"].id, enabled=True, rollout_percentage=100)
        flag_id = flag.id

    resp = client.post(
        f'/api/v1/control-plane/flags/{flag_id}/evaluate?org_id={ff_setup["org"].id}',
        json={'user_id': 'user123'},
        headers=ff_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["enabled"] is True
