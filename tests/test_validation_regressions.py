"""
Unit and Integration tests for Validation Regressions.
Contains 10 test cases covering score drops tracking, severity classification thresholds, resolutions workflow, and REST endpoints.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.validation_regression import ValidationRegression
from app.services.validation_regression_service import ValidationRegressionService
from app.research.routes import create_jwt


@pytest.fixture
def regressions_setup(app):
    with app.app_context():
        db.session.query(ValidationRegression).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_regression_model(app, regressions_setup):
    """Test 1: ValidationRegression model validations."""
    with app.app_context():
        r = ValidationRegression(
            resource_type="control",
            resource_id=1,
            metric_type="score",
            previous_score=90.0,
            current_score=80.0,
            regression_delta=10.0,
            severity="medium",
            status="open",
            organization_id=regressions_setup["o1"].id
        )
        db.session.add(r)
        db.session.commit()
        assert r.id is not None


def test_compare_results(app, regressions_setup):
    """Test 2: compare_results calculation."""
    assert ValidationRegressionService.compare_results("control", 1, 95.0, 80.0, regressions_setup["o1"].id) == 15.0
    assert ValidationRegressionService.compare_results("control", 1, 70.0, 75.0, regressions_setup["o1"].id) == 0.0


def test_classify_regression_none(app, regressions_setup):
    """Test 3: classify_regression returns None if delta < 5.0."""
    assert ValidationRegressionService.classify_regression(4.9) is None


def test_classify_regression_low(app, regressions_setup):
    """Test 4: classify_regression low severity threshold."""
    assert ValidationRegressionService.classify_regression(7.5) == "low"


def test_classify_regression_medium(app, regressions_setup):
    """Test 5: classify_regression medium severity threshold."""
    assert ValidationRegressionService.classify_regression(15.0) == "medium"


def test_classify_regression_high(app, regressions_setup):
    """Test 6: classify_regression high severity threshold."""
    assert ValidationRegressionService.classify_regression(25.0) == "high"


def test_classify_regression_critical(app, regressions_setup):
    """Test 7: classify_regression critical severity threshold."""
    assert ValidationRegressionService.classify_regression(35.0) == "critical"


def test_detect_regression_saves(app, regressions_setup):
    """Test 8: detect_regression creates record if drop warrants it."""
    with app.app_context():
        reg = ValidationRegressionService.detect_regression("control", 1, 90.0, 75.0, regressions_setup["o1"].id)
        assert reg is not None
        assert reg.severity == "medium"
        assert reg.status == "open"


def test_resolve_regression(app, regressions_setup):
    """Test 9: resolve_regression transitions state to resolved."""
    with app.app_context():
        reg = ValidationRegressionService.detect_regression("control", 1, 90.0, 70.0, regressions_setup["o1"].id)
        resolved = ValidationRegressionService.resolve_regression(reg.id, regressions_setup["o1"].id)
        assert resolved.status == "resolved"


def test_api_regressions_routes(app, regressions_setup):
    """Test 10: Regressions listing and resolution endpoints."""
    client = app.test_client()

    with app.app_context():
        reg = ValidationRegressionService.detect_regression("control", 1, 95.0, 60.0, regressions_setup["o1"].id)
        reg_id = reg.id

    resp = client.get(
        f'/api/v1/validation-fabric/regressions?org_id={regressions_setup["o1"].id}',
        headers=regressions_setup["headers"]
    )
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1

    resp = client.post(
        f'/api/v1/validation-fabric/regressions/{reg_id}/resolve',
        json={"org_id": regressions_setup["o1"].id},
        headers=regressions_setup["headers"]
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "resolved"
