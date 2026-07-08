"""
FindingService - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
Registers, updates, and deduplicates simulated vulnerability or misconfiguration findings.
"""
from app.extensions import db
from app.models.exposure_finding import ExposureFinding
from app.services.hook_service import HookService
import datetime


class FindingService:

    @staticmethod
    def validate_source(source_type):
        allowed = ["simulation", "synthetic_import", "control_gap", "sbom_metadata", "attestation_gap", "architecture_review"]
        if source_type not in allowed:
            raise ValueError(f"Live action or scanning source type '{source_type}' is strictly prohibited.")
        return True

    @staticmethod
    def create_finding(exposure_asset_id, finding_type, title, severity, likelihood, impact_score, confidence, status, source_type, metadata_json, org_id):
        FindingService.validate_source(source_type)

        # Hook mutation integration
        hook_results = HookService.trigger_hook(
            'before_exposure_evaluation',
            exposure_asset_id=exposure_asset_id,
            finding_type=finding_type,
            title=title,
            severity=severity,
            likelihood=likelihood,
            impact_score=impact_score,
            confidence=confidence,
            status=status,
            source_type=source_type,
            org_id=org_id
        )
        for res in hook_results:
            if isinstance(res, dict):
                title = res.get('title', title)
                severity = res.get('severity', severity)
                likelihood = res.get('likelihood', likelihood)

        finding = ExposureFinding(
            exposure_asset_id=exposure_asset_id,
            finding_type=finding_type,
            title=title,
            severity=severity,
            likelihood=likelihood,
            impact_score=impact_score,
            confidence=confidence,
            status=status,
            source_type=source_type,
            metadata_json=metadata_json,
            organization_id=org_id
        )
        db.session.add(finding)
        db.session.commit()

        HookService.trigger_hook(
            'after_exposure_evaluation',
            finding_id=finding.id,
            org_id=org_id
        )

        return finding

    @staticmethod
    def calculate_risk(finding_id, org_id):
        finding = ExposureFinding.query.filter_by(id=finding_id, organization_id=org_id).first()
        if not finding:
            return 0.0
        return finding.impact_score * finding.likelihood

    @staticmethod
    def update_status(finding_id, new_status, org_id):
        finding = ExposureFinding.query.filter_by(id=finding_id, organization_id=org_id).first()
        if finding:
            finding.status = new_status
            finding.last_seen_at = datetime.datetime.utcnow()
            db.session.commit()
            return finding
        return None

    @staticmethod
    def deduplicate(org_id):
        findings = ExposureFinding.query.filter_by(organization_id=org_id).order_by(ExposureFinding.id.asc()).all()
        seen = set()
        duplicates = []
        for f in findings:
            key = (f.exposure_asset_id, f.title)
            if key in seen:
                duplicates.append(f)
            else:
                seen.add(key)

        for d in duplicates:
            db.session.delete(d)
        db.session.commit()
        return len(duplicates)

    @staticmethod
    def finding_summary(org_id):
        findings = ExposureFinding.query.filter_by(organization_id=org_id, status='open').all()
        summary = {"low": 0, "medium": 0, "high": 0, "critical": 0, "total": len(findings)}
        for f in findings:
            sev = f.severity.lower()
            if sev in summary:
                summary[sev] += 1
        return summary
