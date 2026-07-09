import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.strategic_decision_record import StrategicDecisionRecord
from app.services.strategic_decision_service import StrategicDecisionService
from app.research.routes import create_jwt


@pytest.fixture
def dec_setup(app):
    with app.app_context():
        db.session.query(StrategicDecisionRecord).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_create_decision_valid(app, dec_setup):
    """Test 1: Create valid strategic decision record in pending status."""
    with app.app_context():
        rec = StrategicDecisionService.create_decision(
            "budget_allocation", "Strategic MFA Rollout", "Rollout MFA", ["Option A", "Option B"], "Option A", dec_setup["o1"].id
        )
        assert rec.id is not None
        assert rec.approval_status == "pending"


def test_create_decision_invalid_type(app, dec_setup):
    """Test 2: Invalid type triggers ValueError."""
    with app.app_context():
        with pytest.raises(ValueError):
            StrategicDecisionService.create_decision(
                "invalid_type", "Title", "Context", [], "A", dec_setup["o1"].id
            )


def test_evaluate_options(app, dec_setup):
    """Test 3: Evaluates decision update scoring values."""
    with app.app_context():
        rec = StrategicDecisionService.create_decision(
            "budget_allocation", "Title", "Context", [], "A", dec_setup["o1"].id
        )
        evaluated = StrategicDecisionService.evaluate_options(rec.id, dec_setup["o1"].id)
        assert evaluated.risk_reduction_score > 0.0


def test_score_option(dec_setup):
    """Test 4: Option scoring logic returns float."""
    score = StrategicDecisionService.score_option(1, "Option A", dec_setup["o1"].id)
    assert isinstance(score, float)


def test_recommend_option(app, dec_setup):
    """Test 5: Sets recommended option reference."""
    with app.app_context():
        rec = StrategicDecisionService.create_decision(
            "budget_allocation", "Title", "Context", [], None, dec_setup["o1"].id
        )
        updated = StrategicDecisionService.recommend_option(rec.id, "Option B", dec_setup["o1"].id)
        assert updated.recommended_option == "Option B"


def test_submit_for_approval(app, dec_setup):
    """Test 6: Submission changes status to requires_review."""
    with app.app_context():
        rec = StrategicDecisionService.create_decision(
            "budget_allocation", "Title", "Context", [], None, dec_setup["o1"].id
        )
        submitted = StrategicDecisionService.submit_for_approval(rec.id, dec_setup["o1"].id)
        assert submitted.approval_status == "requires_review"


def test_approve_decision(app, dec_setup):
    """Test 7: Approval transitions status and logs signer."""
    with app.app_context():
        rec = StrategicDecisionService.create_decision(
            "budget_allocation", "Title", "Context", [], None, dec_setup["o1"].id
        )
        approved = StrategicDecisionService.approve(rec.id, "chief_security_officer", dec_setup["o1"].id)
        assert approved.approval_status == "approved"
        assert approved.approved_by == "chief_security_officer"


def test_reject_decision(app, dec_setup):
    """Test 8: Rejection transitions status to rejected."""
    with app.app_context():
        rec = StrategicDecisionService.create_decision(
            "budget_allocation", "Title", "Context", [], None, dec_setup["o1"].id
        )
        rejected = StrategicDecisionService.reject(rec.id, dec_setup["o1"].id)
        assert rejected.approval_status == "rejected"


def test_decision_summary(app, dec_setup):
    """Test 9: Decision summary aggregates count details."""
    with app.app_context():
        StrategicDecisionService.create_decision(
            "budget_allocation", "Title", "Context", [], None, dec_setup["o1"].id
        )
        summary = StrategicDecisionService.decision_summary(dec_setup["o1"].id)
        assert summary["total_decisions"] == 1


def test_api_get_decisions(app, client, dec_setup):
    """Test 10: REST API list decisions endpoint."""
    res = client.get(
        f'/api/v1/strategic-resilience/decisions?org_id={dec_setup["o1"].id}',
        headers=dec_setup["headers"]
    )
    assert res.status_code == 200
