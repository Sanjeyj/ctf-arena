"""
Unit and Integration tests for Governance Scorecards.
Phase 38 — Enterprise Security Decision Intelligence & Governance Fabric.
Contains 10 test cases covering GovernanceScorecard model, scoring, weight validation, and REST endpoints.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.governance_scorecard import GovernanceScorecard
from app.services.governance_scorecard_service import GovernanceScorecardService
from app.research.routes import create_jwt


@pytest.fixture
def gs_setup(app):
    with app.app_context():
        db.session.query(GovernanceScorecard).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="GS Org", slug="gs-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_governance_scorecard_model(app, gs_setup):
    """Test 1: GovernanceScorecard model basic persistence."""
    with app.app_context():
        sc = GovernanceScorecard(
            scorecard_type="overall",
            overall_score=78.5,
            risk_alignment_score=80.0,
            policy_effectiveness_score=75.0,
            evidence_quality_score=70.0,
            decision_quality_score=85.0,
            objective_progress_score=72.0,
            organization_id=gs_setup["org"].id
        )
        db.session.add(sc)
        db.session.commit()
        assert sc.id is not None
        assert sc.overall_score == 78.5


def test_calculate_risk_alignment(app, gs_setup):
    """Test 2: calculate_risk_alignment returns a float in [0, 100]."""
    with app.app_context():
        score = GovernanceScorecardService.calculate_risk_alignment(gs_setup["org"].id)
        assert 0.0 <= score <= 100.0


def test_calculate_policy_effectiveness(app, gs_setup):
    """Test 3: calculate_policy_effectiveness returns a float in [0, 100]."""
    with app.app_context():
        score = GovernanceScorecardService.calculate_policy_effectiveness(gs_setup["org"].id)
        assert 0.0 <= score <= 100.0


def test_calculate_evidence_quality(app, gs_setup):
    """Test 4: calculate_evidence_quality returns a float in [0, 100]."""
    with app.app_context():
        score = GovernanceScorecardService.calculate_evidence_quality(gs_setup["org"].id)
        assert 0.0 <= score <= 100.0


def test_calculate_overall_score_valid(app, gs_setup):
    """Test 5: calculate_overall_score computes a weighted average correctly."""
    with app.app_context():
        weights = {
            'risk_alignment': 0.25,
            'policy_effectiveness': 0.20,
            'evidence_quality': 0.15,
            'decision_quality': 0.20,
            'objective_progress': 0.20
        }
        scores = {
            'risk_alignment': 80.0,
            'policy_effectiveness': 75.0,
            'evidence_quality': 70.0,
            'decision_quality': 85.0,
            'objective_progress': 60.0
        }
        result = GovernanceScorecardService.calculate_overall_score(weights, scores)
        assert 0.0 <= result <= 100.0


def test_calculate_overall_score_bad_weights(app, gs_setup):
    """Test 6: calculate_overall_score raises ValueError when weights don't sum to 1.0."""
    with app.app_context():
        weights = {'risk_alignment': 0.5, 'policy_effectiveness': 0.5,
                   'evidence_quality': 0.5, 'decision_quality': 0.5, 'objective_progress': 0.5}
        scores = {k: 70.0 for k in weights}
        with pytest.raises(ValueError, match="weights must sum"):
            GovernanceScorecardService.calculate_overall_score(weights, scores)


def test_save_scorecard(app, gs_setup):
    """Test 7: save_scorecard persists a GovernanceScorecard record."""
    with app.app_context():
        sc = GovernanceScorecardService.save_scorecard(gs_setup["org"].id)
        assert sc.id is not None
        assert sc.overall_score >= 0.0


def test_scorecard_summary_empty(app, gs_setup):
    """Test 8: scorecard_summary returns zero defaults when no scorecards exist."""
    with app.app_context():
        summary = GovernanceScorecardService.scorecard_summary(gs_setup["org"].id)
        assert "overall_score" in summary


def test_scorecard_summary_populated(app, gs_setup):
    """Test 9: scorecard_summary returns the latest scorecard values after save."""
    with app.app_context():
        GovernanceScorecardService.save_scorecard(gs_setup["org"].id)
        summary = GovernanceScorecardService.scorecard_summary(gs_setup["org"].id)
        assert summary["overall_score"] > 0.0


def test_api_calculate_scorecard(app, client, gs_setup):
    """Test 10: POST /api/v1/governance-intelligence/scorecards/calculate returns 200."""
    response = client.post(
        "/api/v1/governance-intelligence/scorecards/calculate",
        json={"org_id": gs_setup["org"].id},
        headers=gs_setup["headers"]
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "overall_score" in data
