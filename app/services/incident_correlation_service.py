"""
IncidentCorrelationService - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Correlates telemetry alerts, trace signals, and service health anomalies into incident logs.
"""
from app.extensions import db
from app.models.operational_incident import OperationalIncident
from app.models.platform_service import PlatformService
from app.models.operations_timeline_event import OperationsTimelineEvent
from app.services.hook_service import HookService
import datetime
import json


class IncidentCorrelationService:
    @staticmethod
    def create_incident(title: str, severity: str, source_module: str, affected_services_list: list, root_cause_summary: str, impact_summary: str, org_id: int) -> OperationalIncident:
        """Create a platform incident, executing hooks and establishing tenant boundaries."""
        # Hook dispatch with potential parameter mutation
        hook_results = HookService.trigger_hook(
            'before_incident_correlation',
            title=title,
            severity=severity,
            source_module=source_module,
            affected_services_list=affected_services_list,
            root_cause_summary=root_cause_summary,
            impact_summary=impact_summary,
            org_id=org_id
        )
        for res in hook_results:
            if isinstance(res, dict):
                if 'title' in res:
                    title = res['title']
                if 'severity' in res:
                    severity = res['severity']
                if 'affected_services_list' in res:
                    affected_services_list = res['affected_services_list']
                if 'root_cause_summary' in res:
                    root_cause_summary = res['root_cause_summary']

        # Enforce tenant boundaries on affected services
        verified_services = []
        for sname in affected_services_list:
            srv = PlatformService.query.filter_by(service_name=sname, organization_id=org_id).first()
            if srv:
                verified_services.append(sname)

        incident = OperationalIncident(
            title=title,
            severity=severity,
            status='active',
            source_module=source_module,
            affected_services_json=json.dumps(verified_services),
            root_cause_summary=root_cause_summary,
            impact_summary=impact_summary,
            started_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(incident)
        db.session.commit()

        # Log timeline event
        timeline_evt = OperationsTimelineEvent(
            incident_id=incident.id,
            event_type='incident_start',
            severity=severity,
            description=f"Incident opened: {title}",
            source_service=source_module,
            score_delta=-10.0 if severity == 'critical' else -5.0,
            event_time=datetime.datetime.utcnow(),
            metadata_json=json.dumps({'source_module': source_module, 'services': verified_services}),
            organization_id=org_id
        )
        db.session.add(timeline_evt)
        db.session.commit()

        HookService.trigger_hook('after_incident_correlation', incident=incident)

        return incident

    @staticmethod
    def correlate_signals(incident_id: int, telemetry_metric_ids: list, trace_ids: list, org_id: int) -> dict:
        """Correlate metrics and traces to an active incident, creating timeline entries."""
        incident = db.session.get(OperationalIncident, incident_id)
        if not incident or incident.organization_id != org_id:
            return {}

        # Log correlation timeline event
        correlations = {
            'telemetry_metric_ids': telemetry_metric_ids,
            'trace_ids': trace_ids
        }
        timeline_evt = OperationsTimelineEvent(
            incident_id=incident_id,
            event_type='correlation',
            severity='info',
            description=f"Correlated {len(telemetry_metric_ids)} metrics and {len(trace_ids)} traces to incident.",
            source_service='IncidentCorrelationService',
            score_delta=0.0,
            event_time=datetime.datetime.utcnow(),
            metadata_json=json.dumps(correlations),
            organization_id=org_id
        )
        db.session.add(timeline_evt)

        # Update root cause summary with correlated info
        incident.root_cause_summary = f"{incident.root_cause_summary or ''} [Correlated Signals: Metrics={telemetry_metric_ids}, Traces={trace_ids}]"
        db.session.commit()

        return correlations

    @staticmethod
    def attach_service(incident_id: int, platform_service_id: int, org_id: int) -> OperationalIncident:
        """Attach a registered platform service to the affected services list of an incident."""
        incident = db.session.get(OperationalIncident, incident_id)
        srv = db.session.get(PlatformService, platform_service_id)
        if not incident or not srv or incident.organization_id != org_id or srv.organization_id != org_id:
            return None

        services = json.loads(incident.affected_services_json) if incident.affected_services_json else []
        if srv.service_name not in services:
            services.append(srv.service_name)
            incident.affected_services_json = json.dumps(services)

            # Log timeline event
            timeline_evt = OperationsTimelineEvent(
                incident_id=incident_id,
                event_type='mitigation',
                severity='warning',
                description=f"Service '{srv.service_name}' attached to incident.",
                source_service='IncidentCorrelationService',
                score_delta=-2.0,
                event_time=datetime.datetime.utcnow(),
                metadata_json=json.dumps({'platform_service_id': platform_service_id}),
                organization_id=org_id
            )
            db.session.add(timeline_evt)
            db.session.commit()

        return incident

    @staticmethod
    def calculate_impact(incident_id: int, org_id: int) -> float:
        """Calculate severity/impact score based on the number of affected critical services."""
        incident = db.session.get(OperationalIncident, incident_id)
        if not incident or incident.organization_id != org_id:
            return 0.0

        services = json.loads(incident.affected_services_json) if incident.affected_services_json else []
        impact_score = 0.0

        # Severity base weight
        base_weights = {'low': 10.0, 'medium': 25.0, 'high': 50.0, 'critical': 80.0}
        impact_score += base_weights.get(incident.severity.lower(), 25.0)

        for sname in services:
            srv = PlatformService.query.filter_by(service_name=sname, organization_id=org_id).first()
            if srv:
                # Criticality multiplier
                crit_multiplier = {'low': 1.1, 'medium': 1.3, 'high': 1.5, 'critical': 2.0}
                impact_score *= crit_multiplier.get(srv.criticality.lower(), 1.3)

        return round(min(100.0, impact_score), 2)

    @staticmethod
    def suggest_root_cause(incident_id: int, org_id: int) -> str:
        """Suggest root cause based on correlated signals inside the incident description."""
        incident = db.session.get(OperationalIncident, incident_id)
        if not incident or incident.organization_id != org_id:
            return "No incident found"

        # Check if there are correlated signals in the summary
        if "Correlated Signals" in (incident.root_cause_summary or ""):
            return "Correlated anomalies detected in recent telemetry metrics and trace latency records."
        return "Insufficient telemetry signals correlated to formulate root cause automatically."

    @staticmethod
    def resolve_incident(incident_id: int, org_id: int) -> OperationalIncident:
        """Mark incident resolved."""
        incident = db.session.get(OperationalIncident, incident_id)
        if not incident or incident.organization_id != org_id:
            return None

        incident.status = 'resolved'
        incident.resolved_at = datetime.datetime.utcnow()

        # Log timeline event
        timeline_evt = OperationsTimelineEvent(
            incident_id=incident_id,
            event_type='resolution',
            severity='info',
            description="Incident resolved successfully.",
            source_service='IncidentCorrelationService',
            score_delta=10.0,
            event_time=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(timeline_evt)
        db.session.commit()

        return incident

    @staticmethod
    def incident_summary(org_id: int) -> dict:
        """Report statistics on incidents."""
        incidents = OperationalIncident.query.filter_by(organization_id=org_id).all()
        if not incidents:
            return {
                'total_incidents': 0,
                'active_count': 0,
                'resolved_count': 0,
                'avg_mttr_minutes': 0.0
            }

        active = sum(1 for i in incidents if i.status == 'active')
        resolved = sum(1 for i in incidents if i.status == 'resolved')

        # Calculate Mean Time To Resolution (MTTR)
        durations = []
        for i in incidents:
            if i.status == 'resolved' and i.resolved_at:
                dur = (i.resolved_at - i.started_at).total_seconds() / 60.0
                durations.append(dur)

        avg_mttr = sum(durations) / len(durations) if durations else 0.0

        return {
            'total_incidents': len(incidents),
            'active_count': active,
            'resolved_count': resolved,
            'avg_mttr_minutes': round(avg_mttr, 2)
        }
