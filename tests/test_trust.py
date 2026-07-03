"""
Unit and Integration tests for Phase 27 Global Security Intelligence Network — Trust.
Contains 10 test cases covering trust networks, validate/calculate services, update logic, and APIs.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.trust_network import TrustNetwork
from app.services.trust_service import TrustService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def trust_setup(app):
    """Fixture for trust network tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(TrustNetwork).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Trust Org", slug="trust-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="trust_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Trust Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "trust_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_trust_network_creation(app, trust_setup):
    """Test 1: TrustNetwork model fields."""
    with app.app_context():
        trust = TrustNetwork(
            source_org="Org-A",
            target_org="Org-B",
            trust_score=0.85,
            status="active",
            organization_id=trust_setup["org"].id
        )
        db.session.add(trust)
        db.session.commit()
        assert trust.id is not None
        assert trust.source_org == "Org-A"
        assert trust.target_org == "Org-B"
        assert trust.trust_score == 0.85


def test_trust_network_to_dict(app, trust_setup):
    """Test 2: TrustNetwork serialization."""
    with app.app_context():
        trust = TrustNetwork(
            source_org="Federal-CERT",
            target_org="State-CERT",
            trust_score=0.92,
            status="active",
            organization_id=trust_setup["org"].id
        )
        db.session.add(trust)
        db.session.commit()
        d = trust.to_dict()
        assert d["source_org"] == "Federal-CERT"
        assert d["target_org"] == "State-CERT"
        assert d["trust_score"] == 0.92


def test_trust_service_calculate_new(app, trust_setup):
    """Test 3: Calculation of initial trust scores for a new connection."""
    with app.app_context():
        trust = TrustService.calculate("GovAgency", "FinanceSector", org_id=trust_setup["org"].id)
        assert trust.id is not None
        assert trust.source_org == "GovAgency"
        assert trust.status == "pending"


def test_trust_service_calculate_existing(app, trust_setup):
    """Test 4: Calculation returns existing connection without adding duplicates."""
    with app.app_context():
        t1 = TrustService.calculate("GovAgency", "FinanceSector", org_id=trust_setup["org"].id)
        t2 = TrustService.calculate("GovAgency", "FinanceSector", org_id=trust_setup["org"].id)
        assert t1.id == t2.id


def test_trust_service_validate_active(app, trust_setup):
    """Test 5: Validation of active, trusted relationship."""
    with app.app_context():
        trust = TrustNetwork(source_org="A", target_org="B", trust_score=0.7, status="active", organization_id=trust_setup["org"].id)
        db.session.add(trust)
        db.session.commit()

        val = TrustService.validate(trust.id)
        assert val["valid"] is True
        assert val["status"] == "active"


def test_trust_service_validate_suspended(app, trust_setup):
    """Test 6: Validation fails for suspended relationships."""
    with app.app_context():
        trust = TrustNetwork(source_org="A", target_org="B", trust_score=0.1, status="suspended", organization_id=trust_setup["org"].id)
        db.session.add(trust)
        db.session.commit()

        val = TrustService.validate(trust.id)
        assert val["valid"] is False


def test_trust_service_validate_not_found(app):
    """Test 7: Validation logic handles missing trust relationships."""
    with app.app_context():
        val = TrustService.validate(99999)
        assert val["valid"] is False
        assert "not found" in val["reason"]


def test_trust_service_update(app, trust_setup):
    """Test 8: Adjusting trust scores and status updates."""
    with app.app_context():
        trust = TrustNetwork(source_org="A", target_org="B", trust_score=0.5, status="pending", organization_id=trust_setup["org"].id)
        db.session.add(trust)
        db.session.commit()

        # Incremented above 0.6 updates status to active
        TrustService.update(trust.id, 0.15)
        assert trust.trust_score == 0.65
        assert trust.status == "active"

        # Decremented below 0.2 updates status to suspended
        TrustService.update(trust.id, -0.5)
        assert trust.trust_score == 0.15
        assert trust.status == "suspended"


def test_api_get_trust(client, trust_setup):
    """Test 9: GET /api/v1/trust returns relationships list."""
    with client.application.app_context():
        trust = TrustNetwork(source_org="SourceCERT", target_org="DestCERT", trust_score=0.8, status="active", organization_id=trust_setup["org"].id)
        db.session.add(trust)
        db.session.commit()

    resp = client.get(
        f'/api/v1/trust?org_id={trust_setup["org"].id}',
        headers=trust_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["source_org"] == "SourceCERT"


def test_trust_network_custom_attributes(app, trust_setup):
    """Test 10: Validation of custom bounds checks in trust scoring."""
    with app.app_context():
        trust = TrustNetwork(source_org="A", target_org="B", trust_score=0.95, status="active", organization_id=trust_setup["org"].id)
        db.session.add(trust)
        db.session.commit()

        # Verify boundaries: cannot exceed 1.0
        TrustService.update(trust.id, 0.2)
        assert trust.trust_score == 1.0

        # Verify boundaries: cannot go below 0.0
        TrustService.update(trust.id, -2.0)
        assert trust.trust_score == 0.0
