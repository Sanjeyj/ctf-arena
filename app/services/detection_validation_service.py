"""
DetectionValidationService - Phase 35 Continuous Security Validation.
Models detection rule coverage and logs gap detection metrics for Sigma/YARA rules.
"""
from app.extensions import db
from app.models.detection_validation import DetectionValidation
from app.services.hook_service import HookService
import datetime


class DetectionValidationService:
    @staticmethod
    def create_synthetic_signal(execution_id, detection_type, detection_reference, synthetic_signal_type, expected_detection, org_id):
        # Validate detection type parameter
        allowed_types = ['sigma', 'yara_metadata', 'ioc_match', 'anomaly_rule', 'correlation_rule']
        if detection_type not in allowed_types:
            raise ValueError(f"Invalid detection_type. Must be one of: {allowed_types}")

        hook_results = HookService.trigger_hook(
            'before_detection_validation',
            execution_id=execution_id,
            detection_type=detection_type,
            detection_reference=detection_reference,
            synthetic_signal_type=synthetic_signal_type,
            expected_detection=expected_detection,
            org_id=org_id
        )
        for res in hook_results:
            if isinstance(res, dict):
                detection_reference = res.get('detection_reference', detection_reference)
                expected_detection = res.get('expected_detection', expected_detection)

        val = DetectionValidation(
            execution_id=execution_id,
            detection_type=detection_type,
            detection_reference=detection_reference,
            synthetic_signal_type=synthetic_signal_type,
            expected_detection=expected_detection,
            detected=expected_detection,  # default to successful simulation
            confidence=1.0,
            latency_score=1.0,
            coverage_score=1.0,
            organization_id=org_id
        )
        db.session.add(val)
        db.session.commit()

        HookService.trigger_hook('after_detection_validation', validation_id=val.id, org_id=org_id)
        return val

    @staticmethod
    def evaluate_detection(validation_id, detected, latency_score, org_id):
        val = DetectionValidation.query.filter_by(id=validation_id, organization_id=org_id).first()
        if not val:
            return None
        val.detected = detected
        val.latency_score = latency_score
        val.coverage_score = 1.0 if detected else 0.0
        db.session.commit()
        return val

    @staticmethod
    def calculate_coverage(org_id):
        validations = DetectionValidation.query.filter_by(organization_id=org_id).all()
        if not validations:
            return 0.0
        detected = sum(1 for v in validations if v.detected)
        return round(detected / len(validations), 2)

    @staticmethod
    def calculate_latency_score(latency_seconds):
        if latency_seconds < 0:
            return 0.0
        return round(max(0.0, 1.0 - (latency_seconds / 300.0)), 2)

    @staticmethod
    def find_detection_gaps(org_id):
        validations = DetectionValidation.query.filter_by(organization_id=org_id).all()
        gaps = []
        for v in validations:
            if v.expected_detection and not v.detected:
                gaps.append({
                    "id": v.id,
                    "detection_reference": v.detection_reference,
                    "detection_type": v.detection_type,
                    "synthetic_signal_type": v.synthetic_signal_type
                })
        return gaps

    @staticmethod
    def detection_summary(org_id):
        validations = DetectionValidation.query.filter_by(organization_id=org_id).all()
        if not validations:
            return {"total_validations": 0, "avg_coverage": 0.0, "avg_latency_score": 0.0}

        avg_cov = sum(v.coverage_score for v in validations) / len(validations)
        avg_lat = sum(v.latency_score for v in validations) / len(validations)

        return {
            "total_validations": len(validations),
            "avg_coverage": round(avg_cov, 2),
            "avg_latency_score": round(avg_lat, 2)
        }
