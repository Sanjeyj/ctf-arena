"""
Unit and Integration tests for Remediation Verification.
Contains 10 test cases covering plans loading, verification scenario mappings, automated assessment runs, posture improvements, and verification REST APIs.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.exposure_asset import ExposureAsset
from app.models.exposure_finding import ExposureFinding
from app.models.remediation_plan import RemediationPlan
from app.models.validation_campaign import ValidationCampaign
from app.models.validation_scenario import ValidationScenario
from app.models.validation_execution import ValidationExecution
from app.services.validation_campaign_service import ValidationCampaignService
from app.services.validation_engine_service import ValidationEngineService
from app.services.remediation_verification_service import RemediationVerificationService
from app.research.routes import create_jwt


@pytest.fixture
def remediation_setup(app):
    with app.app_context():
        db.session.query(ValidationExecution).delete()
        db.session.query(ValidationScenario).delete()
        db.session.query(ValidationCampaign).delete()
        db.session.query(RemediationPlan).delete()
        db.session.query(ExposureFinding).delete()
        db.session.query(ExposureAsset).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        asset = ExposureAsset(
            asset_reference_type="asset",
            asset_reference_id=1,
            display_name="Verify Main",
            organization_id=o1.id
        )
        db.session.add(asset)
        db.session.commit()

        finding = ExposureFinding(
            exposure_asset_id=asset.id,
            finding_type="vulnerability",
            title="CVE-2024-9999",
            severity="high",
            likelihood=0.8,
            impact_score=8.5,
            confidence=0.9,
            status="open",
            source_type="simulation",
            organization_id=o1.id
        )
        db.session.add(finding)
        db.session.commit()

        plan = RemediationPlan(
            title="Update Packages",
            finding_id=finding.id,
            priority_score=9.0,
            recommended_action="Run updates",
            status="planned",
            organization_id=o1.id
        )
        db.session.add(plan)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "asset": asset,
            "finding": finding,
            "plan": plan,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_select_plan(app, remediation_setup):
    """Test 1: select_plan queries plan correctly."""
    with app.app_context():
        plan = RemediationVerificationService.select_plan(remediation_setup["plan"].id, remediation_setup["o1"].id)
        assert plan is not None
        assert plan.title == "Update Packages"


def test_create_verification_scenario_creates_campaign(app, remediation_setup):
    """Test 2: create_verification_scenario creates campaign if absent."""
    with app.app_context():
        scenario = RemediationVerificationService.create_verification_scenario(remediation_setup["plan"].id, remediation_setup["o1"].id)
        assert scenario is not None
        campaign = ValidationCampaign.query.filter_by(id=scenario.campaign_id).first()
        assert campaign.campaign_type == 'remediation_verification'


def test_create_verification_scenario_uses_existing(app, remediation_setup):
    """Test 3: create_verification_scenario reuses campaign if present."""
    with app.app_context():
        c = ValidationCampaignService.create_campaign(
            "Remediation Campaign", "Desc", "remediation_verification", "remediation", "high", None, remediation_setup["o1"].id
        )
        scenario = RemediationVerificationService.create_verification_scenario(remediation_setup["plan"].id, remediation_setup["o1"].id)
        assert scenario.campaign_id == c.id


def test_evaluate_remediation_score(app, remediation_setup):
    """Test 4: evaluate_remediation executes simulation score."""
    with app.app_context():
        scenario = RemediationVerificationService.create_verification_scenario(remediation_setup["plan"].id, remediation_setup["o1"].id)
        ex = ValidationEngineService.execute_scenario(scenario.id, remediation_setup["o1"].id)
        score = RemediationVerificationService.evaluate_remediation(ex.id, remediation_setup["o1"].id)
        assert score == 0.95


def test_evaluate_remediation_marks_verified(app, remediation_setup):
    """Test 5: evaluate_remediation marks plan status verified."""
    with app.app_context():
        scenario = RemediationVerificationService.create_verification_scenario(remediation_setup["plan"].id, remediation_setup["o1"].id)
        ex = ValidationEngineService.execute_scenario(scenario.id, remediation_setup["o1"].id)
        RemediationVerificationService.evaluate_remediation(ex.id, remediation_setup["o1"].id)
        plan = RemediationPlan.query.filter_by(id=remediation_setup["plan"].id).first()
        assert plan.status == 'verified'


def test_calculate_improvement(app, remediation_setup):
    """Test 6: calculate_improvement computes risk delta."""
    delta = RemediationVerificationService.calculate_improvement(10.0, 3.5)
    assert delta == 6.5
    assert RemediationVerificationService.calculate_improvement(5.0, 7.0) == 0.0


def test_mark_verified(app, remediation_setup):
    """Test 7: mark_verified state update."""
    with app.app_context():
        plan = RemediationVerificationService.mark_verified(remediation_setup["plan"].id, remediation_setup["o1"].id)
        assert plan.status == 'verified'


def test_verification_summary(app, remediation_setup):
    """Test 8: verification_summary stats."""
    with app.app_context():
        summary = RemediationVerificationService.verification_summary(remediation_setup["o1"].id)
        assert summary["total_remediation_plans"] == 1
        assert summary["verified_plans"] == 0


def test_remediation_verification_e2e(app, remediation_setup):
    """Test 9: Verification E2E flow check."""
    with app.app_context():
        plan_id = remediation_setup["plan"].id
        org_id = remediation_setup["o1"].id

        scenario = RemediationVerificationService.create_verification_scenario(plan_id, org_id)
        ex = ValidationEngineService.execute_scenario(scenario.id, org_id)
        outcome = RemediationVerificationService.evaluate_remediation(ex.id, org_id)
        assert outcome == 0.95
        assert RemediationPlan.query.get(plan_id).status == 'verified'


def test_api_verify_remediation_route(app, remediation_setup):
    """Test 10: Verification API POST route."""
    client = app.test_client()

    resp = client.post(
        '/api/v1/validation-fabric/remediation/verify',
        json={
            "org_id": remediation_setup["o1"].id,
            "plan_id": remediation_setup["plan"].id
        },
        headers=remediation_setup["headers"]
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == 'verified'
    assert data["improvement_score"] == 0.95
