"""
ControlCoverageService - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
Aggregates control coverage mapping and computes defensive gaps.
"""
from app.extensions import db
from app.models.control_coverage_map import ControlCoverageMap
from app.models.control_validation import ControlValidation
from app.services.hook_service import HookService
import datetime


class ControlCoverageService:

    @staticmethod
    def map_control(control_ref, resource_type, resource_id, coverage_score, effectiveness_score, status, org_id):
        # Hook mutation check
        hook_results = HookService.trigger_hook(
            'before_control_coverage_evaluation',
            control_ref=control_ref,
            resource_type=resource_type,
            resource_id=resource_id,
            coverage_score=coverage_score,
            effectiveness_score=effectiveness_score,
            status=status,
            org_id=org_id
        )
        for res in hook_results:
            if isinstance(res, dict):
                coverage_score = res.get('coverage_score', coverage_score)
                effectiveness_score = res.get('effectiveness_score', effectiveness_score)

        cc = ControlCoverageMap(
            control_reference=control_ref,
            resource_type=resource_type,
            resource_id=resource_id,
            coverage_score=coverage_score,
            effectiveness_score=effectiveness_score,
            validation_status=status,
            last_validated_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(cc)
        db.session.commit()

        HookService.trigger_hook('after_control_coverage_evaluation', map_id=cc.id, org_id=org_id)
        return cc

    @staticmethod
    def calculate_coverage(control_ref, org_id):
        validations = ControlValidation.query.filter_by(control_reference=control_ref, organization_id=org_id).all()
        if not validations:
            return 0.0

        # Calculate coverage ratio: passed tests vs total validations
        valid_count = sum(1 for v in validations if v.status == 'passed')
        return round(valid_count / len(validations), 2)

    @staticmethod
    def calculate_effectiveness(control_ref, org_id):
        validations = ControlValidation.query.filter_by(control_reference=control_ref, organization_id=org_id).all()
        if not validations:
            return 0.0

        # Effectiveness matches the average percentage score of validations
        total_score = sum(v.effectiveness_score for v in validations if v.effectiveness_score is not None)
        total_count = sum(1 for v in validations if v.effectiveness_score is not None)
        if total_count == 0:
            return 0.5  # fallback default
        return round(total_score / total_count, 2)

    @staticmethod
    def find_coverage_gaps(org_id):
        maps = ControlCoverageMap.query.filter_by(organization_id=org_id).all()
        gaps = []
        for m in maps:
            if m.coverage_score < 0.5 or m.effectiveness_score < 0.5:
                gaps.append({
                    "id": m.id,
                    "control_reference": m.control_reference,
                    "coverage_score": m.coverage_score,
                    "effectiveness_score": m.effectiveness_score
                })
        return gaps

    @staticmethod
    def apply_validation_result(control_ref, resource_type, resource_id, status, score, org_id):
        cc = ControlCoverageMap.query.filter_by(
            control_reference=control_ref,
            resource_type=resource_type,
            resource_id=resource_id,
            organization_id=org_id
        ).first()

        if not cc:
            cc = ControlCoverageMap(
                control_reference=control_ref,
                resource_type=resource_type,
                resource_id=resource_id,
                organization_id=org_id
            )
            db.session.add(cc)

        cc.validation_status = status
        # Normalize score to float (0.0 to 1.0)
        cc.effectiveness_score = round(score / 100.0, 2)
        cc.coverage_score = 1.0 if status in ['passed', 'valid'] else 0.5
        cc.last_validated_at = datetime.datetime.utcnow()
        db.session.commit()
        return cc

    @staticmethod
    def coverage_summary(org_id):
        maps = ControlCoverageMap.query.filter_by(organization_id=org_id).all()
        if not maps:
            return {"total_mapped": 0, "avg_coverage": 0.0, "avg_effectiveness": 0.0}

        avg_cov = sum(m.coverage_score for m in maps) / len(maps)
        avg_eff = sum(m.effectiveness_score for m in maps) / len(maps)

        return {
            "total_mapped": len(maps),
            "avg_coverage": round(avg_cov, 2),
            "avg_effectiveness": round(avg_eff, 2)
        }
