"""
ValidationRegressionService - Phase 35 Continuous Security Validation.
Tracks performance deltas, classifies drops in scores, and handles regression alerts.
"""
from app.extensions import db
from app.models.validation_regression import ValidationRegression
from app.services.hook_service import HookService
import datetime


class ValidationRegressionService:
    @staticmethod
    def compare_results(resource_type, resource_id, previous_score, current_score, org_id):
        # Simply returns the numeric drop
        return max(0.0, previous_score - current_score)

    @staticmethod
    def detect_regression(resource_type, resource_id, previous_score, current_score, org_id):
        delta = previous_score - current_score

        hook_results = HookService.trigger_hook(
            'before_regression_evaluation',
            resource_type=resource_type,
            resource_id=resource_id,
            previous_score=previous_score,
            current_score=current_score,
            org_id=org_id
        )
        for res in hook_results:
            if isinstance(res, dict):
                current_score = res.get('current_score', current_score)
                delta = previous_score - current_score

        severity = ValidationRegressionService.classify_regression(delta)
        if not severity:
            return None

        reg = ValidationRegression(
            resource_type=resource_type,
            resource_id=resource_id,
            metric_type='score',
            previous_score=previous_score,
            current_score=current_score,
            regression_delta=round(delta, 2),
            severity=severity,
            status='open',
            detected_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(reg)
        db.session.commit()

        HookService.trigger_hook('after_regression_evaluation', regression_id=reg.id, org_id=org_id)
        return reg

    @staticmethod
    def classify_regression(delta):
        if delta < 5.0:
            return None
        elif delta < 10.0:
            return 'low'
        elif delta < 20.0:
            return 'medium'
        elif delta < 30.0:
            return 'high'
        else:
            return 'critical'

    @staticmethod
    def create_regression_record(resource_type, resource_id, metric_type, previous_score, current_score, severity, org_id):
        delta = previous_score - current_score
        reg = ValidationRegression(
            resource_type=resource_type,
            resource_id=resource_id,
            metric_type=metric_type,
            previous_score=previous_score,
            current_score=current_score,
            regression_delta=round(delta, 2),
            severity=severity,
            status='open',
            detected_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(reg)
        db.session.commit()
        return reg

    @staticmethod
    def resolve_regression(regression_id, org_id):
        reg = ValidationRegression.query.filter_by(id=regression_id, organization_id=org_id).first()
        if not reg:
            return None
        reg.status = 'resolved'
        db.session.commit()
        return reg

    @staticmethod
    def regression_summary(org_id):
        records = ValidationRegression.query.filter_by(organization_id=org_id).all()
        return {
            "total_regressions": len(records),
            "open_count": sum(1 for r in records if r.status == 'open'),
            "resolved_count": sum(1 for r in records if r.status == 'resolved'),
            "critical_count": sum(1 for r in records if r.severity == 'critical')
        }
