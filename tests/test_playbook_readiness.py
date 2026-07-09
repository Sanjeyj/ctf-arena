"""
Unit and Integration tests for Playbook Readiness.
Contains 10 test cases covering playbook structures audit, dependencies checking, readiness indexing weights, and API endpoints.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.validation_campaign import ValidationCampaign
from app.models.validation_scenario import ValidationScenario
from app.models.validation_execution import ValidationExecution
from app.models.playbook_readiness import PlaybookReadiness
from app.models.playbook import Playbook
from app.services.validation_campaign_service import ValidationCampaignService
from app.services.validation_engine_service import ValidationEngineService
from app.services.playbook_validation_service import PlaybookValidationService
from app.research.routes import create_jwt


@pytest.fixture
def readiness_setup(app):
    with app.app_context():
        db.session.query(PlaybookReadiness).delete()
        db.session.query(Playbook).delete()
        db.session.query(ValidationExecution).delete()
        db.session.query(ValidationScenario).delete()
        db.session.query(ValidationCampaign).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        pb = Playbook(
            name="Verify Response Playbook",
            description="Playbook for testing",
            trigger_type="manual",
            steps_json='["step1", "step2"]',
            is_active=True,
            organization_id=o1.id
        )
        db.session.add(pb)
        db.session.commit()

        c = ValidationCampaignService.create_campaign(
            "Playbook Campaign", "Desc", "playbook_validation", "scope", "medium", None, o1.id
        )
        s = ValidationCampaignService.add_scenario(
            c.id, "Playbook Scenario", "playbook", "Verify playbooks", "high", "remediated", "{}", o1.id
        )
        ex = ValidationEngineService.execute_scenario(s.id, o1.id)

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "pb": pb,
            "exec": ex,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_playbook_readiness_model(app, readiness_setup):
    """Test 1: PlaybookReadiness model properties."""
    with app.app_context():
        r = PlaybookReadiness(
            playbook_id=readiness_setup["pb"].id,
            execution_id=readiness_setup["exec"].id,
            step_coverage_score=0.9,
            dependency_score=0.8,
            approval_score=1.0,
            evidence_score=0.95,
            readiness_score=0.9,
            status="ready",
            organization_id=readiness_setup["o1"].id
        )
        db.session.add(r)
        db.session.commit()
        assert r.id is not None


def test_evaluate_structure(app, readiness_setup):
    """Test 2: evaluate_structure returns structural correctness score."""
    with app.app_context():
        score = PlaybookValidationService.evaluate_structure(readiness_setup["pb"].id, readiness_setup["o1"].id)
        assert score == 0.8  # default baseline validation score


def test_evaluate_dependencies(app, readiness_setup):
    """Test 3: evaluate_dependencies returns dependency correctness score."""
    with app.app_context():
        score = PlaybookValidationService.evaluate_dependencies(readiness_setup["pb"].id, readiness_setup["o1"].id)
        assert score == 0.9  # baseline dependency checks score


def test_evaluate_approvals(app, readiness_setup):
    """Test 4: evaluate_approvals returns approval score."""
    with app.app_context():
        score = PlaybookValidationService.evaluate_approvals(readiness_setup["pb"].id, readiness_setup["o1"].id)
        assert score == 1.0  # baseline approvals checked score


def test_calculate_readiness_formula(app, readiness_setup):
    """Test 5: calculate_readiness uses correct weights calculation."""
    with app.app_context():
        # formula: 0.4 * step_cov + 0.3 * dep_score + 0.15 * app_score + 0.15 * ev_score
        # with defaults: 0.4*0.8 + 0.3*0.9 + 0.15*1.0 + 0.15*0.95 = 0.32 + 0.27 + 0.15 + 0.1425 = 0.8825 -> rounded to 0.88
        record = PlaybookValidationService.calculate_readiness(readiness_setup["pb"].id, readiness_setup["exec"].id, readiness_setup["o1"].id)
        assert record.readiness_score == 0.88


def test_calculate_readiness_records_saved(app, readiness_setup):
    """Test 6: calculate_readiness saves record successfully in DB."""
    with app.app_context():
        record = PlaybookValidationService.calculate_readiness(readiness_setup["pb"].id, readiness_setup["exec"].id, readiness_setup["o1"].id)
        saved = PlaybookReadiness.query.filter_by(id=record.id).first()
        assert saved is not None
        assert saved.status == 'ready'


def test_identify_missing_steps(app, readiness_setup):
    """Test 7: identify_missing_steps returns missing components."""
    with app.app_context():
        steps = PlaybookValidationService.identify_missing_steps(readiness_setup["pb"].id, readiness_setup["o1"].id)
        assert len(steps) > 0
        assert "Missing Step" in steps[0]


def test_playbook_summary_empty(app, readiness_setup):
    """Test 8: playbook_summary returns defaults when no records."""
    with app.app_context():
        summary = PlaybookValidationService.playbook_summary(readiness_setup["o1"].id)
        assert summary["total_playbooks"] == 0
        assert summary["avg_readiness"] == 0.0


def test_playbook_summary_calculated(app, readiness_setup):
    """Test 9: playbook_summary aggregates metrics correctly."""
    with app.app_context():
        PlaybookValidationService.calculate_readiness(readiness_setup["pb"].id, readiness_setup["exec"].id, readiness_setup["o1"].id)
        summary = PlaybookValidationService.playbook_summary(readiness_setup["o1"].id)
        assert summary["total_playbooks"] == 1
        assert summary["avg_readiness"] == 0.88


def test_api_playbook_readiness_route(app, readiness_setup):
    """Test 10: Playbook readiness API endpoints."""
    client = app.test_client()

    resp = client.post(
        f'/api/v1/validation-fabric/playbooks/{readiness_setup["pb"].id}/evaluate',
        json={
            "org_id": readiness_setup["o1"].id,
            "execution_id": readiness_setup["exec"].id
        },
        headers=readiness_setup["headers"]
    )
    assert resp.status_code == 201
    assert resp.get_json()["readiness_score"] == 0.88

    resp = client.get(
        f'/api/v1/validation-fabric/playbooks/summary?org_id={readiness_setup["o1"].id}',
        headers=readiness_setup["headers"]
    )
    assert resp.status_code == 200
    assert resp.get_json()["total_playbooks"] == 1
