"""
Unit and Integration tests for Step 3 Risk Engine.
"""
import pytest
import json
from app.extensions import db
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.asset import Asset
from app.models.user import User
from app.models.organization import Organization
from app.models.attack_simulation import AttackSimulation
from app.services.risk_service import RiskService
from app.research.routes import create_jwt

@pytest.fixture
def risk_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(Alert).delete()
        db.session.query(Incident).delete()
        db.session.query(Asset).delete()
        db.session.query(User).delete()
        db.session.commit()

        org = Organization(name="Risk Org", slug="risk-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        user = User(username="analyst_bob", email="bob@risk.net", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        asset = Asset(name="Core DB", type_label="server", criticality=8, organization_id=org.id)
        db.session.add(asset)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "risk_admin"}, secret)

        yield {
            "org": org,
            "user": user,
            "asset": asset,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_asset_risk_calculation(app, risk_setup):
    """Test calculating risk levels for single asset."""
    with app.app_context():
        asset = risk_setup['asset']
        # Criticality = 8 -> score = 80 -> CRITICAL
        risk = RiskService.calculate_asset_risk(asset.id)
        assert risk == "CRITICAL"

def test_user_risk_calculation(app, risk_setup):
    """Test user threat risk level scaling with active incidents count."""
    with app.app_context():
        user = risk_setup['user']
        org = risk_setup['org']
        
        sim = AttackSimulation(name="Sim Test", organization_id=org.id)
        db.session.add(sim)
        db.session.commit()

        # Add active incidents assigned to user
        inc1 = Incident(title="Incident 1", assigned_to=user.username, simulation_id=sim.id)
        inc2 = Incident(title="Incident 2", assigned_to=user.username, simulation_id=sim.id)
        db.session.add_all([inc1, inc2])
        db.session.commit()

        risk = RiskService.calculate_user_risk(user.id)
        assert risk == "MEDIUM" or risk == "HIGH"

def test_organization_risk_scale(app, risk_setup):
    """Test organization risk level calculation incorporates alerts and incidents."""
    with app.app_context():
        org = risk_setup['org']
        sim = AttackSimulation(name="Sim 2", organization_id=org.id)
        db.session.add(sim)
        db.session.commit()

        inc = Incident(title="Inc A", simulation_id=sim.id)
        alert = Alert(title="Alert A", severity="high", status="new", organization_id=org.id)
        db.session.add_all([inc, alert])
        db.session.commit()

        risk = RiskService.calculate_organization_risk(org.id)
        assert risk == "LOW" or risk == "MEDIUM"

def test_risk_api_route(client, risk_setup):
    """Test GET /api/v1/risk response values."""
    headers = risk_setup['headers']
    resp = client.get('/api/v1/risk', headers=headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "organization_risk" in data
    assert "threat_risk" in data


def test_risk_calculation_for_nonexistent_asset(app):
    """Test calculating risk of missing asset returns LOW default."""
    with app.app_context():
        res = RiskService.calculate_asset_risk(9999)
        assert res == "LOW"


def test_risk_calculation_for_nonexistent_user(app):
    """Test calculating user risk of missing user returns LOW default."""
    with app.app_context():
        res = RiskService.calculate_user_risk(9999)
        assert res == "LOW"


def test_organization_risk_for_invalid_org(app):
    """Test calculating org risk with empty parameters returns LOW."""
    with app.app_context():
        res = RiskService.calculate_organization_risk(9999)
        assert res == "LOW"


def test_threat_risk_with_many_alerts(app, risk_setup):
    """Test threat risk calculation escalates to CRITICAL when alert volume is > 10."""
    with app.app_context():
        org = risk_setup['org']
        # Create 11 alerts
        for i in range(11):
            a = Alert(title=f"Alert {i}", severity="high", status="new", organization_id=org.id)
            db.session.add(a)
        db.session.commit()
        
        res = RiskService.calculate_threat_risk()
        assert res == "CRITICAL"

