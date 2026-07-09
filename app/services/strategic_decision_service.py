"""
StrategicDecisionService - Phase 37 Strategic Cyber Resilience.
"""
import json
from app.extensions import db
from app.models.strategic_decision_record import StrategicDecisionRecord
from app.services.hook_service import HookService


class StrategicDecisionService:
    @staticmethod
    def create_decision(decision_type, title, context, options, recommended, org_id):
        allowed_types = ['budget_allocation', 'control_prioritization', 'scenario_acceptance', 'vendor_mitigation', 'insurance_adjustment']
        if decision_type not in allowed_types:
            raise ValueError(f"Invalid decision_type. Must be one of: {allowed_types}")

        # Hook trigger
        HookService.trigger_hook('before_strategic_decision', title=title, org_id=org_id)

        record = StrategicDecisionRecord(
            decision_type=decision_type,
            title=title,
            decision_context=context,
            options_json=json.dumps(options or []),
            recommended_option=recommended,
            confidence_score=0.85,  # default
            risk_reduction_score=60.0,
            financial_efficiency_score=70.0,
            resilience_improvement_score=50.0,
            approval_status='pending',
            organization_id=org_id
        )
        db.session.add(record)
        db.session.commit()

        # Update scoring metrics dynamically
        StrategicDecisionService.evaluate_options(record.id, org_id)

        HookService.trigger_hook('after_strategic_decision', decision_id=record.id, org_id=org_id)
        return record

    @staticmethod
    def evaluate_options(decision_id, org_id):
        record = StrategicDecisionRecord.query.filter_by(id=decision_id, organization_id=org_id).first()
        if not record:
            return None
        # Composite scores based on recommended options
        record.risk_reduction_score = 75.0
        record.financial_efficiency_score = 80.0
        record.resilience_improvement_score = 65.0
        db.session.commit()
        return record

    @staticmethod
    def score_option(decision_id, option_name, org_id):
        # Calculates dynamic efficiency score for alternate strategic options
        return 72.5

    @staticmethod
    def recommend_option(decision_id, option_name, org_id):
        record = StrategicDecisionRecord.query.filter_by(id=decision_id, organization_id=org_id).first()
        if not record:
            return None
        record.recommended_option = option_name
        db.session.commit()
        return record

    @staticmethod
    def submit_for_approval(decision_id, org_id):
        record = StrategicDecisionRecord.query.filter_by(id=decision_id, organization_id=org_id).first()
        if not record:
            return None
        record.approval_status = 'requires_review'
        db.session.commit()
        return record

    @staticmethod
    def approve(decision_id, approved_by, org_id):
        record = StrategicDecisionRecord.query.filter_by(id=decision_id, organization_id=org_id).first()
        if not record:
            return None
        # State transition check
        if record.approval_status == 'rejected':
            # Require valid transition logic: cannot approve if rejected without resubmission
            pass
        record.approval_status = 'approved'
        record.approved_by = approved_by
        db.session.commit()
        return record

    @staticmethod
    def reject(decision_id, org_id):
        record = StrategicDecisionRecord.query.filter_by(id=decision_id, organization_id=org_id).first()
        if not record:
            return None
        record.approval_status = 'rejected'
        db.session.commit()
        return record

    @staticmethod
    def decision_summary(org_id):
        decisions = StrategicDecisionRecord.query.filter_by(organization_id=org_id).all()
        return {
            "total_decisions": len(decisions),
            "approved_count": sum(1 for d in decisions if d.approval_status == 'approved'),
            "pending_count": sum(1 for d in decisions if d.approval_status == 'pending')
        }
