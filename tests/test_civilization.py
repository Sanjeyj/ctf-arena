"""
Unit and Integration tests for Phase 28 Cyber Civilization Platform — Civilization.
Contains 12 test cases covering model creation, service evaluation, benchmarks, and API endpoints.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.cyber_nation import CyberNation
from app.models.civilization_metric import CivilizationMetric
from app.services.civilization_service import CivilizationService
from app.services.executive_civilization_ai import ExecutiveCivilizationAI
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def civ_setup(app):
    """Fixture for cyber civilization tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(CyberNation).delete()
        db.session.query(CivilizationMetric).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Civ Org", slug="civ-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="civ_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Civ Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "civ_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_cyber_nation_creation(app, civ_setup):
    """Test 1: CyberNation model fields."""
    with app.app_context():
        nation = CyberNation(
            name="AlphaNation",
            region="us-east",
            maturity_score=0.75,
            population=50000,
            status="active",
            organization_id=civ_setup["org"].id
        )
        db.session.add(nation)
        db.session.commit()
        assert nation.id is not None
        assert nation.name == "AlphaNation"
        assert nation.population == 50000


def test_cyber_nation_to_dict(app, civ_setup):
    """Test 2: CyberNation serialization."""
    with app.app_context():
        nation = CyberNation(
            name="BetaNation",
            region="eu-west",
            maturity_score=0.6,
            population=12000,
            status="offline",
            organization_id=civ_setup["org"].id
        )
        db.session.add(nation)
        db.session.commit()
        d = nation.to_dict()
        assert d["name"] == "BetaNation"
        assert d["region"] == "eu-west"
        assert d["status"] == "offline"


def test_civilization_metric_creation(app, civ_setup):
    """Test 3: CivilizationMetric model fields."""
    with app.app_context():
        metric = CivilizationMetric(
            maturity=0.7,
            resilience=0.65,
            intelligence=0.8,
            innovation=0.62,
            organization_id=civ_setup["org"].id
        )
        db.session.add(metric)
        db.session.commit()
        assert metric.id is not None
        assert metric.maturity == 0.7
        assert metric.resilience == 0.65


def test_civilization_metric_to_dict(app, civ_setup):
    """Test 4: CivilizationMetric serialization."""
    with app.app_context():
        metric = CivilizationMetric(
            maturity=0.55,
            resilience=0.6,
            intelligence=0.75,
            innovation=0.5,
            organization_id=civ_setup["org"].id
        )
        db.session.add(metric)
        db.session.commit()
        d = metric.to_dict()
        assert d["maturity"] == 0.55
        assert d["resilience"] == 0.6
        assert d["intelligence"] == 0.75


def test_civilization_service_evaluate_new(app, civ_setup):
    """Test 5: Evaluate creates metrics if not existing."""
    with app.app_context():
        metric = CivilizationService.evaluate(org_id=civ_setup["org"].id)
        assert metric is not None
        assert metric.organization_id == civ_setup["org"].id
        assert metric.maturity == 0.6


def test_civilization_service_evaluate_existing(app, civ_setup):
    """Test 6: Evaluate returns pre-existing metrics."""
    with app.app_context():
        m1 = CivilizationMetric(maturity=0.8, resilience=0.8, intelligence=0.8, innovation=0.8, organization_id=civ_setup["org"].id)
        db.session.add(m1)
        db.session.commit()

        metric = CivilizationService.evaluate(org_id=civ_setup["org"].id)
        assert metric.id == m1.id
        assert metric.maturity == 0.8


def test_civilization_service_benchmark_above_average(app, civ_setup):
    """Test 7: Benchmarking when maturity score is above average."""
    with app.app_context():
        # Baseline maturity is 0.6 (> 0.55 industry avg)
        res = CivilizationService.benchmark(org_id=civ_setup["org"].id)
        assert res["status"] == "above_average"
        assert res["variance"] > 0


def test_civilization_service_benchmark_below_average(app, civ_setup):
    """Test 8: Benchmarking when maturity score is below average."""
    with app.app_context():
        metric = CivilizationMetric(maturity=0.45, resilience=0.5, intelligence=0.5, innovation=0.5, organization_id=civ_setup["org"].id)
        db.session.add(metric)
        db.session.commit()

        res = CivilizationService.benchmark(org_id=civ_setup["org"].id)
        assert res["status"] == "below_average"
        assert res["variance"] < 0


def test_civilization_service_calculate(app, civ_setup):
    """Test 9: Computation of composite civilization index."""
    with app.app_context():
        metric = CivilizationMetric(maturity=0.6, resilience=0.7, intelligence=0.8, innovation=0.9, organization_id=civ_setup["org"].id)
        db.session.add(metric)
        db.session.commit()

        composite = CivilizationService.calculate(org_id=civ_setup["org"].id)
        assert composite == 0.75


def test_executive_ai_summarize(app, civ_setup):
    """Test 10: Executive AI summary generator output."""
    with app.app_context():
        nation = CyberNation(name="TestNation", region="us-east", maturity_score=0.8, population=1000, status="active", organization_id=civ_setup["org"].id)
        db.session.add(nation)
        db.session.commit()

        summary = ExecutiveCivilizationAI.summarize(org_id=civ_setup["org"].id)
        assert "TestNation" not in summary  # summary tracks count and metrics
        assert "1 cyber nation" in summary
        assert "maturity score" in summary


def test_executive_ai_advise_topics(app):
    """Test 11: Executive AI topic advisor suggestions."""
    a1 = ExecutiveCivilizationAI.advise("alliances")
    a2 = ExecutiveCivilizationAI.advise("economy")
    a3 = ExecutiveCivilizationAI.advise("grid")
    a4 = ExecutiveCivilizationAI.advise("unknown")

    assert "alliances" in a1.lower() or "alliance" in a1.lower()
    assert "workforce" in a2.lower() or "r&d" in a2.lower()
    assert "grid" in a3.lower() or "defense" in a3.lower()
    assert "unknown" in a4


def test_api_get_civilization(client, civ_setup):
    """Test 12: GET /api/v1/civilization returns cyber nations lists."""
    with client.application.app_context():
        nation = CyberNation(name="APINation", region="us-east", maturity_score=0.9, population=1000, status="active", organization_id=civ_setup["org"].id)
        db.session.add(nation)
        db.session.commit()

    resp = client.get(
        f'/api/v1/civilization?org_id={civ_setup["org"].id}',
        headers=civ_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["name"] == "APINation"
