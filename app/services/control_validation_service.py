"""
ControlValidationService - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Validates control effectiveness based on simulated validation checks and monitors regression history.
"""
from app.extensions import db
from app.models.control_validation import ControlValidation
from app.services.hook_service import HookService
import datetime


class ControlValidationService:
    @staticmethod
    def validate_control(control_reference: str, validation_type: str, expected_result: str, actual_result: str, effectiveness_score: float, org_id: int, evidence_id: int = None) -> ControlValidation:
        """Execute simulated control validation run, triggering wargame hooks."""
        # Hook fired before control validation
        HookService.trigger_hook("before_control_validation", reference=control_reference)

        status_str = 'passed'
        if effectiveness_score < 0.5:
            status_str = 'failed'
        elif effectiveness_score < 0.9:
            status_str = 'partially_effective'

        val = ControlValidation(
            control_reference=control_reference,
            validation_type=validation_type,
            expected_result=expected_result,
            actual_result=actual_result,
            effectiveness_score=max(0.0, min(1.0, effectiveness_score)),
            status=status_str,
            tested_at=datetime.datetime.utcnow(),
            evidence_record_id=evidence_id,
            organization_id=org_id
        )
        db.session.add(val)
        db.session.commit()

        # Hook fired after control validation
        HookService.trigger_hook("after_control_validation", validation=val)

        return val

    @staticmethod
    def calculate_effectiveness(validation_id: int, org_id: int) -> float:
        """Retrieve effectiveness metrics score."""
        val = db.session.get(ControlValidation, validation_id)
        if not val or val.organization_id != org_id:
            return 0.0
        return val.effectiveness_score

    @staticmethod
    def record_result(validation_id: int, status: str, org_id: int) -> ControlValidation:
        """Overwrite status result override."""
        val = db.session.get(ControlValidation, validation_id)
        if not val or val.organization_id != org_id:
            return None
        val.status = status
        db.session.commit()
        return val

    @staticmethod
    def detect_regression(control_reference: str, org_id: int) -> bool:
        """Compare current validation run score against history to detect regressions."""
        runs = (
            ControlValidation.query
            .filter_by(control_reference=control_reference, organization_id=org_id)
            .order_by(ControlValidation.tested_at.desc())
            .limit(2)
            .all()
        )
        if len(runs) < 2:
            return False
        # If current score is lower than previous score, regression detected
        return runs[0].effectiveness_score < runs[1].effectiveness_score

    @staticmethod
    def validation_summary(org_id: int) -> dict:
        """Retrieve overview numbers of validation checks."""
        runs = ControlValidation.query.filter_by(organization_id=org_id).all()
        if not runs:
            return {'total_tests': 0, 'failed_count': 0, 'avg_effectiveness': 1.0}
        failed = sum(1 for r in runs if r.status == 'failed')
        avg_eff = sum(r.effectiveness_score for r in runs) / len(runs)
        return {
            'total_tests': len(runs),
            'failed_count': failed,
            'avg_effectiveness': round(avg_eff, 2)
        }
