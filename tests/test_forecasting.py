"""
Unit and Integration tests for Phase 27 Global Security Intelligence Network — Forecasting.
Contains 10 test cases covering prediction models, forecasting events, service logic, and APIs.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.prediction_model import PredictionModel
from app.models.forecast_event import ForecastEvent
from app.services.forecast_service import ForecastService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def forecast_setup(app):
    """Fixture for forecast tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(ForecastEvent).delete()
        db.session.query(PredictionModel).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Forecast Org", slug="forecast-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="forecast_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Forecast Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "forecast_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_prediction_model_creation(app, forecast_setup):
    """Test 1: PredictionModel model fields."""
    with app.app_context():
        model = PredictionModel(
            model_name="Ransomware-Predictor",
            confidence=0.85,
            version="1.2.0",
            accuracy=0.89,
            organization_id=forecast_setup["org"].id
        )
        db.session.add(model)
        db.session.commit()
        assert model.id is not None
        assert model.model_name == "Ransomware-Predictor"
        assert model.confidence == 0.85
        assert model.accuracy == 0.89


def test_prediction_model_to_dict(app, forecast_setup):
    """Test 2: PredictionModel serialization."""
    with app.app_context():
        model = PredictionModel(
            model_name="Phishing-LSTM",
            confidence=0.78,
            version="2.0.1",
            accuracy=0.82,
            organization_id=forecast_setup["org"].id
        )
        db.session.add(model)
        db.session.commit()
        d = model.to_dict()
        assert d["model_name"] == "Phishing-LSTM"
        assert d["confidence"] == 0.78
        assert d["version"] == "2.0.1"


def test_forecast_event_creation(app, forecast_setup):
    """Test 3: ForecastEvent model fields."""
    with app.app_context():
        event = ForecastEvent(
            prediction="Ransomware surge on finance sector.",
            probability=0.75,
            impact="critical",
            confidence=0.8,
            organization_id=forecast_setup["org"].id
        )
        db.session.add(event)
        db.session.commit()
        assert event.id is not None
        assert event.impact == "critical"
        assert event.probability == 0.75


def test_forecast_event_to_dict(app, forecast_setup):
    """Test 4: ForecastEvent serialization."""
    with app.app_context():
        event = ForecastEvent(
            prediction="DDoS surge on DNS hosts.",
            probability=0.45,
            impact="medium",
            confidence=0.7,
            organization_id=forecast_setup["org"].id
        )
        db.session.add(event)
        db.session.commit()
        d = event.to_dict()
        assert d["impact"] == "medium"
        assert d["probability"] == 0.45
        assert d["confidence"] == 0.7


def test_forecast_service_predict_default(app, forecast_setup):
    """Test 5: ForecastService predict with unrecognized type."""
    with app.app_context():
        event = ForecastService.predict("unknown_threat", org_id=forecast_setup["org"].id)
        assert event is not None
        assert "unknown_threat" in event.prediction
        assert event.organization_id == forecast_setup["org"].id


def test_forecast_service_predict_template(app, forecast_setup):
    """Test 6: ForecastService predict with registered template."""
    with app.app_context():
        # Setup pre-existing model for accuracy check
        model = PredictionModel(
            model_name="Baseline-ML",
            confidence=0.9,
            version="1.0.0",
            accuracy=0.85,
            organization_id=forecast_setup["org"].id
        )
        db.session.add(model)
        db.session.commit()

        event = ForecastService.predict("ransomware", org_id=forecast_setup["org"].id)
        assert event is not None
        assert "ransomware" in event.prediction or "Ransomware" in event.prediction
        assert event.confidence == 0.9


def test_forecast_service_score_valid(app, forecast_setup):
    """Test 7: Score calculations for a valid forecast."""
    with app.app_context():
        event = ForecastEvent(
            prediction="Test Prediction",
            probability=0.8,
            impact="high",
            confidence=0.9,
            organization_id=forecast_setup["org"].id
        )
        db.session.add(event)
        db.session.commit()

        res = ForecastService.score(event.id)
        assert res["composite_score"] == 0.85
        assert res["risk_level"] == "high"


def test_forecast_service_score_invalid(app):
    """Test 8: Score calculation for invalid forecast ID."""
    with app.app_context():
        res = ForecastService.score(99999)
        assert "error" in res


def test_forecast_service_explain(app, forecast_setup):
    """Test 9: ForecastService explanation generator."""
    with app.app_context():
        event = ForecastEvent(
            prediction="Ransomware alert",
            probability=0.6,
            impact="medium",
            confidence=0.7,
            organization_id=forecast_setup["org"].id
        )
        db.session.add(event)
        db.session.commit()

        exp = ForecastService.explain(event.id)
        assert "Ransomware alert" in exp
        assert "60%" in exp
        assert "70%" in exp


def test_api_get_forecast(client, forecast_setup):
    """Test 10: GET /api/v1/forecast API route."""
    with client.application.app_context():
        event = ForecastEvent(
            prediction="Zero-day vector in OpenSSL",
            probability=0.92,
            impact="critical",
            confidence=0.88,
            organization_id=forecast_setup["org"].id
        )
        db.session.add(event)
        db.session.commit()

    resp = client.get(
        f'/api/v1/forecast?org_id={forecast_setup["org"].id}',
        headers=forecast_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["prediction"] == "Zero-day vector in OpenSSL"
