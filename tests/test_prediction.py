"""
Unit and Integration tests for Step 6 Threat Prediction Engine.
"""
import pytest
import json
from app.extensions import db
from app.models.alert import Alert
from app.models.organization import Organization
from app.models.threat_actor import ThreatActor
from app.services.prediction_service import PredictionService
from app.research.routes import create_jwt

@pytest.fixture
def pred_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(ThreatActor).delete()
        db.session.query(Alert).delete()
        db.session.commit()

        org = Organization(name="Pred Org", slug="pred-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        # Seed alerts
        alert1 = Alert(title="Authentication anomaly", severity="medium", status="new", organization_id=org.id)
        alert2 = Alert(title="Directory traversal attempt", severity="high", status="new", organization_id=org.id)
        db.session.add_all([alert1, alert2])
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "pred_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_prediction_forecast_math(app, pred_setup):
    """Test compiled forecast outputs and risk parameters calculation."""
    with app.app_context():
        org = pred_setup['org']
        forecast = PredictionService.forecast_threats(org_id=org.id)
        assert forecast['alert_count_input'] == 2
        assert "trending_techniques" in forecast
        assert len(forecast['high_risk_assets']) >= 1
        assert forecast['confidence_percentage'] > 0.0


def test_prediction_api_endpoint(client, pred_setup):
    """Test GET /api/v1/predictions endpoint."""
    headers = pred_setup['headers']
    resp = client.get('/api/v1/predictions', headers=headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)['predictions']
    assert data['alert_count_input'] == 2
    assert "forecasted_adversary" in data


def test_prediction_empty_database_forecast(app):
    """Test forecasting triggers default values when database is empty."""
    with app.app_context():
        # Using org_id that has no alerts
        forecast = PredictionService.forecast_threats(org_id=9999)
        assert forecast['forecasted_adversary'] == "Generic Cybercrime Syndicate" or forecast['forecasted_adversary'] == "APT39 / Chafer"


def test_prediction_adversary_threat_escalation(app, pred_setup):
    """Test threat prediction adversary changes based on alert volume thresholds."""
    with app.app_context():
        org = pred_setup['org']
        # Create a ThreatActor so actor_count > 0
        actor = ThreatActor(name="Cozy Bear", aliases="APT29", country="RU", motivation="espionage", sophistication="high")
        db.session.add(actor)
        
        # Add 3 more alerts to reach a total of 5 alerts
        for i in range(3):
            alert = Alert(title=f"Exploit {i}", severity="high", status="new", organization_id=org.id)
            db.session.add(alert)
        db.session.commit()
        
        forecast = PredictionService.forecast_threats(org_id=org.id)
        assert forecast['alert_count_input'] == 5
        assert forecast['forecasted_adversary'] == "APT28 / Cozy Bear"

