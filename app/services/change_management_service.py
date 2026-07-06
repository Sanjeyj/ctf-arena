"""
ChangeManagementService - Phase 31 Cyber Platform Control Plane.
Tracks simulated platform configuration changes.
"""
from app.extensions import db
from app.models.change_record import ChangeRecord
from app.services.hook_service import HookService


class ChangeManagementService:
    @staticmethod
    def request_change(change_type: str, resource_type: str, resource_id: str, requested_by: str, org_id: int, rollback_plan: str = None) -> ChangeRecord:
        """Request a platform feature rollout change."""
        rec = ChangeRecord(
            change_type=change_type,
            resource_type=resource_type,
            resource_id=str(resource_id),
            requested_by=requested_by,
            approval_status='requested',
            risk_score=0.0,
            rollback_plan=rollback_plan,
            status='planned',
            organization_id=org_id
        )
        db.session.add(rec)
        db.session.commit()
        return rec

    @staticmethod
    def assess_risk(change_id: int, org_id: int) -> float:
        """Compute calculated risk score for change request based on type."""
        rec = db.session.get(ChangeRecord, change_id)
        if not rec or rec.organization_id != org_id:
            return 0.0
        
        # Simple simulated risk assessment math
        risk = 0.2
        if rec.change_type == 'policy_update':
            risk += 0.5
        elif rec.change_type == 'model_swap':
            risk += 0.3
        
        rec.risk_score = risk
        db.session.commit()
        return risk

    @staticmethod
    def approve(change_id: int, org_id: int) -> ChangeRecord:
        """Approve requested change."""
        rec = db.session.get(ChangeRecord, change_id)
        if not rec or rec.organization_id != org_id:
            return None
        rec.approval_status = 'approved'
        db.session.commit()
        return rec

    @staticmethod
    def simulate(change_id: int, org_id: int) -> ChangeRecord:
        """Simulate change execution, triggering before/after change simulation hooks."""
        rec = db.session.get(ChangeRecord, change_id)
        if not rec or rec.organization_id != org_id:
            return None

        # Trigger hook before simulation
        HookService.trigger_hook("before_change_simulation", change=rec)

        rec.status = 'simulated'
        db.session.commit()

        # Trigger hook after simulation
        HookService.trigger_hook("after_change_simulation", change=rec, outcome="success")

        return rec

    @staticmethod
    def rollback(change_id: int, org_id: int) -> ChangeRecord:
        """Rollback simulated change."""
        rec = db.session.get(ChangeRecord, change_id)
        if not rec or rec.organization_id != org_id:
            return None
        rec.status = 'rolled_back'
        db.session.commit()
        return rec

    @staticmethod
    def close(change_id: int, org_id: int) -> ChangeRecord:
        """Complete the change request workflow."""
        rec = db.session.get(ChangeRecord, change_id)
        if not rec or rec.organization_id != org_id:
            return None
        rec.status = 'completed'
        db.session.commit()
        return rec
