"""
RemediationPrioritizationService - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
Prioritizes remediation plans based on severity and business impact.
"""
from app.extensions import db
from app.models.remediation_plan import RemediationPlan
from app.models.exposure_finding import ExposureFinding
from app.services.hook_service import HookService
import json


class RemediationPrioritizationService:

    @staticmethod
    def create_plan(title, finding_id, recommended_action, target_date, org_id):
        finding = ExposureFinding.query.filter_by(id=finding_id, organization_id=org_id).first()
        if not finding:
            return None

        # Automatically calculate priority score
        severity_mult = {'critical': 4.0, 'high': 3.0, 'medium': 2.0, 'low': 1.0}
        mult = severity_mult.get(finding.severity.lower(), 1.0)
        priority = finding.impact_score * mult

        # Hook mutation check
        hook_results = HookService.trigger_hook(
            'before_remediation_prioritization',
            title=title,
            finding_id=finding_id,
            recommended_action=recommended_action,
            priority_score=priority,
            org_id=org_id
        )
        for res in hook_results:
            if isinstance(res, dict):
                priority = res.get('priority_score', priority)

        plan = RemediationPlan(
            title=title,
            finding_id=finding_id,
            priority_score=priority,
            recommended_action=recommended_action,
            target_date=target_date,
            organization_id=org_id
        )
        db.session.add(plan)
        db.session.commit()

        HookService.trigger_hook('after_remediation_prioritization', plan_id=plan.id, org_id=org_id)
        return plan

    @staticmethod
    def calculate_priority(plan_id, org_id):
        plan = RemediationPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            return 0.0

        finding = plan.finding
        if finding:
            severity_mult = {'critical': 4.0, 'high': 3.0, 'medium': 2.0, 'low': 1.0}
            mult = severity_mult.get(finding.severity.lower(), 1.0)
            plan.priority_score = finding.impact_score * mult
            db.session.commit()

        return plan.priority_score

    @staticmethod
    def recommend_compensating_controls(plan_id, org_id):
        plan = RemediationPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            return []

        finding = plan.finding
        if not finding:
            return ["GEN-001"]

        # Suggest based on finding type
        ftype = finding.finding_type.lower()
        if 'vulnerability' in ftype:
            return ["VULN-PATCH-01", "IPS-SHIELD-02"]
        elif 'misconfiguration' in ftype:
            return ["CONF-AUDIT-03", "ZTR-ZONE-04"]
        elif 'credentials' in ftype:
            return ["AUTH-MFA-05", "KEY-ROT-06"]

        return ["DEF-IN-DEPTH-07"]

    @staticmethod
    def approve_plan(plan_id, org_id):
        plan = RemediationPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if plan:
            plan.approval_status = 'approved'
            db.session.commit()
            return plan
        return None

    @staticmethod
    def close_plan(plan_id, status, org_id):
        plan = RemediationPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if plan:
            plan.status = status
            db.session.commit()
            return plan
        return None

    @staticmethod
    def remediation_summary(org_id):
        plans = RemediationPlan.query.filter_by(organization_id=org_id).all()
        completed = sum(1 for p in plans if p.status in ['completed', 'verified'])
        approved = sum(1 for p in plans if p.approval_status == 'approved')

        return {
            "total_plans": len(plans),
            "approved_plans": approved,
            "completed_plans": completed
        }
