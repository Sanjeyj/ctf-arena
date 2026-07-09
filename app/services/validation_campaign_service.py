"""
ValidationCampaignService - Phase 35 Continuous Security Validation.
Handles campaigns management, scenarios listing, lifecycle state transitions, and metrics.
"""
from app.extensions import db
from app.models.validation_campaign import ValidationCampaign
from app.models.validation_scenario import ValidationScenario
from app.services.hook_service import HookService
import datetime
import json


class ValidationCampaignService:
    @staticmethod
    def create_campaign(name, description, campaign_type, scope, priority, scheduled_at, org_id):
        # Hook trigger
        hook_results = HookService.trigger_hook(
            'before_validation_campaign',
            name=name,
            description=description,
            campaign_type=campaign_type,
            scope=scope,
            priority=priority,
            scheduled_at=scheduled_at,
            org_id=org_id
        )
        for res in hook_results:
            if isinstance(res, dict):
                name = res.get('name', name)
                campaign_type = res.get('campaign_type', campaign_type)
                priority = res.get('priority', priority)

        allowed_types = [
            'control_validation', 'detection_validation', 'playbook_validation',
            'resilience_validation', 'architecture_validation', 'remediation_verification'
        ]
        if campaign_type not in allowed_types:
            raise ValueError(f"Invalid campaign_type. Must be one of: {allowed_types}")

        campaign = ValidationCampaign(
            name=name,
            description=description,
            campaign_type=campaign_type,
            scope=scope,
            status='draft',
            priority=priority,
            scheduled_at=scheduled_at,
            organization_id=org_id
        )
        db.session.add(campaign)
        db.session.commit()

        HookService.trigger_hook('after_validation_campaign', campaign_id=campaign.id, org_id=org_id)
        return campaign

    @staticmethod
    def add_scenario(campaign_id, name, scenario_type, description, severity, expected_outcome, configuration_json, org_id):
        campaign = ValidationCampaign.query.filter_by(id=campaign_id, organization_id=org_id).first()
        if not campaign:
            return None

        scenario = ValidationScenario(
            campaign_id=campaign_id,
            name=name,
            scenario_type=scenario_type,
            description=description,
            severity=severity,
            expected_outcome=expected_outcome,
            configuration_json=configuration_json,
            status='active',
            organization_id=org_id
        )
        db.session.add(scenario)
        db.session.commit()
        return scenario

    @staticmethod
    def schedule_campaign(campaign_id, org_id):
        campaign = ValidationCampaign.query.filter_by(id=campaign_id, organization_id=org_id).first()
        if not campaign:
            return None
        if campaign.status != 'draft':
            raise ValueError("Only draft campaigns can be scheduled.")
        campaign.status = 'scheduled'
        db.session.commit()
        return campaign

    @staticmethod
    def start_campaign(campaign_id, org_id):
        campaign = ValidationCampaign.query.filter_by(id=campaign_id, organization_id=org_id).first()
        if not campaign:
            return None
        if campaign.status not in ['draft', 'scheduled']:
            raise ValueError("Only draft or scheduled campaigns can be started.")
        campaign.status = 'running'
        campaign.started_at = datetime.datetime.utcnow()
        db.session.commit()
        return campaign

    @staticmethod
    def complete_campaign(campaign_id, org_id):
        campaign = ValidationCampaign.query.filter_by(id=campaign_id, organization_id=org_id).first()
        if not campaign:
            return None
        if campaign.status != 'running':
            raise ValueError("Only running campaigns can be completed.")
        campaign.status = 'completed'
        campaign.completed_at = datetime.datetime.utcnow()
        db.session.commit()
        return campaign

    @staticmethod
    def cancel_campaign(campaign_id, org_id):
        campaign = ValidationCampaign.query.filter_by(id=campaign_id, organization_id=org_id).first()
        if not campaign:
            return None
        if campaign.status not in ['draft', 'scheduled', 'running']:
            raise ValueError("Cannot cancel campaign in this status.")
        campaign.status = 'cancelled'
        campaign.completed_at = datetime.datetime.utcnow()
        db.session.commit()
        return campaign

    @staticmethod
    def campaign_summary(campaign_id, org_id):
        campaign = ValidationCampaign.query.filter_by(id=campaign_id, organization_id=org_id).first()
        if not campaign:
            return None
        scenarios = ValidationScenario.query.filter_by(campaign_id=campaign_id, organization_id=org_id).all()
        return {
            "campaign_id": campaign.id,
            "name": campaign.name,
            "status": campaign.status,
            "scenarios_count": len(scenarios),
            "priority": campaign.priority
        }
