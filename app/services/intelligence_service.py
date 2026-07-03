"""
IntelligenceService - Phase 27 Global Security Intelligence Network.
Ingests, normalizes, and correlates global threat intelligence reports.
Simulation-only: no external API calls.
"""
from app.extensions import db
from app.models.intelligence_report import IntelligenceReport
from app.models.intelligence_source import IntelligenceSource


class IntelligenceService:
    @staticmethod
    def ingest(data: dict, source_id: int = None, organization_id: int = None) -> IntelligenceReport:
        """Normalize and store a raw intelligence payload as an IntelligenceReport."""
        normalized = IntelligenceService.normalize(data)
        report = IntelligenceReport(
            title=normalized.get('title', 'Untitled Report'),
            severity=normalized.get('severity', 'medium'),
            source=normalized.get('source', 'unknown'),
            confidence=float(normalized.get('confidence', 0.7)),
            summary=normalized.get('summary', ''),
            organization_id=organization_id,
        )
        db.session.add(report)
        db.session.commit()
        return report

    @staticmethod
    def normalize(raw: dict) -> dict:
        """Standardize raw intelligence into a canonical format."""
        severity_map = {'info': 'low', 'warning': 'medium', 'alert': 'high', 'critical': 'critical'}
        severity = raw.get('severity', raw.get('level', 'medium')).lower()
        severity = severity_map.get(severity, severity)

        confidence = float(raw.get('confidence', raw.get('score', 0.7)))
        confidence = max(0.0, min(1.0, confidence))

        return {
            'title': str(raw.get('title', raw.get('name', 'Unknown Intelligence'))),
            'severity': severity,
            'source': str(raw.get('source', raw.get('provider', 'unknown'))),
            'confidence': confidence,
            'summary': str(raw.get('summary', raw.get('description', ''))),
        }

    @staticmethod
    def correlate(report_id: int) -> list:
        """Find related IntelligenceReports with matching severity."""
        report = db.session.get(IntelligenceReport, report_id)
        if not report:
            return []
        related = IntelligenceReport.query.filter(
            IntelligenceReport.severity == report.severity,
            IntelligenceReport.id != report_id,
        ).limit(10).all()
        return [r.to_dict() for r in related]

    @staticmethod
    def list_reports(org_id: int = None) -> list:
        """Return all intelligence reports, optionally filtered by org."""
        q = IntelligenceReport.query
        if org_id:
            q = IntelligenceReport.tenant_filter(q, org_id)
        return q.order_by(IntelligenceReport.created_at.desc()).all()
