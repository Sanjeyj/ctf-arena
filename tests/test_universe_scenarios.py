"""
Unit and Integration tests for Phase 30 — Universe Scenarios.
Contains 13 test cases covering UniverseScenario and UniverseSimulation model validation, wargame execution, impact calculations, and controllers suggestions.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.defense_universe import DefenseUniverse
from app.models.universe_scenario import UniverseScenario
from app.models.universe_simulation import UniverseSimulation
from app.services.universe_service import UniverseService
from app.services.scenario_engine_service import ScenarioEngineService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def scen_setup(app):
    """Fixture for scenario tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(UniverseSimulation).delete()
        db.session.query(UniverseScenario).delete()
        db.session.query(DefenseUniverse).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Scen Org", slug="scen-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        uni = UniverseService.create_universe("Scen Uni", org.id)

        try:
            UserRepository.create(
                username="scen_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Scen Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "scen_admin"}, secret)

        yield {
            "org": org,
            "uni": uni,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_universe_scenario_creation(app, scen_setup):
    """Test 1: UniverseScenario model fields."""
    with app.app_context():
        scen = UniverseScenario(
            universe_id=scen_setup["uni"].id,
            scenario_name="Ransomware Outage Event",
            scenario_type="ransomware_outage",
            severity="critical",
            probability=0.8,
            impact_score=0.9,
            organization_id=scen_setup["org"].id
        )
        db.session.add(scen)
        db.session.commit()
        assert scen.id is not None
        assert scen.scenario_name == "Ransomware Outage Event"
        assert scen.severity == "critical"


def test_universe_scenario_repr(app, scen_setup):
    """Test 2: UniverseScenario repr format."""
    with app.app_context():
        scen = UniverseScenario(
            scenario_name="Phishing Test",
            scenario_type="phish",
            organization_id=scen_setup["org"].id
        )
        assert "Phishing Test" in repr(scen)


def test_universe_scenario_to_dict(app, scen_setup):
    """Test 3: UniverseScenario serialization."""
    with app.app_context():
        scen = UniverseScenario(
            scenario_name="Ransom",
            scenario_type="ransomware_outage",
            severity="high",
            organization_id=scen_setup["org"].id
        )
        d = scen.to_dict()
        assert d["scenario_name"] == "Ransom"
        assert d["severity"] == "high"


def test_universe_simulation_creation(app, scen_setup):
    """Test 4: UniverseSimulation model fields."""
    with app.app_context():
        scen = ScenarioEngineService.create_scenario(scen_setup["uni"].id, "S1", "ransomware_outage", scen_setup["org"].id)
        sim = UniverseSimulation(
            universe_id=scen_setup["uni"].id,
            scenario_id=scen.id,
            status="running",
            initial_score=0.8,
            final_score=0.7,
            organization_id=scen_setup["org"].id
        )
        db.session.add(sim)
        db.session.commit()
        assert sim.id is not None
        assert sim.status == "running"
        assert sim.initial_score == 0.8


def test_universe_simulation_repr(app, scen_setup):
    """Test 5: UniverseSimulation repr format."""
    with app.app_context():
        sim = UniverseSimulation(status="complete", organization_id=scen_setup["org"].id)
        assert "complete" in repr(sim)


def test_universe_simulation_to_dict(app, scen_setup):
    """Test 6: UniverseSimulation serialization."""
    with app.app_context():
        sim = UniverseSimulation(status="complete", initial_score=0.8, final_score=0.6, organization_id=scen_setup["org"].id)
        d = sim.to_dict()
        assert d["status"] == "complete"
        assert d["initial_score"] == 0.8
        assert d["final_score"] == 0.6


def test_scenario_engine_create(app, scen_setup):
    """Test 7: Service create scenario creation."""
    with app.app_context():
        scen = ScenarioEngineService.create_scenario(scen_setup["uni"].id, "Engine Scen", "cloud_region_failure", scen_setup["org"].id)
        assert scen.id is not None
        assert scen.scenario_name == "Engine Scen"
        assert scen.scenario_type == "cloud_region_failure"


def test_scenario_engine_validate(app, scen_setup):
    """Test 8: Service validate scenario checks correctly."""
    with app.app_context():
        s1 = ScenarioEngineService.create_scenario(scen_setup["uni"].id, "Valid Scen", "ransomware_outage", scen_setup["org"].id)
        assert ScenarioEngineService.validate_scenario(s1.id, scen_setup["org"].id) is True
        assert ScenarioEngineService.validate_scenario(99999, scen_setup["org"].id) is False


def test_scenario_engine_simulate(app, scen_setup):
    """Test 9: Service simulate runs wargame, updating readiness scores."""
    with app.app_context():
        scen = ScenarioEngineService.create_scenario(scen_setup["uni"].id, "S1", "ransomware_outage", scen_setup["org"].id, severity="high")
        
        # Pre check
        assert scen_setup["uni"].readiness_score == 0.5
        
        sim = ScenarioEngineService.simulate(scen.id, scen_setup["org"].id)
        assert sim.status == "complete"
        # High severity drops score by 0.10 -> 0.40
        uni = db.session.get(DefenseUniverse, scen_setup["uni"].id)
        assert uni.readiness_score == 0.40


def test_scenario_engine_calculate_impact(app, scen_setup):
    """Test 10: Service calculate impact calculates correct values."""
    with app.app_context():
        scen = ScenarioEngineService.create_scenario(scen_setup["uni"].id, "Impact Scen", "ransomware_outage", scen_setup["org"].id, severity="critical")
        scen.probability = 0.8
        db.session.commit()
        # base = 0.5 + 0.4 = 0.9. Impact = 0.9 * 0.8 = 0.72
        assert ScenarioEngineService.calculate_impact(scen.id, scen_setup["org"].id) == 0.72


def test_scenario_engine_recommend_controls(app, scen_setup):
    """Test 11: Service control recommendations check."""
    with app.app_context():
        scen = ScenarioEngineService.create_scenario(scen_setup["uni"].id, "Rec Scen", "ransomware_outage", scen_setup["org"].id)
        recs = ScenarioEngineService.recommend_controls(scen.id, scen_setup["org"].id)
        assert "Deploy automated disaster recovery playbook" in recs


def test_api_get_scenarios(client, scen_setup):
    """Test 12: GET /api/v1/universe/<id>/scenarios REST endpoint."""
    with client.application.app_context():
        ScenarioEngineService.create_scenario(scen_setup["uni"].id, "API Scenario", "ransomware_outage", scen_setup["org"].id)

    resp = client.get(
        f'/api/v1/universe/{scen_setup["uni"].id}/scenarios?org_id={scen_setup["org"].id}',
        headers=scen_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["scenario_name"] == "API Scenario"


def test_api_simulate_scenario(client, scen_setup):
    """Test 13: POST /api/v1/universe/scenarios/<id>/simulate REST endpoint."""
    with client.application.app_context():
        scen = ScenarioEngineService.create_scenario(scen_setup["uni"].id, "API Sim Scen", "ransomware_outage", scen_setup["org"].id)
        scen_id = scen.id

    resp = client.post(
        f'/api/v1/universe/scenarios/{scen_id}/simulate?org_id={scen_setup["org"].id}',
        headers=scen_setup["headers"]
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["status"] == "complete"
