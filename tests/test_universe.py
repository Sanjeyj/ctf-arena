"""
Unit and Integration tests for Phase 30 — Universe.
Contains 13 test cases covering DefenseUniverse model creation, status checks, serialization, API actions, and tenant boundaries.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.defense_universe import DefenseUniverse
from app.services.universe_service import UniverseService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def uni_setup(app):
    """Fixture for universe tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(DefenseUniverse).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Uni Org", slug="uni-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="uni_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Uni Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "uni_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_universe_creation(app, uni_setup):
    """Test 1: Model creation fields."""
    with app.app_context():
        uni = DefenseUniverse(
            name="Universe Alpha",
            description="Sandbox 1",
            universe_type="sim",
            status="draft",
            organization_id=uni_setup["org"].id
        )
        db.session.add(uni)
        db.session.commit()
        assert uni.id is not None
        assert uni.name == "Universe Alpha"
        assert uni.status == "draft"


def test_universe_repr(app, uni_setup):
    """Test 2: __repr__ format check."""
    with app.app_context():
        uni = DefenseUniverse(name="Universe Beta", status="active", organization_id=uni_setup["org"].id)
        assert "Universe Beta" in repr(uni)
        assert "active" in repr(uni)


def test_universe_to_dict(app, uni_setup):
    """Test 3: Model to dict serialization."""
    with app.app_context():
        uni = DefenseUniverse(
            name="Universe Gamma",
            universe_type="test",
            status="paused",
            organization_id=uni_setup["org"].id
        )
        d = uni.to_dict()
        assert d["name"] == "Universe Gamma"
        assert d["universe_type"] == "test"
        assert d["status"] == "paused"


def test_create_universe_service(app, uni_setup):
    """Test 4: Service layer creation defaults."""
    with app.app_context():
        uni = UniverseService.create_universe("Uni Service", uni_setup["org"].id, "Desc")
        assert uni.id is not None
        assert uni.status == "draft"
        assert uni.readiness_score == 0.5


def test_universe_service_activate(app, uni_setup):
    """Test 5: Service activate updates status."""
    with app.app_context():
        uni = UniverseService.create_universe("Uni Act", uni_setup["org"].id)
        activated = UniverseService.activate(uni.id, uni_setup["org"].id)
        assert activated.status == "active"


def test_universe_service_activate_unauthorized(app, uni_setup):
    """Test 6: Service activate enforces tenant scoping check."""
    with app.app_context():
        uni = UniverseService.create_universe("Uni Scope", uni_setup["org"].id)
        res = UniverseService.activate(uni.id, 99999)
        assert res is None


def test_universe_service_pause(app, uni_setup):
    """Test 7: Service pause updates status."""
    with app.app_context():
        uni = UniverseService.create_universe("Uni Pause", uni_setup["org"].id)
        paused = UniverseService.pause(uni.id, uni_setup["org"].id)
        assert paused.status == "paused"


def test_universe_service_complete(app, uni_setup):
    """Test 8: Service complete updates status."""
    with app.app_context():
        uni = UniverseService.create_universe("Uni Comp", uni_setup["org"].id)
        comp = UniverseService.complete(uni.id, uni_setup["org"].id)
        assert comp.status == "completed"


def test_universe_service_posture(app, uni_setup):
    """Test 9: Service posture dictionary summary check."""
    with app.app_context():
        uni = UniverseService.create_universe("Uni Posture", uni_setup["org"].id)
        posture = UniverseService.get_posture(uni.id, uni_setup["org"].id)
        assert posture["readiness_score"] == 0.5
        assert posture["status"] == "draft"


def test_universe_service_calculate_readiness_no_domains(app, uni_setup):
    """Test 10: Service calculate readiness returns default score when no domains exist."""
    with app.app_context():
        uni = UniverseService.create_universe("Uni Calc Empty", uni_setup["org"].id)
        score = UniverseService.calculate_readiness(uni.id, uni_setup["org"].id)
        assert score == 0.5


def test_api_get_universes(client, uni_setup):
    """Test 11: GET /api/v1/universe endpoint."""
    with client.application.app_context():
        UniverseService.create_universe("API Uni", uni_setup["org"].id)

    resp = client.get(
        f'/api/v1/universe?org_id={uni_setup["org"].id}',
        headers=uni_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["name"] == "API Uni"


def test_api_create_universe(client, uni_setup):
    """Test 12: POST /api/v1/universe endpoint."""
    resp = client.post(
        f'/api/v1/universe?org_id={uni_setup["org"].id}',
        json={'name': 'POST Uni'},
        headers=uni_setup["headers"]
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["name"] == "POST Uni"


def test_api_get_universe_detail(client, uni_setup):
    """Test 13: GET /api/v1/universe/<id> endpoint."""
    with client.application.app_context():
        uni = UniverseService.create_universe("API Detail", uni_setup["org"].id)
        uni_id = uni.id

    resp = client.get(
        f'/api/v1/universe/{uni_id}?org_id={uni_setup["org"].id}',
        headers=uni_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["name"] == "API Detail"
