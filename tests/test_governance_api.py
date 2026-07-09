"""
Unit and Integration tests for Governance Scorecard REST API and Admin Endpoints.
Phase 38 — Enterprise Security Decision Intelligence & Governance Fabric.
Contains 10 test cases covering all REST and admin route paths of the governance_intelligence blueprint.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.control_policy import ControlPolicy
from app.models.governance_objective import GovernanceObjective
from app.models.governance_scorecard import GovernanceScorecard
from app.models.governance_drift_record import GovernanceDriftRecord
from app.research.routes import create_jwt


@pytest.fixture
def api_setup(app):
    with app.app_context():
        db.session.query(GovernanceDriftRecord).delete()
        db.session.query(GovernanceScorecard).delete()
        db.session.query(GovernanceObjective).delete()
        db.session.query(ControlPolicy).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="API Org", slug="api-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_get_contexts_returns_list(app, client, api_setup):
    """Test 1: GET /api/v1/governance-intelligence/contexts returns a list."""
    r = client.get(
        f"/api/v1/governance-intelligence/contexts?org_id={api_setup['org'].id}",
        headers=api_setup["headers"]
    )
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_create_context_via_api(app, client, api_setup):
    """Test 2: POST /api/v1/governance-intelligence/contexts creates a context."""
    r = client.post(
        "/api/v1/governance-intelligence/contexts",
        json={"org_id": api_setup["org"].id, "name": "API Ctx", "context_type": "risk", "business_scope": "global"},
        headers=api_setup["headers"]
    )
    assert r.status_code == 201
    data = r.get_json()
    assert data["name"] == "API Ctx"


def test_create_context_missing_fields(app, client, api_setup):
    """Test 3: POST /api/v1/governance-intelligence/contexts returns 400 on missing fields."""
    r = client.post(
        "/api/v1/governance-intelligence/contexts",
        json={"org_id": api_setup["org"].id},
        headers=api_setup["headers"]
    )
    assert r.status_code == 400


def test_get_recommendations_returns_list(app, client, api_setup):
    """Test 4: GET /api/v1/governance-intelligence/recommendations returns a list."""
    r = client.get(
        f"/api/v1/governance-intelligence/recommendations?org_id={api_setup['org'].id}",
        headers=api_setup["headers"]
    )
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_get_policy_optimizations_list(app, client, api_setup):
    """Test 5: GET /api/v1/governance-intelligence/policy-optimizations returns a list."""
    r = client.get(
        f"/api/v1/governance-intelligence/policy-optimizations?org_id={api_setup['org'].id}",
        headers=api_setup["headers"]
    )
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_get_conflicts_returns_list(app, client, api_setup):
    """Test 6: GET /api/v1/governance-intelligence/conflicts returns a list."""
    r = client.get(
        f"/api/v1/governance-intelligence/conflicts?org_id={api_setup['org'].id}",
        headers=api_setup["headers"]
    )
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_create_objective_via_api(app, client, api_setup):
    """Test 7: POST /api/v1/governance-intelligence/objectives creates an objective."""
    r = client.post(
        "/api/v1/governance-intelligence/objectives",
        json={
            "org_id": api_setup["org"].id,
            "title": "Reduce Risk 20%",
            "objective_type": "risk_reduction",
            "target_score": 80.0,
            "weight": 0.25
        },
        headers=api_setup["headers"]
    )
    assert r.status_code == 201
    data = r.get_json()
    assert data["title"] == "Reduce Risk 20%"


def test_get_scorecards_list(app, client, api_setup):
    """Test 8: GET /api/v1/governance-intelligence/scorecards returns a list."""
    r = client.get(
        f"/api/v1/governance-intelligence/scorecards?org_id={api_setup['org'].id}",
        headers=api_setup["headers"]
    )
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_get_drift_returns_list(app, client, api_setup):
    """Test 9: GET /api/v1/governance-intelligence/drift returns a list."""
    r = client.get(
        f"/api/v1/governance-intelligence/drift?org_id={api_setup['org'].id}",
        headers=api_setup["headers"]
    )
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_get_brief_returns_text(app, client, api_setup):
    """Test 10: GET /api/v1/governance-intelligence/brief returns a brief string."""
    r = client.get(
        f"/api/v1/governance-intelligence/brief?org_id={api_setup['org'].id}",
        headers=api_setup["headers"]
    )
    assert r.status_code == 200
    data = r.get_json()
    assert "brief" in data
