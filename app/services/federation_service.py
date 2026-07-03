"""
FederationService - Phase 27 Global Security Intelligence Network.
Handles cross-organization intelligence sharing and feed subscriptions.
Simulation-only: no live external org connections.
"""
from app.extensions import db
from app.models.intelligence_report import IntelligenceReport
from app.models.intelligence_source import IntelligenceSource


class FederationService:
    @staticmethod
    def share(report_id: int, target_org_id: int) -> dict:
        """Push an intelligence report to a partner organization."""
        report = db.session.get(IntelligenceReport, report_id)
        if not report:
            return {'shared': False, 'reason': f'Report {report_id} not found'}

        # Simulate sharing: create a copy attributed to target org
        shared = IntelligenceReport(
            title=f'[Shared] {report.title}',
            severity=report.severity,
            source=f'federated:{report.source}',
            confidence=round(report.confidence * 0.95, 3),  # slight confidence decay
            summary=report.summary,
            organization_id=target_org_id,
        )
        db.session.add(shared)
        db.session.commit()
        return {
            'shared': True,
            'original_report_id': report_id,
            'shared_report_id': shared.id,
            'target_org_id': target_org_id,
        }

    @staticmethod
    def subscribe(source_org_id: int, org_id: int) -> IntelligenceSource:
        """Subscribe an organization to a source org's intelligence feed."""
        existing = IntelligenceSource.query.filter_by(
            organization=str(source_org_id),
            organization_id=org_id,
        ).first()
        if existing:
            return existing
        source = IntelligenceSource(
            organization=str(source_org_id),
            source_type='federated',
            reputation=0.7,
            status='active',
            organization_id=org_id,
        )
        db.session.add(source)
        db.session.commit()
        return source

    @staticmethod
    def synchronize(org_id: int) -> dict:
        """Pull latest reports from all active federated subscriptions."""
        subscriptions = IntelligenceSource.query.filter_by(
            source_type='federated',
            status='active',
            organization_id=org_id,
        ).all()
        synced_count = 0
        for sub in subscriptions:
            # Simulate synchronization: count available reports from source
            available = IntelligenceReport.query.filter(
                IntelligenceReport.source.like(f'%{sub.organization}%')
            ).count()
            synced_count += available
        return {
            'org_id': org_id,
            'subscriptions': len(subscriptions),
            'synced_reports': synced_count,
            'status': 'synchronized',
        }
