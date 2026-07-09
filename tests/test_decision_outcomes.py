"""
Unit and Integration tests for Decision Outcomes.
Phase 38 — Enterprise Security Decision Intelligence & Governance Fabric.
Contains 10 test cases covering DecisionOutcome model, effectiveness evaluation, variance, and REST endpoints.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.decision_context import DecisionContext
from app.models.decision_recommendation import DecisionRecommendation
from app.models.decision_outcome import DecisionOutcome
from app.models.strategic_decision_record import StrategicDecisionRecord
from app.services.decision_intelligence_service import DecisionIntelligenceService
from app.services.decision_outcome_service import DecisionOutcomeService
from app.research.routes import create_jwt


@pytest.fixture
def do_setup(app):
    with app.app_context():
        db.session.query(DecisionOutcome).delete()
        db.session.query(DecisionRecommendation).delete()
        db.session.query(DecisionContext).delete()
        db.session.query(StrategicDecisionRecord).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="DO Org", slug="do-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        ctx = DecisionIntelligenceService.create_context("Ctx", "risk", "US", org.id)
        rec = DecisionIntelligenceService.generate_recommendation(
            ctx.id, "patch", "Fix Auth", "desc", 30.0, 20.0, 25.0, 10000.0, 85.0, org.id
        )
        dec = StrategicDecisionRecord(
            title="Approve Auth Fix",
            decision_type="budget_allocation",
            decision_context="Security improvement",
            approval_status="approved",
            organization_id=org.id
        )
        db.session.add(dec)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "org": org,
            "rec": rec,
            "dec": dec,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_decision_outcome_model(app, do_setup):
    """Test 1: DecisionOutcome model basic persistence."""
    with app.app_context():
        outcome = DecisionOutcome(
            recommendation_id=do_setup["rec"].id,
            decision_record_id=do_setup["dec"].id,
            baseline_metric=50.0,
            result_metric=65.0,
            improvement_delta=15.0,
            expected_improvement=20.0,
            variance=-5.0,
            outcome_status="partially_effective",
            organization_id=do_setup["org"].id
        )
        db.session.add(outcome)
        db.session.commit()
        assert outcome.id is not None
        assert outcome.outcome_status == "partially_effective"


def test_record_outcome_effective(app, do_setup):
    """Test 2: record_outcome creates an 'effective' outcome when delta >= expected."""
    with app.app_context():
        outcome = DecisionOutcomeService.record_outcome(
            do_setup["rec"].id, do_setup["dec"].id,
            50.0, 80.0, 25.0, do_setup["org"].id
        )
        assert outcome.id is not None
        assert outcome.outcome_status == "effective"


def test_record_outcome_partially_effective(app, do_setup):
    """Test 3: record_outcome creates 'partially_effective' when 0 < delta < expected."""
    with app.app_context():
        ctx = DecisionIntelligenceService.create_context("C2", "risk", "EU", do_setup["org"].id)
        rec2 = DecisionIntelligenceService.generate_recommendation(
            ctx.id, "patch", "Minor fix", "d", 20.0, 10.0, 10.0, 5000.0, 80.0, do_setup["org"].id
        )
        outcome = DecisionOutcomeService.record_outcome(
            rec2.id, do_setup["dec"].id,
            50.0, 60.0, 20.0, do_setup["org"].id
        )
        assert outcome.outcome_status == "partially_effective"


def test_record_outcome_regressed(app, do_setup):
    """Test 4: record_outcome creates 'regressed' when delta drops significantly."""
    with app.app_context():
        ctx = DecisionIntelligenceService.create_context("C3", "risk", "APAC", do_setup["org"].id)
        rec3 = DecisionIntelligenceService.generate_recommendation(
            ctx.id, "patch", "Bad patch", "d", 10.0, 5.0, 5.0, 2000.0, 60.0, do_setup["org"].id
        )
        outcome = DecisionOutcomeService.record_outcome(
            rec3.id, do_setup["dec"].id,
            50.0, 40.0, 15.0, do_setup["org"].id
        )
        assert outcome.outcome_status == "regressed"


def test_calculate_variance(app, do_setup):
    """Test 5: calculate_variance returns the correct signed variance."""
    with app.app_context():
        outcome = DecisionOutcomeService.record_outcome(
            do_setup["rec"].id, do_setup["dec"].id,
            50.0, 70.0, 30.0, do_setup["org"].id
        )
        variance = DecisionOutcomeService.calculate_variance(outcome.id, do_setup["org"].id)
        # delta = 20.0, expected = 30.0 → variance = -10.0
        assert variance == pytest.approx(-10.0, abs=0.1)


def test_evaluate_effectiveness(app, do_setup):
    """Test 6: evaluate_effectiveness returns status string."""
    with app.app_context():
        outcome = DecisionOutcomeService.record_outcome(
            do_setup["rec"].id, do_setup["dec"].id,
            50.0, 90.0, 25.0, do_setup["org"].id
        )
        status = DecisionOutcomeService.evaluate_effectiveness(outcome.id, do_setup["org"].id)
        assert status in ("effective", "partially_effective", "ineffective", "regressed", "pending")


def test_compare_expected_actual(app, do_setup):
    """Test 7: compare_expected_actual returns expected/actual/variance dict."""
    with app.app_context():
        outcome = DecisionOutcomeService.record_outcome(
            do_setup["rec"].id, do_setup["dec"].id,
            60.0, 80.0, 25.0, do_setup["org"].id
        )
        comparison = DecisionOutcomeService.compare_expected_actual(outcome.id, do_setup["org"].id)
        assert "expected" in comparison
        assert "actual" in comparison
        assert "variance" in comparison


def test_detect_negative_outcome(app, do_setup):
    """Test 8: detect_negative_outcome returns True for regressed outcomes."""
    with app.app_context():
        ctx = DecisionIntelligenceService.create_context("C4", "trust", "US", do_setup["org"].id)
        rec4 = DecisionIntelligenceService.generate_recommendation(
            ctx.id, "patch", "Reg patch", "d", 5.0, 5.0, 5.0, 500.0, 50.0, do_setup["org"].id
        )
        outcome = DecisionOutcomeService.record_outcome(
            rec4.id, do_setup["dec"].id,
            50.0, 35.0, 10.0, do_setup["org"].id
        )
        assert DecisionOutcomeService.detect_negative_outcome(outcome.id, do_setup["org"].id) is True


def test_outcome_summary(app, do_setup):
    """Test 9: outcome_summary returns total, effective, and negative counts."""
    with app.app_context():
        DecisionOutcomeService.record_outcome(
            do_setup["rec"].id, do_setup["dec"].id,
            50.0, 80.0, 25.0, do_setup["org"].id
        )
        summary = DecisionOutcomeService.outcome_summary(do_setup["org"].id)
        assert "total_outcomes" in summary
        assert "effective_outcomes" in summary
        assert "negative_outcomes" in summary


def test_api_get_outcomes(app, client, do_setup):
    """Test 10: GET /api/v1/governance-intelligence/outcomes returns 200."""
    response = client.get(
        f"/api/v1/governance-intelligence/outcomes?org_id={do_setup['org'].id}",
        headers=do_setup["headers"]
    )
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
