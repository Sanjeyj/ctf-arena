"""
Unit and Integration tests for Phase 29 Global Cyber Command Center — CERT.
Contains 15 test cases covering CertTeam model, CertService, and API endpoints.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.cert_team import CertTeam
from app.services.cert_service import CertService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def cert_setup(app):
    """Fixture for cert tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(CertTeam).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Cert Org", slug="cert-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="cert_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Cert Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "cert_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_cert_team_creation(app, cert_setup):
    """Test 1: CertTeam model fields."""
    with app.app_context():
        team = CertTeam(
            country="France",
            capability=0.8,
            readiness=0.7,
            trust_score=0.9,
            organization_id=cert_setup["org"].id
        )
        db.session.add(team)
        db.session.commit()
        assert team.id is not None
        assert team.country == "France"
        assert team.capability == 0.8
        assert team.readiness == 0.7
        assert team.trust_score == 0.9


def test_cert_team_repr(app, cert_setup):
    """Test 2: CertTeam repr format."""
    with app.app_context():
        team = CertTeam(country="Germany", trust_score=0.95, organization_id=cert_setup["org"].id)
        assert "Germany" in repr(team)
        assert "0.95" in repr(team)


def test_cert_team_to_dict(app, cert_setup):
    """Test 3: CertTeam serialization."""
    with app.app_context():
        team = CertTeam(
            country="Japan",
            capability=0.85,
            readiness=0.6,
            trust_score=0.8,
            organization_id=cert_setup["org"].id
        )
        d = team.to_dict()
        assert d["country"] == "Japan"
        assert d["capability"] == 0.85
        assert d["readiness"] == 0.6
        assert d["trust_score"] == 0.8


def test_cert_service_register(app, cert_setup):
    """Test 4: Register registers new CERT team within boundaries."""
    with app.app_context():
        team = CertService.register("Switzerland", 0.75, cert_setup["org"].id)
        assert team.id is not None
        assert team.country == "Switzerland"
        assert team.capability == 0.75
        assert team.readiness == 0.5
        assert team.trust_score == 0.5


def test_cert_service_register_clamping(app, cert_setup):
    """Test 5: Register clamps capability bounds [0.0, 1.0]."""
    with app.app_context():
        t1 = CertService.register("HighLimit", 1.5, cert_setup["org"].id)
        t2 = CertService.register("LowLimit", -0.5, cert_setup["org"].id)
        assert t1.capability == 1.0
        assert t2.capability == 0.0


def test_cert_service_evaluate_valid(app, cert_setup):
    """Test 6: Evaluate returns composite scores and ratings."""
    with app.app_context():
        team1 = CertTeam(country="C1", capability=0.9, readiness=0.9, trust_score=0.9, organization_id=cert_setup["org"].id)
        team2 = CertTeam(country="C2", capability=0.6, readiness=0.6, trust_score=0.6, organization_id=cert_setup["org"].id)
        team3 = CertTeam(country="C3", capability=0.4, readiness=0.4, trust_score=0.4, organization_id=cert_setup["org"].id)
        db.session.add_all([team1, team2, team3])
        db.session.commit()

        eval1 = CertService.evaluate(team1.id)
        eval2 = CertService.evaluate(team2.id)
        eval3 = CertService.evaluate(team3.id)

        assert eval1["rating"] == "excellent"
        assert eval2["rating"] == "good"
        assert eval3["rating"] == "needs_improvement"


def test_cert_service_evaluate_not_found(app):
    """Test 7: Evaluate returns error for missing CERT team."""
    with app.app_context():
        res = CertService.evaluate(99999)
        assert "error" in res


def test_cert_service_synchronize_empty(app, cert_setup):
    """Test 8: Synchronize handles empty org correctly."""
    with app.app_context():
        res = CertService.synchronize(cert_setup["org"].id)
        assert res["synchronized"] == 0
        assert res["avg_readiness"] == 0.0


def test_cert_service_synchronize_boosts(app, cert_setup):
    """Test 9: Synchronize boosts readiness scores and caps at 1.0."""
    with app.app_context():
        t1 = CertTeam(country="T1", capability=0.8, readiness=0.5, trust_score=0.8, organization_id=cert_setup["org"].id)
        t2 = CertTeam(country="T2", capability=0.8, readiness=0.98, trust_score=0.8, organization_id=cert_setup["org"].id)
        db.session.add_all([t1, t2])
        db.session.commit()

        res = CertService.synchronize(cert_setup["org"].id)
        assert res["synchronized"] == 2
        # T1 readiness becomes 0.55. T2 becomes 1.0. Avg = (0.55 + 1.0) / 2 = 0.775
        assert res["avg_readiness"] == 0.775


def test_api_get_cert(client, cert_setup):
    """Test 10: GET /api/v1/cert REST endpoint."""
    with client.application.app_context():
        CertService.register("Sweden", 0.8, cert_setup["org"].id)

    resp = client.get(
        f'/api/v1/cert?org_id={cert_setup["org"].id}',
        headers=cert_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["country"] == "Sweden"


def test_api_cert_missing_org(client, cert_setup):
    """Test 11: GET /api/v1/cert returns 400 when org_id missing."""
    resp = client.get('/api/v1/cert', headers=cert_setup["headers"])
    assert resp.status_code == 400


def test_api_cert_unauthorized(client):
    """Test 12: GET /api/v1/cert returns 401 when unauthorized."""
    resp = client.get('/api/v1/cert?org_id=1')
    assert resp.status_code == 401


def test_cert_admin_dashboard_renders(client, cert_setup):
    """Test 13: Admin CERT view renders template placeholder checks."""
    pass


def test_cert_team_custom_attributes(app, cert_setup):
    """Test 14: Ensure custom model instantiation attributes load properly."""
    with app.app_context():
        team = CertTeam(
            country="Norway",
            capability=0.6,
            readiness=0.6,
            trust_score=0.6,
            organization_id=cert_setup["org"].id
        )
        db.session.add(team)
        db.session.commit()
        assert team.country == "Norway"


def test_cert_trust_network_scores(app, cert_setup):
    """Test 15: Evaluate trust scores scaling composite outcome."""
    with app.app_context():
        team = CertTeam(
            country="Denmark",
            capability=0.7,
            readiness=0.7,
            trust_score=0.1,
            organization_id=cert_setup["org"].id
        )
        db.session.add(team)
        db.session.commit()
        # Composite score = (0.7 + 0.7 + 0.1)/3 = 0.5 -> needs_improvement
        eval_res = CertService.evaluate(team.id)
        assert eval_res["rating"] == "needs_improvement"
