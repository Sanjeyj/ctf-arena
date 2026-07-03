"""
EventLake Service - Phase 22 Security Data Lake.
Handles ingestion, logs normalization, event parsing, aggregation, and correlation.
"""
import json
import datetime
from app.extensions import db
from app.models.security_event import SecurityEvent

class EventLakeService:

    @staticmethod
    def normalize(raw_data: dict) -> dict:
        """Standardize raw logs format keys."""
        normalized = {
            "event_type": raw_data.get("type") or raw_data.get("event_type") or "generic_event",
            "severity": (raw_data.get("severity") or "medium").lower(),
            "source": raw_data.get("source") or "SOC",
            "payload": raw_data.get("payload") or raw_data.get("data") or {}
        }
        return normalized

    @staticmethod
    def ingest(normalized_event: dict, org_id: int = None) -> SecurityEvent:
        event = SecurityEvent(
            event_type=normalized_event['event_type'],
            severity=normalized_event['severity'],
            source=normalized_event['source'],
            payload_json=json.dumps(normalized_event['payload']),
            timestamp=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(event)
        db.session.commit()
        return event

    @staticmethod
    def aggregate(event_type: str, org_id: int = None) -> list[SecurityEvent]:
        """Aggregate security events matching type filter."""
        q = SecurityEvent.query.filter_by(event_type=event_type)
        if org_id:
            q = q.filter_by(organization_id=org_id)
        return q.all()

    @staticmethod
    def correlate(source_label: str, org_id: int = None) -> list[SecurityEvent]:
        """Correlate security events collected from source."""
        q = SecurityEvent.query.filter_by(source=source_label)
        if org_id:
            q = q.filter_by(organization_id=org_id)
        return q.all()
