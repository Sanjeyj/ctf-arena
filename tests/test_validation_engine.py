"""
Unit and Integration tests for Validation Engine.
Contains 10 test cases covering scenario executions, assertion checks, effectiveness calculations, and REST API execution endpoints.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.validation_campaign import ValidationCampaign
from app.models.validation_scenario import ValidationScenario
from app.models.validation_execution import ValidationExecution
from app.models.validation_check import ValidationCheck
from app.services.validation_campaign_service import ValidationCampaignService
from app.services.validation_engine_service import ValidationEngineService
from app.research.routes import create_jwt


@pytest.fixture
def engine_setup(app):
    with app.app_context():
        db.session.query(ValidationCheck).delete()
        db.session.query(ValidationExecution).delete()
        db.session.query(ValidationScenario).delete()
        db.session.query(ValidationCampaign).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        c = ValidationCampaignService.create_campaign(
            "Engine Campaign", "Desc", "control_validation", "scope", "medium", None, o1.id
        )
        s = ValidationCampaignService.add_scenario(
            c.id, "Engine Scenario", "control", "Verify firewall", "high", "blocked", '{"fail_sim": false}', o1.id
        )

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "scenario": s,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_execution_model(app, engine_setup):
    """Test 1: ValidationExecution model fields."""
    with app.app_context():
        ex = ValidationExecution(
            campaign_id=engine_setup["scenario"].campaign_id,
            scenario_id=engine_setup["scenario"].id,
            status="running",
            organization_id=engine_setup["o1"].id
        )
        db.session.add(ex)
        db.session.commit()
        assert ex.id is not None


def test_check_model(app, engine_setup):
    """Test 2: ValidationCheck model fields."""
    with app.app_context():
        ex = ValidationExecution(
            campaign_id=engine_setup["scenario"].campaign_id,
            scenario_id=engine_setup["scenario"].id,
            status="running",
            organization_id=engine_setup["o1"].id
        )
        db.session.add(ex)
        db.session.commit()

        ck = ValidationCheck(
            execution_id=ex.id,
            check_type="control",
            target_reference_type="firewall",
            target_reference_id=1,
            expected_result="blocked",
            actual_result="blocked",
            score=100.0,
            status="passed",
            organization_id=engine_setup["o1"].id
        )
        db.session.add(ck)
        db.session.commit()
        assert ck.id is not None


def test_execute_scenario(app, engine_setup):
    """Test 3: ValidationEngineService.execute_scenario success."""
    with app.app_context():
        exec_record = ValidationEngineService.execute_scenario(engine_setup["scenario"].id, engine_setup["o1"].id)
        assert exec_record.status == 'completed'
        assert exec_record.result_score == 100.0
        assert exec_record.effectiveness_score == 1.0


def test_execute_scenario_fail_sim(app, engine_setup):
    """Test 4: execute_scenario with config setting fail_sim=True."""
    with app.app_context():
        scenario2 = ValidationCampaignService.add_scenario(
            engine_setup["scenario"].campaign_id, "Engine Scenario 2", "control", "Verify firewall", "high", "blocked", '{"fail_sim": true}', engine_setup["o1"].id
        )
        exec_record = ValidationEngineService.execute_scenario(scenario2.id, engine_setup["o1"].id)
        assert exec_record.status == 'completed'
        assert exec_record.result_score == 50.0  # 1 of 2 checks passed
        assert exec_record.effectiveness_score == 0.5


def test_create_check(app, engine_setup):
    """Test 5: ValidationEngineService.create_check."""
    with app.app_context():
        ex = ValidationExecution(
            campaign_id=engine_setup["scenario"].campaign_id,
            scenario_id=engine_setup["scenario"].id,
            status="running",
            organization_id=engine_setup["o1"].id
        )
        db.session.add(ex)
        db.session.commit()

        ck = ValidationEngineService.create_check(
            ex.id, "control", "mock_type", 12, "expected", "actual", 80.0, "passed", None, engine_setup["o1"].id
        )
        assert ck.id is not None
        assert ck.score == 80.0


def test_evaluate_expected_outcome(app, engine_setup):
    """Test 6: ValidationEngineService.evaluate_expected_outcome."""
    with app.app_context():
        exec_record = ValidationEngineService.execute_scenario(engine_setup["scenario"].id, engine_setup["o1"].id)
        outcome = ValidationEngineService.evaluate_expected_outcome(exec_record.id, engine_setup["o1"].id)
        assert outcome is True


def test_calculate_effectiveness(app, engine_setup):
    """Test 7: ValidationEngineService.calculate_effectiveness calculation rules."""
    assert ValidationEngineService.calculate_effectiveness(90.0, 100.0) == 0.9
    assert ValidationEngineService.calculate_effectiveness(110.0, 100.0) == 1.0
    assert ValidationEngineService.calculate_effectiveness(0.0, 80.0) == 0.0


def test_complete_execution(app, engine_setup):
    """Test 8: ValidationEngineService.complete_execution."""
    with app.app_context():
        ex = ValidationExecution(
            campaign_id=engine_setup["scenario"].campaign_id,
            scenario_id=engine_setup["scenario"].id,
            status="running",
            organization_id=engine_setup["o1"].id
        )
        db.session.add(ex)
        db.session.commit()

        ex = ValidationEngineService.complete_execution(ex.id, 85.0, "Completed execution manually", engine_setup["o1"].id)
        assert ex.status == "completed"
        assert ex.result_score == 85.0


def test_execution_summary(app, engine_setup):
    """Test 9: ValidationEngineService.execution_summary."""
    with app.app_context():
        exec_record = ValidationEngineService.execute_scenario(engine_setup["scenario"].id, engine_setup["o1"].id)
        summary = ValidationEngineService.execution_summary(exec_record.id, engine_setup["o1"].id)
        assert summary["execution_id"] == exec_record.id
        assert summary["passed_checks"] == 2


def test_api_execute_scenario_route(app, engine_setup):
    """Test 10: Scenario execution REST API routing."""
    client = app.test_client()

    resp = client.post(
        f'/api/v1/validation-fabric/scenarios/{engine_setup["scenario"].id}/execute',
        json={"org_id": engine_setup["o1"].id},
        headers=engine_setup["headers"]
    )
    assert resp.status_code == 201
    assert resp.get_json()["status"] == "completed"
