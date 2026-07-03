"""
Unit and Integration tests for Step 1 Security Data Lake.
"""
import pytest
import json
from app.extensions import db
from app.models.security_event import SecurityEvent
from app.models.event_source import EventSource
from app.models.organization import Organization
from app.services.event_lake_service import EventLakeService
from app.research.routes import create_jwt

@pytest.fixture
def lake_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(SecurityEvent).delete()
        db.session.query(EventSource).delete()
        db.session.commit()

        org = Organization(name="Lake Org", slug="lake-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        source = EventSource(name="Agent Collector", source_type="Agents", status="active", organization_id=org.id)
        db.session.add(source)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "lake_admin"}, secret)

        yield {
            "org": org,
            "source": source,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_security_event_ingestion(app, lake_setup):
    """Test log normalization and ingestion."""
    with app.app_context():
        org = lake_setup['org']
        raw_log = {
            "type": "authentication",
            "severity": "High",
            "source": "Agents",
            "data": {"user": "attacker", "status": "failed"}
        }

        norm = EventLakeService.normalize(raw_log)
        assert norm['event_type'] == "authentication"
        assert norm['severity'] == "high"

        event = EventLakeService.ingest(norm, org_id=org.id)
        assert event.id is not None
        assert event.event_type == "authentication"
        assert event.source == "Agents"

def test_events_lake_aggregation(app, lake_setup):
    """Test aggregating security events by type filter."""
    with app.app_context():
        org = lake_setup['org']
        EventLakeService.ingest({"event_type": "network", "severity": "medium", "source": "SOC", "payload": {}}, org_id=org.id)
        EventLakeService.ingest({"event_type": "process", "severity": "low", "source": "CTI", "payload": {}}, org_id=org.id)

        net_events = EventLakeService.aggregate("network", org_id=org.id)
        assert len(net_events) == 1
        assert net_events[0].event_type == "network"

def test_events_lake_correlation(app, lake_setup):
    """Test correlating security events by source labels."""
    with app.app_context():
        org = lake_setup['org']
        EventLakeService.ingest({"event_type": "network", "severity": "medium", "source": "CTI", "payload": {}}, org_id=org.id)
        EventLakeService.ingest({"event_type": "process", "severity": "low", "source": "CTI", "payload": {}}, org_id=org.id)

        cti_events = EventLakeService.correlate("CTI", org_id=org.id)
        assert len(cti_events) == 2

def test_events_api_route(client, lake_setup):
    """Test GET /api/v1/events response."""
    headers = lake_setup['headers']
    org = lake_setup['org']

    with client.application.app_context():
        EventLakeService.ingest({"event_type": "network", "severity": "medium", "source": "SOC", "payload": {}}, org_id=org.id)

    resp = client.get(f'/api/v1/events?org_id={org.id}', headers=headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['count'] == 1
    assert data['events'][0]['event_type'] == "network"


def test_security_event_serialization(app, lake_setup):
    """Test SecurityEvent model serializes database columns correctly."""
    with app.app_context():
        org = lake_setup['org']
        event = EventLakeService.ingest({"event_type": "network", "severity": "low", "source": "SOC", "payload": {"foo": "bar"}}, org_id=org.id)
        ed = event.to_dict()
        assert ed['event_type'] == "network"
        assert ed['payload']['foo'] == "bar"


def test_event_source_serialization(app, lake_setup):
    """Test EventSource model database serialization."""
    with app.app_context():
        source = lake_setup['source']
        sd = source.to_dict()
        assert sd['name'] == "Agent Collector"
        assert sd['status'] == "active"


def test_lake_aggregate_empty(app):
    """Test EventLakeService aggregate returns empty list for unregistered types."""
    with app.app_context():
        res = EventLakeService.aggregate("non-existent-type")
        assert len(res) == 0


def test_lake_correlate_empty(app):
    """Test EventLakeService correlate returns empty list for unregistered sources."""
    with app.app_context():
        res = EventLakeService.correlate("non-existent-source")
        assert len(res) == 0

