"""
Unit and Integration tests for Phase 28 Cyber Civilization Platform — Prediction Grid.
Contains 12 test cases covering prediction scenarios, simulations, scoring, and APIs.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.prediction_scenario import PredictionScenario
from app.services.prediction_grid_service import PredictionGridService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def grid_setup(app):
    """Fixture for prediction grid tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(PredictionScenario).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Grid Org", slug="grid-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="grid_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Grid Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "grid_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_prediction_scenario_creation(app, grid_setup):
    """Test 1: PredictionScenario model fields."""
    with app.app_context():
        scenario = PredictionScenario(
            scenario_name="GridStorm-Alpha",
            impact_score=0.85,
            probability=0.6,
            confidence=0.78,
            organization_id=grid_setup["org"].id
        )
        db.session.add(scenario)
        db.session.commit()
        assert scenario.id is not None
        assert scenario.scenario_name == "GridStorm-Alpha"
        assert scenario.impact_score == 0.85


def test_prediction_scenario_to_dict(app, grid_setup):
    """Test 2: PredictionScenario serialization."""
    with app.app_context():
        scenario = PredictionScenario(
            scenario_name="GridStorm-Beta",
            impact_score=0.7,
            probability=0.4,
            confidence=0.65,
            organization_id=grid_setup["org"].id
        )
        db.session.add(scenario)
        db.session.commit()
        d = scenario.to_dict()
        assert d["scenario_name"] == "GridStorm-Beta"
        assert d["impact_score"] == 0.7
        assert d["probability"] == 0.4
        assert d["confidence"] == 0.65


def test_prediction_grid_service_predict(app, grid_setup):
    """Test 3: Predict creates a new scenario for a given threat class."""
    with app.app_context():
        event = PredictionGridService.predict("ransomware", org_id=grid_setup["org"].id)
        assert event is not None
        assert "RANSOMWARE" in event.scenario_name
        assert event.organization_id == grid_setup["org"].id


def test_prediction_grid_service_predict_custom(app, grid_setup):
    """Test 4: Predict with custom threat class stores correct scenario name."""
    with app.app_context():
        event = PredictionGridService.predict("supply_chain_attack", org_id=grid_setup["org"].id)
        assert "SUPPLY_CHAIN_ATTACK" in event.scenario_name


def test_prediction_grid_service_simulate_valid(app, grid_setup):
    """Test 5: Simulate updates probabilities for an existing scenario."""
    with app.app_context():
        scenario = PredictionScenario(
            scenario_name="SimScenario",
            impact_score=0.6,
            probability=0.5,
            confidence=0.8,
            organization_id=grid_setup["org"].id
        )
        db.session.add(scenario)
        db.session.commit()

        res = PredictionGridService.simulate(scenario.id)
        assert res["simulation_run"] == "complete"
        # Probability should slightly increase (x 1.05)
        assert res["updated_probability"] == 0.525
        # Confidence should slightly decrease (x 0.98)
        assert res["updated_confidence"] == 0.784


def test_prediction_grid_service_simulate_not_found(app):
    """Test 6: Simulate returns error for non-existent scenario."""
    with app.app_context():
        res = PredictionGridService.simulate(99999)
        assert "error" in res


def test_prediction_grid_service_score_valid(app, grid_setup):
    """Test 7: Score computation for a known scenario."""
    with app.app_context():
        scenario = PredictionScenario(
            scenario_name="ScoreScenario",
            impact_score=0.8,
            probability=0.6,
            confidence=0.75,
            organization_id=grid_setup["org"].id
        )
        db.session.add(scenario)
        db.session.commit()

        score = PredictionGridService.score(scenario.id)
        # (0.8 * 0.5) + (0.6 * 0.5) = 0.4 + 0.3 = 0.7
        assert score == 0.7


def test_prediction_grid_service_score_not_found(app):
    """Test 8: Score returns 0.0 for missing scenario ID."""
    with app.app_context():
        score = PredictionGridService.score(99999)
        assert score == 0.0


def test_prediction_grid_service_score_boundaries(app, grid_setup):
    """Test 9: Score with extreme values returns values in [0.0, 1.0]."""
    with app.app_context():
        scenario = PredictionScenario(
            scenario_name="ExtremeScenario",
            impact_score=1.0,
            probability=1.0,
            confidence=1.0,
            organization_id=grid_setup["org"].id
        )
        db.session.add(scenario)
        db.session.commit()

        score = PredictionGridService.score(scenario.id)
        assert 0.0 <= score <= 1.0
        assert score == 1.0


def test_prediction_grid_simulate_probability_cap(app, grid_setup):
    """Test 10: Simulate caps probability at 1.0 even after repeated runs."""
    with app.app_context():
        scenario = PredictionScenario(
            scenario_name="CapScenario",
            impact_score=0.5,
            probability=0.98,
            confidence=0.8,
            organization_id=grid_setup["org"].id
        )
        db.session.add(scenario)
        db.session.commit()

        PredictionGridService.simulate(scenario.id)
        assert scenario.probability <= 1.0


def test_api_get_predictions(client, grid_setup):
    """Test 11: GET /api/v1/predictions returns prediction scenarios."""
    with client.application.app_context():
        scenario = PredictionScenario(
            scenario_name="API Prediction Scenario",
            impact_score=0.75,
            probability=0.55,
            confidence=0.82,
            organization_id=grid_setup["org"].id
        )
        db.session.add(scenario)
        db.session.commit()

    resp = client.get(
        f'/api/v1/predictions?org_id={grid_setup["org"].id}',
        headers=grid_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["scenario_name"] == "API Prediction Scenario"


def test_api_get_civilization_metrics(client, grid_setup):
    """Test 12: GET /api/v1/civilization/metrics REST endpoint."""
    from app.models.civilization_metric import CivilizationMetric
    with client.application.app_context():
        metric = CivilizationMetric(
            maturity=0.8,
            resilience=0.75,
            intelligence=0.9,
            innovation=0.7,
            organization_id=grid_setup["org"].id
        )
        db.session.add(metric)
        db.session.commit()

    resp = client.get(
        f'/api/v1/civilization/metrics?org_id={grid_setup["org"].id}',
        headers=grid_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["maturity"] == 0.8
