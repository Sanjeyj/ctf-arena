"""
Unit and Integration tests for Detection Validation.
Contains 10 test cases covering synthetic signal mapping, rule coverage ratio calculations, latency penalty rules, and gaps audit APIs.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.validation_campaign import ValidationCampaign
from app.models.validation_scenario import ValidationScenario
from app.models.validation_execution import ValidationExecution
from app.models.detection_validation import DetectionValidation
from app.services.validation_campaign_service import ValidationCampaignService
from app.services.validation_engine_service import ValidationEngineService
from app.services.detection_validation_service import DetectionValidationService
from app.research.routes import create_jwt


@pytest.fixture
def detection_setup(app):
    with app.app_context():
        db.session.query(DetectionValidation).delete()
        db.session.query(ValidationExecution).delete()
        db.session.query(ValidationScenario).delete()
        db.session.query(ValidationCampaign).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        c = ValidationCampaignService.create_campaign(
            "Det Campaign", "Desc", "detection_validation", "scope", "medium", None, o1.id
        )
        s = ValidationCampaignService.add_scenario(
            c.id, "Det Scenario", "detection", "Verify rules", "high", "detected", "{}", o1.id
        )
        ex = ValidationEngineService.execute_scenario(s.id, o1.id)

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "exec": ex,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_detection_validation_model(app, detection_setup):
    """Test 1: DetectionValidation model attributes validation."""
    with app.app_context():
        v = DetectionValidation(
            execution_id=detection_setup["exec"].id,
            detection_type="sigma",
            detection_reference="rules/win_malware.yml",
            synthetic_signal_type="process_create",
            expected_detection=True,
            detected=True,
            organization_id=detection_setup["o1"].id
        )
        db.session.add(v)
        db.session.commit()
        assert v.id is not None


def test_create_synthetic_signal(app, detection_setup):
    """Test 2: DetectionValidationService.create_synthetic_signal."""
    with app.app_context():
        v = DetectionValidationService.create_synthetic_signal(
            detection_setup["exec"].id, "sigma", "rules/sysmon.yml", "file_event", True, detection_setup["o1"].id
        )
        assert v.id is not None
        assert v.detection_type == "sigma"


def test_create_synthetic_signal_invalid_type(app, detection_setup):
    """Test 3: create_synthetic_signal raises error for invalid types."""
    with app.app_context():
        with pytest.raises(ValueError, match="Invalid detection_type"):
            DetectionValidationService.create_synthetic_signal(
                detection_setup["exec"].id, "invalid_type", "ref", "sig", True, detection_setup["o1"].id
            )


def test_evaluate_detection_detected(app, detection_setup):
    """Test 4: evaluate_detection updates detection state successfully."""
    with app.app_context():
        v = DetectionValidationService.create_synthetic_signal(
            detection_setup["exec"].id, "sigma", "rules/sysmon.yml", "file_event", True, detection_setup["o1"].id
        )
        v = DetectionValidationService.evaluate_detection(v.id, True, 0.95, detection_setup["o1"].id)
        assert v.detected is True
        assert v.coverage_score == 1.0


def test_evaluate_detection_missed(app, detection_setup):
    """Test 5: evaluate_detection marks missed rules appropriately."""
    with app.app_context():
        v = DetectionValidationService.create_synthetic_signal(
            detection_setup["exec"].id, "sigma", "rules/sysmon.yml", "file_event", True, detection_setup["o1"].id
        )
        v = DetectionValidationService.evaluate_detection(v.id, False, 0.0, detection_setup["o1"].id)
        assert v.detected is False
        assert v.coverage_score == 0.0


def test_calculate_coverage_empty(app, detection_setup):
    """Test 6: calculate_coverage returns 0.0 if no checks recorded."""
    with app.app_context():
        assert DetectionValidationService.calculate_coverage(detection_setup["o1"].id) == 0.0


def test_calculate_coverage_values(app, detection_setup):
    """Test 7: calculate_coverage computes coverage correctly."""
    with app.app_context():
        v1 = DetectionValidationService.create_synthetic_signal(
            detection_setup["exec"].id, "sigma", "r1", "s1", True, detection_setup["o1"].id
        )
        v2 = DetectionValidationService.create_synthetic_signal(
            detection_setup["exec"].id, "sigma", "r2", "s2", True, detection_setup["o1"].id
        )
        DetectionValidationService.evaluate_detection(v1.id, True, 1.0, detection_setup["o1"].id)
        DetectionValidationService.evaluate_detection(v2.id, False, 1.0, detection_setup["o1"].id)

        assert DetectionValidationService.calculate_coverage(detection_setup["o1"].id) == 0.5


def test_calculate_latency_score(app, detection_setup):
    """Test 8: calculate_latency_score penalty rules."""
    assert DetectionValidationService.calculate_latency_score(0) == 1.0
    assert DetectionValidationService.calculate_latency_score(150) == 0.5
    assert DetectionValidationService.calculate_latency_score(300) == 0.0
    assert DetectionValidationService.calculate_latency_score(400) == 0.0


def test_find_detection_gaps(app, detection_setup):
    """Test 9: find_detection_gaps identifies gaps properly."""
    with app.app_context():
        v = DetectionValidationService.create_synthetic_signal(
            detection_setup["exec"].id, "sigma", "rules/win_malware.yml", "process_create", True, detection_setup["o1"].id
        )
        DetectionValidationService.evaluate_detection(v.id, False, 0.0, detection_setup["o1"].id)

        gaps = DetectionValidationService.find_detection_gaps(detection_setup["o1"].id)
        assert len(gaps) == 1
        assert gaps[0]["detection_reference"] == "rules/win_malware.yml"


def test_api_detection_routes(app, detection_setup):
    """Test 10: Detection validation API endpoints."""
    client = app.test_client()

    # Create signal
    resp = client.post(
        '/api/v1/validation-fabric/detection/signal',
        json={
            "org_id": detection_setup["o1"].id,
            "execution_id": detection_setup["exec"].id,
            "detection_type": "sigma",
            "detection_reference": "rules/api_rule.yml",
            "synthetic_signal_type": "dns_query"
        },
        headers=detection_setup["headers"]
    )
    assert resp.status_code == 201
    val_id = resp.get_json()["id"]

    # Evaluate detection
    resp = client.post(
        '/api/v1/validation-fabric/detection/evaluate',
        json={
            "org_id": detection_setup["o1"].id,
            "validation_id": val_id,
            "detected": True,
            "latency_score": 0.8
        },
        headers=detection_setup["headers"]
    )
    assert resp.status_code == 200

    # Gaps check
    resp = client.get(
        f'/api/v1/validation-fabric/detection/gaps?org_id={detection_setup["o1"].id}',
        headers=detection_setup["headers"]
    )
    assert resp.status_code == 200
