"""
DefenseEffectivenessService - Phase 35 Continuous Security Validation.
Computes effectiveness ratings across controls, detections, playbooks, resilience, and architecture.
"""
from app.extensions import db
from app.models.defense_effectiveness_metric import DefenseEffectivenessMetric
from app.services.control_coverage_service import ControlCoverageService
from app.services.detection_validation_service import DetectionValidationService
from app.services.playbook_validation_service import PlaybookValidationService
from app.services.architecture_service import ArchitectureService
# Safe import of resilience score model
try:
    from app.models.resilience_score import ResilienceScore
except ImportError:
    ResilienceScore = None
import datetime


class DefenseEffectivenessService:
    @staticmethod
    def calculate_control_effectiveness(org_id):
        summary = ControlCoverageService.coverage_summary(org_id)
        # Convert 0.0-1.0 effectiveness rating to 0-100 scale
        return summary.get("avg_effectiveness", 0.8) * 100.0

    @staticmethod
    def calculate_detection_effectiveness(org_id):
        summary = DetectionValidationService.detection_summary(org_id)
        return summary.get("avg_coverage", 0.8) * 100.0

    @staticmethod
    def calculate_playbook_effectiveness(org_id):
        summary = PlaybookValidationService.playbook_summary(org_id)
        return summary.get("avg_readiness", 0.8) * 100.0

    @staticmethod
    def calculate_resilience_effectiveness(org_id):
        if ResilienceScore:
            score = ResilienceScore.query.filter_by(organization_id=org_id).order_by(ResilienceScore.id.desc()).first()
            if score:
                return score.overall_score * 10.0 if score.overall_score <= 10.0 else score.overall_score
        return 80.0

    @staticmethod
    def calculate_architecture_effectiveness(org_id):
        summary = ArchitectureService.architecture_summary(org_id)
        total_b = summary.get("total_boundaries", 0)
        violations = summary.get("boundary_violations", 0)
        if total_b == 0:
            return 100.0
        return max(0.0, 1.0 - (violations / total_b)) * 100.0

    @staticmethod
    def calculate_composite_score(org_id):
        ctrl = DefenseEffectivenessService.calculate_control_effectiveness(org_id)
        det = DefenseEffectivenessService.calculate_detection_effectiveness(org_id)
        play = DefenseEffectivenessService.calculate_playbook_effectiveness(org_id)
        res = DefenseEffectivenessService.calculate_resilience_effectiveness(org_id)
        arch = DefenseEffectivenessService.calculate_architecture_effectiveness(org_id)

        # Composite score weighting
        composite = 0.25 * ctrl + 0.25 * det + 0.20 * play + 0.15 * res + 0.15 * arch
        composite = min(100.0, max(0.0, round(composite, 2)))

        # Fetch previous score to calculate trend/delta
        prev = DefenseEffectivenessMetric.query.filter_by(
            metric_type='composite', organization_id=org_id
        ).order_by(DefenseEffectivenessMetric.id.desc()).first()

        prev_score = prev.score if prev else composite
        delta = composite - prev_score
        trend = 'stable'
        if delta > 0.5:
            trend = 'improving'
        elif delta < -0.5:
            trend = 'declining'

        metric = DefenseEffectivenessMetric(
            metric_type='composite',
            score=composite,
            previous_score=prev_score,
            delta=round(delta, 2),
            trend=trend,
            measured_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(metric)
        db.session.commit()
        return metric

    @staticmethod
    def effectiveness_summary(org_id):
        ctrl = DefenseEffectivenessService.calculate_control_effectiveness(org_id)
        det = DefenseEffectivenessService.calculate_detection_effectiveness(org_id)
        play = DefenseEffectivenessService.calculate_playbook_effectiveness(org_id)
        res = DefenseEffectivenessService.calculate_resilience_effectiveness(org_id)
        arch = DefenseEffectivenessService.calculate_architecture_effectiveness(org_id)

        prev = DefenseEffectivenessMetric.query.filter_by(
            metric_type='composite', organization_id=org_id
        ).order_by(DefenseEffectivenessMetric.id.desc()).first()
        score = prev.score if prev else 80.0

        return {
            "control_effectiveness": round(ctrl, 2),
            "detection_effectiveness": round(det, 2),
            "playbook_readiness": round(play, 2),
            "resilience_effectiveness": round(res, 2),
            "architecture_effectiveness": round(arch, 2),
            "composite_score": round(score, 2)
        }

    @staticmethod
    def effectiveness_trend(org_id):
        metrics = DefenseEffectivenessMetric.query.filter_by(
            metric_type='composite', organization_id=org_id
        ).order_by(DefenseEffectivenessMetric.id.desc()).limit(10).all()
        return [m.to_dict() for m in reversed(metrics)]
