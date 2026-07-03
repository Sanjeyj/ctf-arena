"""
Unit and Integration tests for Phase 28 Cyber Civilization Platform — Alliances.
Contains 12 test cases covering defense alliances, status validations, sync services, and APIs.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.defense_alliance import DefenseAlliance
from app.models.defense_grid import DefenseGrid
from app.services.alliance_service import AllianceService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def alliance_setup(app):
    """Fixture for defense alliance tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(DefenseAlliance).delete()
        db.session.query(DefenseGrid).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Alliance Org", slug="alliance-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="alliance_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Alliance Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "alliance_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_defense_alliance_creation(app, alliance_setup):
    """Test 1: DefenseAlliance model fields."""
    with app.app_context():
        alliance = DefenseAlliance(
            alliance_name="Global Shield",
            trust_score=0.85,
            members="NationA, NationB",
            status="active",
            organization_id=alliance_setup["org"].id
        )
        db.session.add(alliance)
        db.session.commit()
        assert alliance.id is not None
        assert alliance.alliance_name == "Global Shield"
        assert alliance.trust_score == 0.85


def test_defense_alliance_to_dict(app, alliance_setup):
    """Test 2: DefenseAlliance serialization."""
    with app.app_context():
        alliance = DefenseAlliance(
            alliance_name="APAC Coalition",
            trust_score=0.72,
            members="NationC, NationD",
            status="suspended",
            organization_id=alliance_setup["org"].id
        )
        db.session.add(alliance)
        db.session.commit()
        d = alliance.to_dict()
        assert d["alliance_name"] == "APAC Coalition"
        assert d["trust_score"] == 0.72
        assert d["status"] == "suspended"


def test_defense_grid_creation(app, alliance_setup):
    """Test 3: DefenseGrid model fields."""
    with app.app_context():
        grid = DefenseGrid(
            name="Zone-US-East",
            coverage=0.9,
            health=0.95,
            readiness=0.88,
            organization_id=alliance_setup["org"].id
        )
        db.session.add(grid)
        db.session.commit()
        assert grid.id is not None
        assert grid.name == "Zone-US-East"
        assert grid.coverage == 0.9
        assert grid.health == 0.95


def test_defense_grid_to_dict(app, alliance_setup):
    """Test 4: DefenseGrid serialization."""
    with app.app_context():
        grid = DefenseGrid(
            name="Zone-EU-West",
            coverage=0.75,
            health=0.6,
            readiness=0.7,
            organization_id=alliance_setup["org"].id
        )
        db.session.add(grid)
        db.session.commit()
        d = grid.to_dict()
        assert d["name"] == "Zone-EU-West"
        assert d["coverage"] == 0.75
        assert d["health"] == 0.6


def test_alliance_service_create(app, alliance_setup):
    """Test 5: Create alliance successfully sets members list."""
    with app.app_context():
        alliance = AllianceService.create("NATO-Sim", ["NationA", "NationB"], org_id=alliance_setup["org"].id)
        assert alliance.id is not None
        assert alliance.alliance_name == "NATO-Sim"
        assert alliance.members == "NationA,NationB"


def test_alliance_service_validate_valid(app, alliance_setup):
    """Test 6: Valid active alliance passes configuration validations."""
    with app.app_context():
        alliance = DefenseAlliance(
            alliance_name="Active League",
            members="NationA, NationB, NationC",
            trust_score=0.75,
            status="active",
            organization_id=alliance_setup["org"].id
        )
        db.session.add(alliance)
        db.session.commit()

        res = AllianceService.validate(alliance.id)
        assert res["valid"] is True
        assert res["member_count"] == 3


def test_alliance_service_validate_invalid_status(app, alliance_setup):
    """Test 7: Suspended/disbanded alliance fails validations."""
    with app.app_context():
        alliance = DefenseAlliance(
            alliance_name="Disbanded League",
            members="NationA, NationB",
            trust_score=0.5,
            status="disbanded",
            organization_id=alliance_setup["org"].id
        )
        db.session.add(alliance)
        db.session.commit()

        res = AllianceService.validate(alliance.id)
        assert res["valid"] is False


def test_alliance_service_validate_insufficient_members(app, alliance_setup):
    """Test 8: Alliance with less than 2 members fails validations."""
    with app.app_context():
        alliance = DefenseAlliance(
            alliance_name="Lonely League",
            members="NationA",
            trust_score=0.6,
            status="active",
            organization_id=alliance_setup["org"].id
        )
        db.session.add(alliance)
        db.session.commit()

        res = AllianceService.validate(alliance.id)
        assert res["valid"] is False


def test_alliance_service_validate_not_found(app):
    """Test 9: Validate returns error code on missing alliance ID."""
    with app.app_context():
        res = AllianceService.validate(99999)
        assert res["valid"] is False
        assert "not found" in res["reason"]


def test_alliance_service_synchronize_operational(app, alliance_setup):
    """Test 10: Synchronize shows operational status for healthy grids."""
    with app.app_context():
        AllianceService.create("Shield-Alliance", ["A", "B"], org_id=alliance_setup["org"].id)
        g1 = DefenseGrid(name="G1", coverage=0.8, health=0.9, readiness=0.8, organization_id=alliance_setup["org"].id)
        g2 = DefenseGrid(name="G2", coverage=0.7, health=0.85, readiness=0.8, organization_id=alliance_setup["org"].id)
        db.session.add_all([g1, g2])
        db.session.commit()

        res = AllianceService.synchronize(org_id=alliance_setup["org"].id)
        assert res["alliances_synced"] == 1
        assert res["total_defense_grids"] == 2
        assert res["synchronized_percentage"] == 100.0
        assert res["status"] == "operational"


def test_alliance_service_synchronize_degraded(app, alliance_setup):
    """Test 11: Synchronize status is degraded when health index drops."""
    with app.app_context():
        AllianceService.create("Shield-Alliance", ["A", "B"], org_id=alliance_setup["org"].id)
        g1 = DefenseGrid(name="G1", coverage=0.8, health=0.9, readiness=0.8, organization_id=alliance_setup["org"].id)
        g2 = DefenseGrid(name="G2", coverage=0.7, health=0.4, readiness=0.5, organization_id=alliance_setup["org"].id)
        db.session.add_all([g1, g2])
        db.session.commit()

        res = AllianceService.synchronize(org_id=alliance_setup["org"].id)
        assert res["synchronized_percentage"] == 50.0
        assert res["status"] == "degraded"


def test_api_get_alliances(client, alliance_setup):
    """Test 12: GET /api/v1/alliances REST endpoint."""
    with client.application.app_context():
        AllianceService.create("Alliance API", ["N1", "N2"], org_id=alliance_setup["org"].id)

    resp = client.get(
        f'/api/v1/alliances?org_id={alliance_setup["org"].id}',
        headers=alliance_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["alliance_name"] == "Alliance API"
