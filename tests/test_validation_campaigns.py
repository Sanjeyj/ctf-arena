"""
Unit and Integration tests for Validation Campaigns.
Contains 10 test cases covering campaigns model validation, service creations, state changes, and REST endpoints.
"""
import pytest
import datetime
from app.extensions import db
from app.models.organization import Organization
from app.models.validation_campaign import ValidationCampaign
from app.models.validation_scenario import ValidationScenario
from app.services.validation_campaign_service import ValidationCampaignService
from app.services.hook_service import HookService
from app.research.routes import create_jwt


@pytest.fixture
def campaign_setup(app):
    with app.app_context():
        db.session.query(ValidationScenario).delete()
        db.session.query(ValidationCampaign).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_campaign_model(app, campaign_setup):
    """Test 1: ValidationCampaign model validations."""
    with app.app_context():
        c = ValidationCampaign(
            name="Control Audit",
            campaign_type="control_validation",
            priority="high",
            organization_id=campaign_setup["o1"].id
        )
        db.session.add(c)
        db.session.commit()
        assert c.id is not None
        assert c.status == "draft"


def test_create_campaign_service(app, campaign_setup):
    """Test 2: ValidationCampaignService.create_campaign."""
    with app.app_context():
        c = ValidationCampaignService.create_campaign(
            "Detection Audit", "Verify Sigma Rules", "detection_validation", "detection", "medium", None, campaign_setup["o1"].id
        )
        assert c.id is not None
        assert c.status == "draft"


def test_create_campaign_invalid_type(app, campaign_setup):
    """Test 3: create_campaign raises error for invalid types."""
    with app.app_context():
        with pytest.raises(ValueError, match="Invalid campaign_type"):
            ValidationCampaignService.create_campaign(
                "Audit", "Desc", "invalid_type", "scope", "medium", None, campaign_setup["o1"].id
            )


def test_add_scenario(app, campaign_setup):
    """Test 4: ValidationCampaignService.add_scenario."""
    with app.app_context():
        c = ValidationCampaignService.create_campaign(
            "Audit", "Desc", "control_validation", "scope", "medium", None, campaign_setup["o1"].id
        )
        s = ValidationCampaignService.add_scenario(
            c.id, "Scenario 1", "control", "Verify firewall rules", "high", "blocked", "{}", campaign_setup["o1"].id
        )
        assert s.id is not None
        assert s.name == "Scenario 1"


def test_schedule_campaign(app, campaign_setup):
    """Test 5: ValidationCampaignService.schedule_campaign."""
    with app.app_context():
        c = ValidationCampaignService.create_campaign(
            "Audit", "Desc", "control_validation", "scope", "medium", None, campaign_setup["o1"].id
        )
        campaign = ValidationCampaignService.schedule_campaign(c.id, campaign_setup["o1"].id)
        assert campaign.status == "scheduled"


def test_start_campaign(app, campaign_setup):
    """Test 6: ValidationCampaignService.start_campaign."""
    with app.app_context():
        c = ValidationCampaignService.create_campaign(
            "Audit", "Desc", "control_validation", "scope", "medium", None, campaign_setup["o1"].id
        )
        campaign = ValidationCampaignService.start_campaign(c.id, campaign_setup["o1"].id)
        assert campaign.status == "running"
        assert campaign.started_at is not None


def test_complete_campaign(app, campaign_setup):
    """Test 7: ValidationCampaignService.complete_campaign."""
    with app.app_context():
        c = ValidationCampaignService.create_campaign(
            "Audit", "Desc", "control_validation", "scope", "medium", None, campaign_setup["o1"].id
        )
        ValidationCampaignService.start_campaign(c.id, campaign_setup["o1"].id)
        campaign = ValidationCampaignService.complete_campaign(c.id, campaign_setup["o1"].id)
        assert campaign.status == "completed"
        assert campaign.completed_at is not None


def test_cancel_campaign(app, campaign_setup):
    """Test 8: ValidationCampaignService.cancel_campaign."""
    with app.app_context():
        c = ValidationCampaignService.create_campaign(
            "Audit", "Desc", "control_validation", "scope", "medium", None, campaign_setup["o1"].id
        )
        campaign = ValidationCampaignService.cancel_campaign(c.id, campaign_setup["o1"].id)
        assert campaign.status == "cancelled"


def test_campaign_summary(app, campaign_setup):
    """Test 9: ValidationCampaignService.campaign_summary."""
    with app.app_context():
        c = ValidationCampaignService.create_campaign(
            "Audit", "Desc", "control_validation", "scope", "medium", None, campaign_setup["o1"].id
        )
        summary = ValidationCampaignService.campaign_summary(c.id, campaign_setup["o1"].id)
        assert summary["campaign_id"] == c.id
        assert summary["scenarios_count"] == 0


def test_api_campaigns_flow(app, campaign_setup):
    """Test 10: campaigns REST endpoints routing and JWT protection."""
    client = app.test_client()

    # Unauthorized check
    resp = client.get('/api/v1/validation-fabric/campaigns')
    assert resp.status_code == 401

    # Authorized check
    resp = client.post(
        '/api/v1/validation-fabric/campaigns',
        json={
            "org_id": campaign_setup["o1"].id,
            "name": "API Campaign",
            "campaign_type": "control_validation"
        },
        headers=campaign_setup["headers"]
    )
    assert resp.status_code == 201
    campaign_id = resp.get_json()["id"]

    resp = client.get(
        f'/api/v1/validation-fabric/campaigns?org_id={campaign_setup["o1"].id}',
        headers=campaign_setup["headers"]
    )
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1
