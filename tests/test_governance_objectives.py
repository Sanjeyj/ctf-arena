"""
Unit and Integration tests for Governance Objectives.
Phase 38 — Enterprise Security Decision Intelligence & Governance Fabric.
Contains 10 test cases covering GovernanceObjective model, service, progress tracking, and REST endpoints.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.governance_objective import GovernanceObjective
from app.services.governance_objective_service import GovernanceObjectiveService
from app.research.routes import create_jwt


@pytest.fixture
def go_setup(app):
    with app.app_context():
        db.session.query(GovernanceObjective).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="GO Org", slug="go-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_governance_objective_model(app, go_setup):
    """Test 1: GovernanceObjective model basic persistence."""
    with app.app_context():
        obj = GovernanceObjective(
            title="Reduce Residual Risk to <30",
            objective_type="risk_reduction",
            target_score=90.0,
            current_score=40.0,
            weight=0.3,
            status="active",
            organization_id=go_setup["org"].id
        )
        db.session.add(obj)
        db.session.commit()
        assert obj.id is not None
        assert obj.target_score == 90.0


def test_create_objective_service(app, go_setup):
    """Test 2: GovernanceObjectiveService.create_objective creates a valid objective."""
    with app.app_context():
        obj = GovernanceObjectiveService.create_objective(
            "Achieve Full Compliance", "compliance", "Achieve all controls",
            85.0, 0.25, "2026-12-31", "CISO", go_setup["org"].id
        )
        assert obj.id is not None
        assert obj.status == "proposed"
        assert obj.objective_type == "compliance"


def test_create_objective_invalid_type(app, go_setup):
    """Test 3: create_objective raises ValueError for invalid types."""
    with app.app_context():
        with pytest.raises(ValueError, match="Invalid objective type"):
            GovernanceObjectiveService.create_objective(
                "Bad Obj", "alien_type", "desc", 80.0, 0.2, None, None, go_setup["org"].id
            )


def test_create_objective_invalid_weight(app, go_setup):
    """Test 4: create_objective raises ValueError for weight out of [0,1]."""
    with app.app_context():
        with pytest.raises(ValueError, match="Weight must be between"):
            GovernanceObjectiveService.create_objective(
                "Heavy Obj", "resilience", "desc", 80.0, 1.5, None, None, go_setup["org"].id
            )


def test_calculate_progress(app, go_setup):
    """Test 5: calculate_progress returns a float between 0 and 100."""
    with app.app_context():
        obj = GovernanceObjectiveService.create_objective(
            "Progress Test", "reliability", "Desc", 80.0, 0.2, None, None, go_setup["org"].id
        )
        progress = GovernanceObjectiveService.calculate_progress(obj.id, go_setup["org"].id)
        assert 0.0 <= progress <= 100.0


def test_evaluate_target_achieved(app, go_setup):
    """Test 6: evaluate_target marks objective as 'achieved' when score meets target."""
    with app.app_context():
        obj = GovernanceObjectiveService.create_objective(
            "Low Bar", "exposure_reduction", "Easy objective", 50.0, 0.1, None, None, go_setup["org"].id
        )
        result = GovernanceObjectiveService.evaluate_target(obj.id, 75.0, go_setup["org"].id)
        assert result is True
        refreshed = GovernanceObjective.query.get(obj.id)
        assert refreshed.status == "achieved"


def test_evaluate_target_not_achieved(app, go_setup):
    """Test 7: evaluate_target keeps objective 'active' when score is below target."""
    with app.app_context():
        obj = GovernanceObjectiveService.create_objective(
            "High Bar", "investment_efficiency", "Hard objective", 95.0, 0.2, None, None, go_setup["org"].id
        )
        result = GovernanceObjectiveService.evaluate_target(obj.id, 60.0, go_setup["org"].id)
        assert result is False


def test_rank_objectives(app, go_setup):
    """Test 8: rank_objectives returns objectives sorted by weight descending."""
    with app.app_context():
        GovernanceObjectiveService.create_objective("Low Weight", "resilience", "d", 80.0, 0.1, None, None, go_setup["org"].id)
        GovernanceObjectiveService.create_objective("High Weight", "compliance", "d", 80.0, 0.5, None, None, go_setup["org"].id)
        ranked = GovernanceObjectiveService.rank_objectives(go_setup["org"].id)
        assert ranked[0].weight >= ranked[-1].weight


def test_detect_stalled_objectives(app, go_setup):
    """Test 9: detect_stalled_objectives returns objectives with low progress."""
    with app.app_context():
        GovernanceObjectiveService.create_objective("Stalled Obj", "risk_reduction", "d", 90.0, 0.3, None, None, go_setup["org"].id)
        stalled = GovernanceObjectiveService.detect_stalled_objectives(go_setup["org"].id)
        assert isinstance(stalled, list)


def test_api_get_objectives(app, client, go_setup):
    """Test 10: GET /api/v1/governance-intelligence/objectives returns 200."""
    response = client.get(
        f"/api/v1/governance-intelligence/objectives?org_id={go_setup['org'].id}",
        headers=go_setup["headers"]
    )
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
