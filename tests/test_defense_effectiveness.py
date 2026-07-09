"""
Unit and Integration tests for Defense Effectiveness.
Contains 10 test cases covering control coverage integrations, playbook metric calculations, composite scores weighting, trends tracking, and API endpoints.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.defense_effectiveness_metric import DefenseEffectivenessMetric
from app.models.control_coverage_map import ControlCoverageMap
from app.services.control_coverage_service import ControlCoverageService
from app.services.defense_effectiveness_service import DefenseEffectivenessService
from app.research.routes import create_jwt


@pytest.fixture
def effectiveness_setup(app):
    with app.app_context():
        db.session.query(DefenseEffectivenessMetric).delete()
        db.session.query(ControlCoverageMap).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        # Seed a control map record to establish avg_effectiveness at 80% (0.8)
        ControlCoverageService.map_control(
            control_ref="CTRL-001",
            resource_type="service",
            resource_id=1,
            coverage_score=0.8,
            effectiveness_score=0.8,
            status="passed",
            org_id=o1.id
        )

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_metric_model(app, effectiveness_setup):
    """Test 1: DefenseEffectivenessMetric model validations."""
    with app.app_context():
        m = DefenseEffectivenessMetric(
            metric_type="composite",
            score=85.0,
            previous_score=80.0,
            delta=5.0,
            trend="improving",
            organization_id=effectiveness_setup["o1"].id
        )
        db.session.add(m)
        db.session.commit()
        assert m.id is not None


def test_calculate_control_effectiveness(app, effectiveness_setup):
    """Test 2: calculate_control_effectiveness returns 80% based on seeded control."""
    with app.app_context():
        score = DefenseEffectivenessService.calculate_control_effectiveness(effectiveness_setup["o1"].id)
        assert score == 80.0


def test_calculate_detection_effectiveness(app, effectiveness_setup):
    """Test 3: calculate_detection_effectiveness default mapping."""
    with app.app_context():
        score = DefenseEffectivenessService.calculate_detection_effectiveness(effectiveness_setup["o1"].id)
        assert score == 0.0  # empty detection validation summary returns 0.0


def test_calculate_playbook_effectiveness(app, effectiveness_setup):
    """Test 4: calculate_playbook_effectiveness default mapping."""
    with app.app_context():
        score = DefenseEffectivenessService.calculate_playbook_effectiveness(effectiveness_setup["o1"].id)
        assert score == 0.0  # empty playbook metrics returns 0.0


def test_calculate_resilience_effectiveness(app, effectiveness_setup):
    """Test 5: calculate_resilience_effectiveness default baseline."""
    with app.app_context():
        score = DefenseEffectivenessService.calculate_resilience_effectiveness(effectiveness_setup["o1"].id)
        assert score == 80.0  # default baseline if ResilienceScore not in DB


def test_calculate_architecture_effectiveness(app, effectiveness_setup):
    """Test 6: calculate_architecture_effectiveness returns 100.0 if boundaries empty."""
    with app.app_context():
        score = DefenseEffectivenessService.calculate_architecture_effectiveness(effectiveness_setup["o1"].id)
        assert score == 100.0


def test_calculate_composite_score(app, effectiveness_setup):
    """Test 7: calculate_composite_score weights logic."""
    with app.app_context():
        # calculations with defaults: ctrl=80, det=0, play=0, res=80, arch=100
        # composite = 0.25*80 + 0.25*0 + 0.20*0 + 0.15*80 + 0.15*100 = 20 + 0 + 0 + 12 + 15 = 47.0
        m = DefenseEffectivenessService.calculate_composite_score(effectiveness_setup["o1"].id)
        assert m.score == 47.0
        assert m.trend == "stable"  # first run defaults trend to stable


def test_effectiveness_summary(app, effectiveness_setup):
    """Test 8: effectiveness_summary aggregates correctly."""
    with app.app_context():
        summary = DefenseEffectivenessService.effectiveness_summary(effectiveness_setup["o1"].id)
        assert summary["control_effectiveness"] == 80.0
        assert summary["architecture_effectiveness"] == 100.0


def test_effectiveness_trend(app, effectiveness_setup):
    """Test 9: effectiveness_trend displays historical records."""
    with app.app_context():
        DefenseEffectivenessService.calculate_composite_score(effectiveness_setup["o1"].id)
        trend = DefenseEffectivenessService.effectiveness_trend(effectiveness_setup["o1"].id)
        assert len(trend) == 1
        assert trend[0]["score"] == 47.0


def test_api_effectiveness_routes(app, effectiveness_setup):
    """Test 10: Defense effectiveness API endpoints."""
    client = app.test_client()

    resp = client.get(
        f'/api/v1/validation-fabric/effectiveness?org_id={effectiveness_setup["o1"].id}',
        headers=effectiveness_setup["headers"]
    )
    assert resp.status_code == 200
    assert "summary" in resp.get_json()

    resp = client.post(
        '/api/v1/validation-fabric/effectiveness',
        json={"org_id": effectiveness_setup["o1"].id},
        headers=effectiveness_setup["headers"]
    )
    assert resp.status_code == 201
    assert resp.get_json()["score"] == 47.0
