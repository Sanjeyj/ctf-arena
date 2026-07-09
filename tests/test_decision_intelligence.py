"""
Unit and Integration tests for Decision Intelligence Contexts.
Phase 38 — Enterprise Security Decision Intelligence.
Contains 10 test cases covering DecisionContext model, service creation, signal collection, ranking, and REST endpoints.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.decision_context import DecisionContext
from app.models.decision_recommendation import DecisionRecommendation
from app.services.decision_intelligence_service import DecisionIntelligenceService
from app.research.routes import create_jwt


@pytest.fixture
def di_setup(app):
    with app.app_context():
        db.session.query(DecisionRecommendation).delete()
        db.session.query(DecisionContext).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="DI Org", slug="di-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_decision_context_model(app, di_setup):
    """Test 1: DecisionContext model basic persistence."""
    with app.app_context():
        ctx = DecisionContext(
            name="Risk Assessment Q3",
            context_type="risk",
            business_scope="global",
            risk_score=72.0,
            resilience_score=55.0,
            control_effectiveness_score=68.0,
            evidence_confidence_score=80.0,
            urgency_score=65.0,
            status="active",
            organization_id=di_setup["org"].id
        )
        db.session.add(ctx)
        db.session.commit()
        assert ctx.id is not None
        assert ctx.risk_score == 72.0


def test_create_context_service(app, di_setup):
    """Test 2: DecisionIntelligenceService.create_context creates a valid context."""
    with app.app_context():
        ctx = DecisionIntelligenceService.create_context(
            "Resilience Focus", "resilience", "EMEA", di_setup["org"].id
        )
        assert ctx.id is not None
        assert ctx.context_type == "resilience"
        assert ctx.status == "active"


def test_create_context_invalid_type(app, di_setup):
    """Test 3: create_context raises ValueError for unknown context types."""
    with app.app_context():
        with pytest.raises(ValueError, match="Invalid context type"):
            DecisionIntelligenceService.create_context(
                "Bad Type", "magic", "scope", di_setup["org"].id
            )


def test_collect_context_signals(app, di_setup):
    """Test 4: collect_context_signals returns all required score keys."""
    with app.app_context():
        signals = DecisionIntelligenceService.collect_context_signals("risk", di_setup["org"].id)
        assert "risk_score" in signals
        assert "resilience_score" in signals
        assert "control_effectiveness_score" in signals
        assert "evidence_confidence_score" in signals
        assert "urgency_score" in signals


def test_normalize_context(app, di_setup):
    """Test 5: normalize_context clamps scores within [0, 100]."""
    with app.app_context():
        ctx = DecisionContext(
            name="Norm Test",
            context_type="risk",
            risk_score=150.0,
            resilience_score=-20.0,
            control_effectiveness_score=50.0,
            evidence_confidence_score=80.0,
            urgency_score=200.0,
            status="active",
            organization_id=di_setup["org"].id
        )
        db.session.add(ctx)
        db.session.commit()

        result = DecisionIntelligenceService.normalize_context(ctx.id, di_setup["org"].id)
        assert result.risk_score <= 100.0
        assert result.resilience_score >= 0.0
        assert result.urgency_score <= 100.0


def test_generate_recommendation(app, di_setup):
    """Test 6: generate_recommendation creates a prioritized recommendation."""
    with app.app_context():
        ctx = DecisionIntelligenceService.create_context(
            "Compliance Ctx", "compliance", "APAC", di_setup["org"].id
        )
        rec = DecisionIntelligenceService.generate_recommendation(
            ctx.id, "control_enhancement", "Harden MFA", "Deploy phishing-resistant MFA",
            30.0, 15.0, 20.0, 50000.0, 90.0, di_setup["org"].id
        )
        assert rec.id is not None
        assert rec.priority_score > 0.0
        assert rec.status == "generated"


def test_recommendation_invalid_scores(app, di_setup):
    """Test 7: generate_recommendation raises ValueError for out-of-range scores."""
    with app.app_context():
        ctx = DecisionIntelligenceService.create_context(
            "Ops Ctx", "operations", "US", di_setup["org"].id
        )
        with pytest.raises(ValueError):
            DecisionIntelligenceService.generate_recommendation(
                ctx.id, "policy", "Bad Score Rec", "desc",
                150.0, 0.0, 0.0, 1000.0, 80.0, di_setup["org"].id
            )


def test_rank_recommendations(app, di_setup):
    """Test 8: rank_recommendations returns items sorted by priority_score descending."""
    with app.app_context():
        ctx = DecisionIntelligenceService.create_context(
            "Rank Test", "investment", "Global", di_setup["org"].id
        )
        DecisionIntelligenceService.generate_recommendation(
            ctx.id, "patch", "Low Priority", "desc", 10.0, 5.0, 5.0, 1000.0, 70.0, di_setup["org"].id
        )
        DecisionIntelligenceService.generate_recommendation(
            ctx.id, "patch", "High Priority", "desc", 50.0, 40.0, 40.0, 5000.0, 90.0, di_setup["org"].id
        )
        ranked = DecisionIntelligenceService.rank_recommendations(ctx.id, di_setup["org"].id)
        assert ranked[0].priority_score >= ranked[-1].priority_score


def test_decision_summary(app, di_setup):
    """Test 9: decision_summary returns correct aggregated totals."""
    with app.app_context():
        DecisionIntelligenceService.create_context("Ctx A", "risk", "US", di_setup["org"].id)
        summary = DecisionIntelligenceService.decision_summary(di_setup["org"].id)
        assert summary["total_contexts"] >= 1
        assert "average_urgency_score" in summary


def test_api_contexts_endpoint(app, client, di_setup):
    """Test 10: GET /api/v1/governance-intelligence/contexts returns 200."""
    response = client.get(
        f"/api/v1/governance-intelligence/contexts?org_id={di_setup['org'].id}",
        headers=di_setup["headers"]
    )
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
