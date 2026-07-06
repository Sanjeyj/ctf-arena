"""
OperationsTimelineService - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Maintains chronological event logs and incident timelines, with stable sorting and replaying capabilities.
"""
from app.extensions import db
from app.models.operations_timeline_event import OperationsTimelineEvent
from app.models.operational_incident import OperationalIncident
import datetime
import json


class OperationsTimelineService:
    @staticmethod
    def record_event(incident_id: int, event_type: str, severity: str, description: str, source_service: str, org_id: int, score_delta: float = 0.0, metadata_json: dict = None) -> OperationsTimelineEvent:
        """Log a new operational event to the tenant operations ledger."""
        # Enforce boundary if incident is specified
        if incident_id:
            inc = db.session.get(OperationalIncident, incident_id)
            if not inc or inc.organization_id != org_id:
                incident_id = None

        evt = OperationsTimelineEvent(
            incident_id=incident_id,
            event_type=event_type,
            severity=severity,
            description=description,
            source_service=source_service,
            score_delta=score_delta,
            event_time=datetime.datetime.utcnow(),
            metadata_json=json.dumps(metadata_json) if metadata_json else None,
            organization_id=org_id
        )
        db.session.add(evt)
        db.session.commit()
        return evt

    @staticmethod
    def get_timeline(org_id: int, limit: int = 100) -> list:
        """Retrieve recent events in descending chronological order, with ID secondary sorting for stability."""
        return OperationsTimelineEvent.query.filter_by(organization_id=org_id)\
            .order_by(OperationsTimelineEvent.event_time.desc(), OperationsTimelineEvent.id.desc())\
            .limit(limit).all()

    @staticmethod
    def replay(org_id: int) -> list:
        """Retrieve all events in ascending chronological order for timeline playback."""
        return OperationsTimelineEvent.query.filter_by(organization_id=org_id)\
            .order_by(OperationsTimelineEvent.event_time.asc(), OperationsTimelineEvent.id.asc()).all()

    @staticmethod
    def compare_incidents(incident_id_1: int, incident_id_2: int, org_id: int) -> dict:
        """Compare progression events of two incidents."""
        inc1 = db.session.get(OperationalIncident, incident_id_1)
        inc2 = db.session.get(OperationalIncident, incident_id_2)

        if not inc1 or not inc2 or inc1.organization_id != org_id or inc2.organization_id != org_id:
            return {}

        evts1 = OperationsTimelineEvent.query.filter_by(incident_id=incident_id_1, organization_id=org_id)\
            .order_by(OperationsTimelineEvent.event_time.asc(), OperationsTimelineEvent.id.asc()).all()
        evts2 = OperationsTimelineEvent.query.filter_by(incident_id=incident_id_2, organization_id=org_id)\
            .order_by(OperationsTimelineEvent.event_time.asc(), OperationsTimelineEvent.id.asc()).all()

        dur1 = (inc1.resolved_at - inc1.started_at).total_seconds() if inc1.resolved_at else 0.0
        dur2 = (inc2.resolved_at - inc2.started_at).total_seconds() if inc2.resolved_at else 0.0

        return {
            'incident_1': {
                'title': inc1.title,
                'events_count': len(evts1),
                'duration_seconds': round(dur1, 1),
                'events': [e.to_dict() for e in evts1]
            },
            'incident_2': {
                'title': inc2.title,
                'events_count': len(evts2),
                'duration_seconds': round(dur2, 1),
                'events': [e.to_dict() for e in evts2]
            }
        }

    @staticmethod
    def calculate_recovery_delta(incident_id: int, org_id: int) -> float:
        """Determine time delta in seconds between incident start and resolution timeline milestones."""
        incident = db.session.get(OperationalIncident, incident_id)
        if not incident or incident.organization_id != org_id:
            return 0.0

        if incident.resolved_at:
            return round((incident.resolved_at - incident.started_at).total_seconds(), 2)

        # Fallback to checking start and resolution events in timeline
        start_evt = OperationsTimelineEvent.query.filter_by(
            incident_id=incident_id, event_type='incident_start', organization_id=org_id
        ).order_by(OperationsTimelineEvent.event_time.asc()).first()

        res_evt = OperationsTimelineEvent.query.filter_by(
            incident_id=incident_id, event_type='resolution', organization_id=org_id
        ).order_by(OperationsTimelineEvent.event_time.desc()).first()

        if start_evt and res_evt:
            return round((res_evt.event_time - start_evt.event_time).total_seconds(), 2)

        return 0.0

    @staticmethod
    def timeline_summary(org_id: int) -> dict:
        """Provide metrics breakdown for timeline logs."""
        evts = OperationsTimelineEvent.query.filter_by(organization_id=org_id).all()
        if not evts:
            return {
                'total_events': 0,
                'alerts_count': 0,
                'incident_milestones': 0,
                'total_impact_delta': 0.0
            }

        alerts = sum(1 for e in evts if e.event_type == 'alert')
        milestones = sum(1 for e in evts if e.event_type in ['incident_start', 'resolution'])
        total_delta = sum(e.score_delta for e in evts)

        return {
            'total_events': len(evts),
            'alerts_count': alerts,
            'incident_milestones': milestones,
            'total_impact_delta': round(total_delta, 2)
        }
