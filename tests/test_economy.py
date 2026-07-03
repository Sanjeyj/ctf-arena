"""
Unit and Integration tests for Phase 28 Cyber Civilization Platform — Economy.
Contains 12 test cases covering security economies, investments, workforce profiles, and APIs.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.security_economy import SecurityEconomy
from app.models.workforce_profile import WorkforceProfile
from app.services.economy_service import EconomyService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def econ_setup(app):
    """Fixture for security economy tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(SecurityEconomy).delete()
        db.session.query(WorkforceProfile).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Econ Org", slug="econ-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="econ_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Econ Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "econ_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_security_economy_creation(app, econ_setup):
    """Test 1: SecurityEconomy model fields."""
    with app.app_context():
        econ = SecurityEconomy(
            investment=150000.0,
            growth_rate=0.08,
            workforce_score=0.8,
            market_value=1200000.0,
            organization_id=econ_setup["org"].id
        )
        db.session.add(econ)
        db.session.commit()
        assert econ.id is not None
        assert econ.investment == 150000.0
        assert econ.growth_rate == 0.08
        assert econ.market_value == 1200000.0


def test_security_economy_to_dict(app, econ_setup):
    """Test 2: SecurityEconomy serialization."""
    with app.app_context():
        econ = SecurityEconomy(
            investment=50000.0,
            growth_rate=0.06,
            workforce_score=0.72,
            market_value=850000.0,
            organization_id=econ_setup["org"].id
        )
        db.session.add(econ)
        db.session.commit()
        d = econ.to_dict()
        assert d["investment"] == 50000.0
        assert d["growth_rate"] == 0.06
        assert d["market_value"] == 850000.0


def test_workforce_profile_creation(app, econ_setup):
    """Test 3: WorkforceProfile model fields."""
    with app.app_context():
        profile = WorkforceProfile(
            role="Analyst",
            skill_score=0.75,
            experience=3,
            certifications="CEH, CISSP",
            organization_id=econ_setup["org"].id
        )
        db.session.add(profile)
        db.session.commit()
        assert profile.id is not None
        assert profile.role == "Analyst"
        assert profile.skill_score == 0.75
        assert profile.experience == 3


def test_workforce_profile_to_dict(app, econ_setup):
    """Test 4: WorkforceProfile serialization."""
    with app.app_context():
        profile = WorkforceProfile(
            role="Architect",
            skill_score=0.92,
            experience=8,
            certifications="CCSP, ISSAP",
            organization_id=econ_setup["org"].id
        )
        db.session.add(profile)
        db.session.commit()
        d = profile.to_dict()
        assert d["role"] == "Architect"
        assert d["skill_score"] == 0.92
        assert d["certifications"] == "CCSP, ISSAP"


def test_economy_service_growth_default(app, econ_setup):
    """Test 5: Growth calculation with no economy profile returns default 5%."""
    with app.app_context():
        rate = EconomyService.growth(org_id=econ_setup["org"].id)
        assert rate == 0.05


def test_economy_service_growth_calculated(app, econ_setup):
    """Test 6: Growth calculation updates correctly using workforce metrics."""
    with app.app_context():
        econ = SecurityEconomy(
            investment=10000.0,
            growth_rate=0.1,
            workforce_score=0.8,
            organization_id=econ_setup["org"].id
        )
        db.session.add(econ)
        db.session.commit()

        rate = EconomyService.growth(org_id=econ_setup["org"].id)
        # formula: 0.1 * (1.0 + 0.8 * 0.1) = 0.1 * 1.08 = 0.108
        assert rate == 0.108


def test_economy_service_investment_new(app, econ_setup):
    """Test 7: Recording investment creates economy profile if missing."""
    with app.app_context():
        econ = EconomyService.investment(500000.0, org_id=econ_setup["org"].id)
        assert econ.id is not None
        assert econ.investment == 500000.0
        assert econ.market_value == 1750000.0  # 1M default + 500k * 1.5


def test_economy_service_investment_existing(app, econ_setup):
    """Test 8: Recording investment on existing profile updates values."""
    with app.app_context():
        econ = SecurityEconomy(
            investment=10000.0,
            growth_rate=0.05,
            workforce_score=0.7,
            market_value=100000.0,
            organization_id=econ_setup["org"].id
        )
        db.session.add(econ)
        db.session.commit()

        EconomyService.investment(10000.0, org_id=econ_setup["org"].id)
        assert econ.investment == 20000.0
        assert econ.market_value == 115000.0  # 100k + 10k * 1.5


def test_economy_service_workforce_empty(app, econ_setup):
    """Test 9: Workforce evaluation with no registered profiles."""
    with app.app_context():
        metrics = EconomyService.workforce(org_id=econ_setup["org"].id)
        assert metrics["total_workforce"] == 0
        assert metrics["avg_skill"] == 0.0
        assert metrics["capacity"] == "low"


def test_economy_service_workforce_high_capacity(app, econ_setup):
    """Test 10: Workforce evaluation for high capacity skills."""
    with app.app_context():
        p1 = WorkforceProfile(role="Lead", skill_score=0.8, organization_id=econ_setup["org"].id)
        p2 = WorkforceProfile(role="Architect", skill_score=0.9, organization_id=econ_setup["org"].id)
        db.session.add_all([p1, p2])
        db.session.commit()

        metrics = EconomyService.workforce(org_id=econ_setup["org"].id)
        assert metrics["total_workforce"] == 2
        assert metrics["avg_skill"] == 0.85
        assert metrics["capacity"] == "high"


def test_executive_ai_recommend_civ_low_score(app, econ_setup):
    """Test 11: Executive AI recommend lists critical recommendations on low scores."""
    with app.app_context():
        # Civilization calculated score defaults to 0.6 (< 0.65 threshold)
        from app.services.executive_civilization_ai import ExecutiveCivilizationAI
        recs = ExecutiveCivilizationAI.recommend(org_id=econ_setup["org"].id)
        assert any("CRITICAL" in r for r in recs)


def test_api_get_economy(client, econ_setup):
    """Test 12: GET /api/v1/economy REST API endpoint."""
    with client.application.app_context():
        econ = SecurityEconomy(
            investment=200000.0,
            growth_rate=0.07,
            workforce_score=0.75,
            market_value=1500000.0,
            organization_id=econ_setup["org"].id
        )
        db.session.add(econ)
        db.session.commit()

    resp = client.get(
        f'/api/v1/economy?org_id={econ_setup["org"].id}',
        headers=econ_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["investment"] == 200000.0
