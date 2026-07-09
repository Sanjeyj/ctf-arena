"""
RemediationVerificationService - Phase 35 Continuous Security Validation.
Simulates remediation effectiveness, calculates posture improvements, and marks plans verified.
"""
from app.extensions import db
from app.models.remediation_plan import RemediationPlan
from app.models.validation_scenario import ValidationScenario
from app.models.validation_execution import ValidationExecution
import datetime


class RemediationVerificationService:
    @staticmethod
    def select_plan(plan_id, org_id):
        return RemediationPlan.query.filter_by(id=plan_id, organization_id=org_id).first()

    @staticmethod
    def create_verification_scenario(plan_id, org_id):
        plan = RemediationVerificationService.select_plan(plan_id, org_id)
        if not plan:
            return None

        # Look up parent campaign to attach scenario
        from app.models.validation_campaign import ValidationCampaign
        campaign = ValidationCampaign.query.filter_by(
            campaign_type='remediation_verification', organization_id=org_id
        ).first()
        if not campaign:
            from app.services.validation_campaign_service import ValidationCampaignService
            campaign = ValidationCampaignService.create_campaign(
                "Remediation Verification Campaign", "Campaign to verify remediations",
                "remediation_verification", "remediation", "high", None, org_id
            )

        scenario = ValidationScenario(
            campaign_id=campaign.id,
            name=f"Verify: {plan.title}",
            scenario_type="remediation_verification",
            description=f"Automated verification scenario for Remediation Plan ID {plan_id}",
            severity="medium",
            expected_outcome="mitigated",
            configuration_json=f'{{"plan_id": {plan_id}}}',
            status='active',
            organization_id=org_id
        )
        db.session.add(scenario)
        db.session.commit()
        return scenario

    @staticmethod
    def evaluate_remediation(execution_id, org_id):
        exec_record = ValidationExecution.query.filter_by(id=execution_id, organization_id=org_id).first()
        if not exec_record:
            return 0.0

        # Simulate evaluation delta
        baseline = exec_record.baseline_score  # e.g., 70.0
        result = 95.0
        exec_record.result_score = result
        exec_record.effectiveness_score = 0.95
        db.session.commit()

        # Update associated RemediationPlan
        scenario = ValidationScenario.query.filter_by(id=exec_record.scenario_id).first()
        if scenario and scenario.configuration_json:
            import json
            try:
                config = json.loads(scenario.configuration_json)
                plan_id = config.get("plan_id")
                if plan_id:
                    RemediationVerificationService.mark_verified(plan_id, org_id)
            except Exception:
                pass

        return 0.95

    @staticmethod
    def calculate_improvement(baseline_risk, mitigated_risk):
        return max(0.0, baseline_risk - mitigated_risk)

    @staticmethod
    def mark_verified(plan_id, org_id):
        plan = RemediationVerificationService.select_plan(plan_id, org_id)
        if not plan:
            return None
        plan.status = 'verified'
        db.session.commit()
        return plan

    @staticmethod
    def verification_summary(org_id):
        plans = RemediationPlan.query.filter_by(organization_id=org_id).all()
        verified = sum(1 for p in plans if p.status == 'verified')
        return {
            "total_remediation_plans": len(plans),
            "verified_plans": verified,
            "avg_improvement": 25.0  # mock improvement rating delta
        }
