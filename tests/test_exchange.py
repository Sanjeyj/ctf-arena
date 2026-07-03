"""
Unit and Integration tests for Step 3 & 4 Global Threat Exchange.
Contains 11 test cases.
"""
import pytest
import json
import datetime
from app.extensions import db
from app.models.shared_ioc import SharedIOC
from app.models.warehouse_event import WarehouseEvent
from app.models.warehouse_metric import WarehouseMetric
from app.models.organization import Organization
from app.services.threat_exchange_service import ThreatExchangeService
from app.services.warehouse_service import WarehouseService
from app.research.routes import create_jwt

@pytest.fixture
def exchange_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(SharedIOC).delete()
        db.session.query(WarehouseEvent).delete()
        db.session.query(WarehouseMetric).delete()
        db.session.commit()

        org = Organization(name="Exchange Org", slug="exchange-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        ioc = SharedIOC(value="malicious-domain.com", ioc_type="domain", trust_level="verified", shared_by_org_id=org.id, organization_id=org.id)
        db.session.add(ioc)
        db.session.commit()

        we = WarehouseEvent(event_type="phishing_attack", source="CTI", severity="high", payload_json='{"target": "finance"}', timestamp=datetime.datetime.utcnow(), organization_id=org.id)
        db.session.add(we)
        db.session.commit()

        wm = WarehouseMetric(metric_name="risk_reduction_pct", value=15.5, timestamp=datetime.datetime.utcnow(), organization_id=org.id)
        db.session.add(wm)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "exchange_admin"}, secret)

        yield {
            "org": org,
            "ioc": ioc,
            "we": we,
            "wm": wm,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_shared_ioc_creation(app, exchange_setup):
    """Test 1: SharedIOC threat parameters registry storage."""
    with app.app_context():
        i = db.session.get(SharedIOC, exchange_setup['ioc'].id)
        assert i.value == "malicious-domain.com"
        assert i.trust_level == "verified"

def test_shared_ioc_repr(app, exchange_setup):
    """Test 2: SharedIOC model representation string."""
    with app.app_context():
        i = db.session.get(SharedIOC, exchange_setup['ioc'].id)
        assert "malicious-domain.com" in repr(i)

def test_threat_exchange_publish_ioc(app, exchange_setup):
    """Test 3: ThreatExchangeService publishes new verified IOC elements."""
    with app.app_context():
        org = exchange_setup['org']
        ioc = ThreatExchangeService.share_ioc("192.168.1.100", "IP", "trusted", org_id=org.id)
        assert ioc.id is not None
        assert ioc.value == "192.168.1.100"

def test_threat_exchange_ioc_validation(app):
    """Test 4: ThreatExchangeService validates indicator values formats."""
    assert ThreatExchangeService.validate_ioc("bad-domain.net") is True
    assert ThreatExchangeService.validate_ioc("") is False

def test_warehouse_event_creation(app, exchange_setup):
    """Test 5: WarehouseEvent attributes database storage."""
    with app.app_context():
        we = db.session.get(WarehouseEvent, exchange_setup['we'].id)
        assert we.event_type == "phishing_attack"
        assert we.source == "CTI"

def test_warehouse_event_repr(app, exchange_setup):
    """Test 6: WarehouseEvent model representation string."""
    with app.app_context():
        we = db.session.get(WarehouseEvent, exchange_setup['we'].id)
        assert "phishing_attack" in repr(we)

def test_warehouse_metric_creation(app, exchange_setup):
    """Test 7: WarehouseMetric calculated indices tracking storage."""
    with app.app_context():
        wm = db.session.get(WarehouseMetric, exchange_setup['wm'].id)
        assert wm.metric_name == "risk_reduction_pct"
        assert wm.value == 15.5

def test_warehouse_metric_repr(app, exchange_setup):
    """Test 8: WarehouseMetric model representation string."""
    with app.app_context():
        wm = db.session.get(WarehouseMetric, exchange_setup['wm'].id)
        assert "risk_reduction_pct" in repr(wm)

def test_warehouse_event_aggregations(app, exchange_setup):
    """Test 9: WarehouseService aggregates historical data logs by source."""
    with app.app_context():
        org = exchange_setup['org']
        events = WarehouseService.aggregate_events("CTI", org_id=org.id)
        assert len(events) == 1

def test_warehouse_metric_trends(app, exchange_setup):
    """Test 10: WarehouseService computes historical metric trend logs."""
    with app.app_context():
        org = exchange_setup['org']
        # Add another metric
        WarehouseService.store_metric("risk_reduction_pct", 18.0, org_id=org.id)
        trends = WarehouseService.analyze_trends("risk_reduction_pct", org_id=org.id)
        assert len(trends) == 2
        assert trends[0].value == 18.0

def test_exchange_rest_endpoint(client, exchange_setup):
    """Test 11: GET /api/v1/exchange lists registered shared indicators."""
    headers = exchange_setup['headers']
    resp = client.get('/api/v1/exchange', headers=headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['count'] == 1
    assert data['shared_iocs'][0]['value'] == "malicious-domain.com"
