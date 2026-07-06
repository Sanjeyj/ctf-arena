"""
ModelGovernanceService - Phase 31 Cyber Platform Control Plane.
Tracks AI provider/model governance records.
"""
from app.extensions import db
from app.models.model_governance_record import ModelGovernanceRecord
from app.services.hook_service import HookService
import datetime
import json


class ModelGovernanceService:
    @staticmethod
    def register_model(model_name: str, provider: str, org_id: int, purpose: str = None, risk_level: str = 'medium') -> ModelGovernanceRecord:
        """Register AI model in the governance library."""
        rec = ModelGovernanceRecord(
            model_name=model_name,
            provider=provider,
            purpose=purpose,
            risk_level=risk_level,
            approval_status='draft',
            evaluation_score=1.0,
            last_reviewed_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(rec)
        db.session.commit()
        return rec

    @staticmethod
    def evaluate_model(record_id: int, score: float, org_id: int) -> ModelGovernanceRecord:
        """Evaluate prompt safety score indices, triggering check hooks."""
        rec = db.session.get(ModelGovernanceRecord, record_id)
        if not rec or rec.organization_id != org_id:
            return None

        HookService.trigger_hook("before_model_governance_check", record=rec)

        rec.evaluation_score = max(0.0, min(1.0, score))
        rec.last_reviewed_at = datetime.datetime.utcnow()
        db.session.commit()

        HookService.trigger_hook("after_model_governance_check", record=rec, score=score)

        return rec

    @staticmethod
    def approve(record_id: int, org_id: int) -> ModelGovernanceRecord:
        """Approve model for active simulation usage."""
        rec = db.session.get(ModelGovernanceRecord, record_id)
        if not rec or rec.organization_id != org_id:
            return None
        rec.approval_status = 'approved'
        db.session.commit()
        return rec

    @staticmethod
    def restrict(record_id: int, org_id: int) -> ModelGovernanceRecord:
        """Restrict model usage due to evaluation failures."""
        rec = db.session.get(ModelGovernanceRecord, record_id)
        if not rec or rec.organization_id != org_id:
            return None
        rec.approval_status = 'restricted'
        db.session.commit()
        return rec

    @staticmethod
    def retire(record_id: int, org_id: int) -> ModelGovernanceRecord:
        """Retire model, decommissioning from list."""
        rec = db.session.get(ModelGovernanceRecord, record_id)
        if not rec or rec.organization_id != org_id:
            return None
        rec.approval_status = 'retired'
        db.session.commit()
        return rec

    @staticmethod
    def governance_summary(org_id: int) -> dict:
        """Summarize AI models governance levels."""
        recs = ModelGovernanceRecord.query.filter_by(organization_id=org_id).all()
        if not recs:
            return {'total_models': 0, 'approved_count': 0, 'avg_score': 1.0}
        approved = sum(1 for r in recs if r.approval_status == 'approved')
        avg_score = sum(r.evaluation_score for r in recs) / len(recs)
        return {
            'total_models': len(recs),
            'approved_count': approved,
            'avg_score': round(avg_score, 3)
        }
