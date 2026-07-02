"""
SIEM Service — Phase 18 SOC Platform.
Event ingestion, normalization, correlation, and alert generation (simulation only).
"""
import datetime
import json
import random
from app.extensions import db
from app.models.alert import Alert, ALERT_EVENT_TYPES, ALERT_SEVERITIES


# Common normalized event schema field names
NORMALIZED_SCHEMA = {
    'timestamp', 'event_type', 'source_ip', 'dest_ip',
    'source_port', 'dest_port', 'user', 'host', 'action',
    'outcome', 'severity', 'raw'
}

# Vendor field → normalized field mappings
_VENDOR_FIELD_MAP = {
    # Windows/Sysmon
    'SourceIp': 'source_ip',
    'DestinationIp': 'dest_ip',
    'SourcePort': 'source_port',
    'DestinationPort': 'dest_port',
    'User': 'user',
    'Computer': 'host',
    # AWS CloudTrail
    'sourceIPAddress': 'source_ip',
    'userIdentity': 'user',
    'eventName': 'action',
    'errorCode': 'outcome',
    # Generic
    'src_ip': 'source_ip',
    'dst_ip': 'dest_ip',
    'username': 'user',
    'hostname': 'host',
    'status': 'outcome',
}

# Correlation thresholds (simulated)
_CORRELATION_THRESHOLD = 2   # min events to trigger alert


class SIEMService:

    # -------------------------------------------------------------------------
    # Event Ingestion
    # -------------------------------------------------------------------------

    @staticmethod
    def ingest_event(event_type: str, data: dict, org_id: int = None) -> dict:
        """
        Ingest a raw log event. Normalizes it and stores in memory for correlation.
        Returns the normalized event dict.
        """
        if event_type not in ALERT_EVENT_TYPES:
            event_type = 'other'

        normalized = SIEMService.normalize_event(data)
        normalized['event_type'] = event_type
        normalized['org_id'] = org_id
        normalized['ingested_at'] = datetime.datetime.utcnow().isoformat()

        return normalized

    @staticmethod
    def normalize_event(raw: dict) -> dict:
        """
        Map vendor-specific field names to the normalized common schema.
        Unknown fields are passed through under their original names.
        """
        normalized = {'raw': json.dumps(raw)}
        for vendor_key, value in raw.items():
            norm_key = _VENDOR_FIELD_MAP.get(vendor_key, vendor_key.lower())
            normalized[norm_key] = value
        # Ensure required fields exist
        normalized.setdefault('timestamp', datetime.datetime.utcnow().isoformat())
        normalized.setdefault('source_ip', None)
        normalized.setdefault('dest_ip', None)
        normalized.setdefault('severity', 'medium')
        return normalized

    # -------------------------------------------------------------------------
    # Correlation & Alert Generation
    # -------------------------------------------------------------------------

    @staticmethod
    def correlate(events: list, org_id: int = None) -> list:
        """
        Simulate event correlation — group events by source IP into clusters.
        Clusters exceeding the threshold generate alerts.
        Returns list of generated Alert objects.
        """
        # Group by source_ip
        groups = {}
        for ev in events:
            key = ev.get('source_ip') or 'unknown'
            groups.setdefault(key, []).append(ev)

        alerts = []
        for src_ip, evs in groups.items():
            if len(evs) >= _CORRELATION_THRESHOLD:
                event_type = evs[0].get('event_type', 'other')
                severity = SIEMService._compute_severity(evs)
                alert = SIEMService.generate_alert(
                    title=f"Correlated activity from {src_ip} ({len(evs)} events)",
                    severity=severity,
                    event=evs[0],
                    org_id=org_id,
                )
                alerts.append(alert)
        return alerts

    @staticmethod
    def generate_alert(title: str, severity: str, event: dict,
                       org_id: int = None) -> Alert:
        """Persist a new SIEM Alert from a correlated event cluster."""
        if severity not in ALERT_SEVERITIES:
            severity = 'medium'

        alert = Alert(
            title=title,
            severity=severity,
            event_type=event.get('event_type', 'other'),
            source_ip=event.get('source_ip'),
            dest_ip=event.get('dest_ip'),
            source_port=event.get('source_port'),
            dest_port=event.get('dest_port'),
            raw_event=event.get('raw', ''),
            organization_id=org_id,
        )
        db.session.add(alert)
        db.session.commit()
        return alert

    @staticmethod
    def _compute_severity(events: list) -> str:
        """Determine highest severity across a correlated event group."""
        order = ['info', 'low', 'medium', 'high', 'critical']
        highest = 0
        for ev in events:
            sev = ev.get('severity', 'medium')
            idx = order.index(sev) if sev in order else 2
            highest = max(highest, idx)
        return order[highest]

    # -------------------------------------------------------------------------
    # Alert Management
    # -------------------------------------------------------------------------

    @staticmethod
    def list_alerts(org_id: int = None, status: str = None, severity: str = None):
        q = Alert.query
        if org_id:
            q = q.filter_by(organization_id=org_id)
        if status:
            q = q.filter_by(status=status)
        if severity:
            q = q.filter_by(severity=severity)
        return q.order_by(Alert.created_at.desc()).all()

    @staticmethod
    def get_alert(alert_id: int) -> Alert:
        return db.session.get(Alert, alert_id)

    @staticmethod
    def update_alert(alert_id: int, **kwargs) -> Alert:
        alert = db.session.get(Alert, alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")
        for key, val in kwargs.items():
            if hasattr(alert, key):
                setattr(alert, key, val)
        db.session.commit()
        return alert

    @staticmethod
    def assign_alert(alert_id: int, analyst_id: int) -> Alert:
        alert = db.session.get(Alert, alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")
        alert.assigned_to = analyst_id
        alert.assigned_at = datetime.datetime.utcnow()
        alert.status = 'acknowledged'
        db.session.commit()
        return alert
