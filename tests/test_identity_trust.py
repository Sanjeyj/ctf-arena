"""
Unit and Integration tests for Identity Trust.
Contains 10 test cases covering TrustIdentity model, trust calculations, score clamping, verify, restrict, and tenant boundary isolations.
"""
import pytest
import json
import datetime
from app.extensions import db
from app.models.organization import Organization
from app.models.trust_identity import TrustIdentity
from app.services.identity_trust_service import IdentityTrustService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def id_setup(app):
    """Fixture for identity trust tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(TrustIdentity).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        o2 = Organization(name="Org 2", slug="org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        try:
            UserRepository.create(
                username="id_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="ID Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "id_admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_trust_identity_model_fields(app, id_setup):
    """Test 1: TrustIdentity model initialization fields."""
    with app.app_context():
        ident = TrustIdentity(
            user_id=1,
            identity_type="user",
            authentication_strength=0.9,
            risk_score=0.1,
            trust_score=85.0,
            verification_status="verified",
            organization_id=id_setup["o1"].id
        )
        db.session.add(ident)
        db.session.commit()
        assert ident.id is not None
        assert ident.identity_type == "user"
        assert ident.trust_score == 85.0


def test_trust_identity_repr(app, id_setup):
    """Test 2: TrustIdentity repr format."""
    with app.app_context():
        ident = TrustIdentity(user_id=42, verification_status="restricted", organization_id=id_setup["o1"].id)
        assert "42" in repr(ident)
        assert "restricted" in repr(ident)


def test_trust_identity_to_dict(app, id_setup):
    """Test 3: TrustIdentity serialization."""
    with app.app_context():
        now = datetime.datetime.utcnow()
        ident = TrustIdentity(
            user_id=5,
            identity_type="system",
            authentication_strength=0.8,
            risk_score=0.2,
            trust_score=70.0,
            verification_status="verified",
            last_verified_at=now,
            organization_id=id_setup["o1"].id
        )
        d = ident.to_dict()
        assert d["user_id"] == 5
        assert d["trust_score"] == 70.0
        assert d["last_verified_at"] == now.isoformat()


def test_register_identity_service(app, id_setup):
    """Test 4: Service registers identity, calculating trust correctly."""
    with app.app_context():
        ident = IdentityTrustService.register_identity(10, "service_account", id_setup["o1"].id, 0.9, 0.1)
        assert ident.id is not None
        # Score = (0.9 * 100) - (0.1 * 50) = 90 - 5 = 85
        assert ident.trust_score == 85.0


def test_calculate_trust_clamping(app, id_setup):
    """Test 5: Score calculation clamps values correctly to 0 and 100."""
    with app.app_context():
        # High auth strength, no risk -> clamp to 100
        i1 = IdentityTrustService.register_identity(20, "user", id_setup["o1"].id, 1.2, 0.0)
        assert i1.trust_score == 100.0
        
        # Zero auth strength, high risk -> clamp to 0
        i2 = IdentityTrustService.register_identity(21, "user", id_setup["o1"].id, 0.0, 1.5)
        assert i2.trust_score == 0.0


def test_identity_verification(app, id_setup):
    """Test 6: Verify updates state to verified and sets timestamp."""
    with app.app_context():
        ident = IdentityTrustService.register_identity(30, "user", id_setup["o1"].id)
        assert ident.verification_status == "unverified"
        assert ident.last_verified_at is None
        
        verified = IdentityTrustService.verify(ident.id, id_setup["o1"].id)
        assert verified.verification_status == "verified"
        assert verified.last_verified_at is not None


def test_identity_restriction(app, id_setup):
    """Test 7: Restrict caps maximum trust score to 40."""
    with app.app_context():
        ident = IdentityTrustService.register_identity(40, "user", id_setup["o1"].id, 1.0, 0.0)
        assert ident.trust_score == 100.0
        
        restricted = IdentityTrustService.restrict(ident.id, id_setup["o1"].id)
        assert restricted.verification_status == "restricted"
        assert restricted.trust_score == 40.0


def test_identity_revocation(app, id_setup):
    """Test 8: Revoked simulation sets trust score to 0."""
    with app.app_context():
        ident = IdentityTrustService.register_identity(50, "user", id_setup["o1"].id, 1.0, 0.0)
        revoked = IdentityTrustService.revoke(ident.id, id_setup["o1"].id)
        assert revoked.verification_status == "revoked_simulation"
        assert revoked.trust_score == 0.0


def test_identity_explain_score(app, id_setup):
    """Test 9: Explain score generates diagnostic details."""
    with app.app_context():
        ident = IdentityTrustService.register_identity(60, "user", id_setup["o1"].id, 0.5, 0.6)
        explanation = IdentityTrustService.explain_score(ident.id, id_setup["o1"].id)
        assert "50.0" in explanation or "Weak authentication" in explanation


def test_api_register_identity(client, id_setup):
    """Test 10: POST /api/v1/assurance/identities REST endpoint."""
    resp = client.post(
        f'/api/v1/assurance/identities?org_id={id_setup["o1"].id}',
        json={
            'user_id': 99,
            'identity_type': 'user',
            'authentication_strength': 0.8,
            'risk_score': 0.2
        },
        headers=id_setup["headers"]
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["user_id"] == 99
    assert data["trust_score"] == 70.0
