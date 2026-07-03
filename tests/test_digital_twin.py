"""
Unit and Integration tests for Step 5 & 6 Digital Twin simulations.
Contains 11 test cases.
"""
import pytest
import json
from app.extensions import db
from app.models.digital_twin import DigitalTwin
from app.models.asset import Asset
from app.models.compliance_control import ComplianceControl
from app.models.governance_framework import GovernanceFramework
from app.models.organization import Organization
from app.services.digital_twin_service import DigitalTwinService
from app.research.routes import create_jwt

@pytest.fixture
def twin_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(DigitalTwin).delete()
        db.session.query(Asset).delete()
        db.session.query(ComplianceControl).delete()
        db.session.query(GovernanceFramework).delete()
        db.session.commit()

        org = Organization(name="Twin Org", slug="twin-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        twin = DigitalTwin(name="Ransomware-Twin-Primary", scenario_type="ransomware", impact_score=65.0, risk_score=70.0, organization_id=org.id)
        db.session.add(twin)
        db.session.commit()

        asset = Asset(name="Auth-Server", type_label="server", criticality=8, organization_id=org.id)
        db.session.add(asset)
        db.session.commit()

        fw = GovernanceFramework(name="NIST-CSF", organization_id=org.id)
        db.session.add(fw)
        db.session.commit()

        ctrl = ComplianceControl(framework_id=fw.id, control_code="PR.AC-1", status="failed", organization_id=org.id)
        db.session.add(ctrl)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "twin_admin"}, secret)

        yield {
            "org": org,
            "twin": twin,
            "asset": asset,
            "ctrl": ctrl,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_digital_twin_creation(app, twin_setup):
    """Test 1: DigitalTwin model database parameters insertion."""
    with app.app_context():
        t = db.session.get(DigitalTwin, twin_setup['twin'].id)
        assert t.name == "Ransomware-Twin-Primary"
        assert t.scenario_type == "ransomware"

def test_digital_twin_repr(app, twin_setup):
    """Test 2: DigitalTwin model representation string."""
    with app.app_context():
        t = db.session.get(DigitalTwin, twin_setup['twin'].id)
        assert "Ransomware-Twin-Primary" in repr(t)

def test_twin_service_simulate_asset_failure_impact(app, twin_setup):
    """Test 3: DigitalTwinService calculates asset failure impact score."""
    with app.app_context():
        asset = twin_setup['asset']
        res = DigitalTwinService.simulate_asset_failure(asset.id)
        assert res['scenario'] == "asset_failure"
        assert res['impact_score'] == 95.0 # criticality 8 * 10 + 15

def test_twin_service_simulate_asset_failure_missing(app):
    """Test 4: DigitalTwinService handles default asset failure simulation values."""
    with app.app_context():
        res = DigitalTwinService.simulate_asset_failure(9999)
        assert res['impact_score'] == 65.0 # default criticality 5 * 10 + 15

def test_twin_service_simulate_ransomware_propagation(app, twin_setup):
    """Test 5: DigitalTwinService models ransomware network spread factor risk."""
    with app.app_context():
        asset = twin_setup['asset']
        res = DigitalTwinService.simulate_ransomware(asset.id, spread_factor=1)
        assert res['scenario'] == "ransomware"
        assert res['impact_score'] == 80.0 # criticality 8 * 10 * 1

def test_twin_service_simulate_ransomware_missing_asset(app):
    """Test 6: DigitalTwinService default ransomware metrics fallback."""
    with app.app_context():
        res = DigitalTwinService.simulate_ransomware(9999)
        assert res['impact_score'] == 100.0 # default criticality 5 * 10 * 2 = 100

def test_twin_service_simulate_control_failure(app, twin_setup):
    """Test 7: DigitalTwinService calculates risk from failed compliance control."""
    with app.app_context():
        ctrl = twin_setup['ctrl']
        res = DigitalTwinService.simulate_control_failure(ctrl.id)
        assert res['scenario'] == "control_failures"
        assert res['impact_score'] == 75.0

def test_twin_service_simulate_control_failure_missing(app):
    """Test 8: DigitalTwinService control failure fallback configuration."""
    with app.app_context():
        res = DigitalTwinService.simulate_control_failure(9999)
        assert res['impact_score'] == 45.0

def test_twin_rest_endpoint(client, twin_setup):
    """Test 9: GET /api/v1/digital-twin lists twin template profiles."""
    headers = twin_setup['headers']
    resp = client.get('/api/v1/digital-twin', headers=headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['count'] == 1
    assert data['digital_twins'][0]['name'] == "Ransomware-Twin-Primary"

def test_twin_rest_endpoint_org_filter(client, twin_setup):
    """Test 10: GET /api/v1/digital-twin filters by organization ID."""
    headers = twin_setup['headers']
    resp = client.get('/api/v1/digital-twin?org_id=9999', headers=headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['count'] == 0

def test_twin_rest_endpoint_requires_auth(client):
    """Test 11: GET /api/v1/digital-twin rejects requests with invalid JWT tokens."""
    resp = client.get('/api/v1/digital-twin', headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401
