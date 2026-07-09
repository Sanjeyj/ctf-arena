"""Tests for Mission Control API endpoints.
Phase 40 — Platform Convergence, Certification, Mission Control & Release Readiness.
Contains 10 test cases.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.platform_capability import PlatformCapability
from app.models.platform_certification_run import PlatformCertificationRun
from app.models.release_baseline import ReleaseBaseline
from app.services.capability_registry_service import CapabilityRegistryService
from app.services.release_baseline_service import ReleaseBaselineService
from app.research.routes import create_jwt


@pytest.fixture
def mc_setup(app):
    with app.app_context():
        db.session.query(PlatformCapability).delete()
        db.session.query(PlatformCertificationRun).delete()
        db.session.query(ReleaseBaseline).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="MissionOrg", slug="mission-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin", "org_id": org.id}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }


def test_api_overview_returns_200(app, mc_setup):
    """Test 1: Overview endpoint returns 200 with org_id."""
    client = app.test_client()
    with app.app_context():
        resp = client.get(
            f"/api/v1/mission-control/overview?org_id={mc_setup['org'].id}",
            headers=mc_setup["headers"],
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_capabilities" in data


def test_api_overview_requires_org_id(app, mc_setup):
    """Test 2: Overview endpoint requires org_id."""
    client = app.test_client()
    resp = client.get("/api/v1/mission-control/overview", headers=mc_setup["headers"])
    assert resp.status_code == 400


def test_api_overview_requires_auth(app, mc_setup):
    """Test 3: Overview endpoint requires JWT."""
    client = app.test_client()
    with app.app_context():
        resp = client.get(
            f"/api/v1/mission-control/overview?org_id={mc_setup['org'].id}"
        )
        assert resp.status_code == 401


def test_api_get_capabilities_returns_200(app, mc_setup):
    """Test 4: Capabilities list endpoint returns 200."""
    client = app.test_client()
    with app.app_context():
        CapabilityRegistryService.register_capability(
            mc_setup["org"].id, "cap1", "Cap 1", 1
        )
        resp = client.get(
            f"/api/v1/mission-control/capabilities?org_id={mc_setup['org'].id}",
            headers=mc_setup["headers"],
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1


def test_api_register_capability_post(app, mc_setup):
    """Test 5: POST capabilities registers new capability."""
    client = app.test_client()
    with app.app_context():
        payload = {
            "org_id": mc_setup["org"].id,
            "capability_key": "new_cap",
            "name": "New Cap",
            "phase_introduced": 40,
            "category": "certification",
        }
        resp = client.post(
            "/api/v1/mission-control/capabilities",
            json=payload,
            headers=mc_setup["headers"],
        )
        assert resp.status_code == 201
        assert resp.get_json()["capability_key"] == "new_cap"


def test_api_register_capability_missing_fields(app, mc_setup):
    """Test 6: Missing capability fields returns 400."""
    client = app.test_client()
    resp = client.post(
        "/api/v1/mission-control/capabilities",
        json={"org_id": mc_setup["org"].id},
        headers=mc_setup["headers"],
    )
    assert resp.status_code == 400


def test_api_create_certification_post(app, mc_setup):
    """Test 7: POST certifications creates a run."""
    client = app.test_client()
    with app.app_context():
        payload = {
            "org_id": mc_setup["org"].id,
            "name": "Phase 40 Full Audit",
            "certification_type": "full_platform",
        }
        resp = client.post(
            "/api/v1/mission-control/certifications",
            json=payload,
            headers=mc_setup["headers"],
        )
        assert resp.status_code == 201
        assert resp.get_json()["name"] == "Phase 40 Full Audit"


def test_api_evaluate_readiness_post(app, mc_setup):
    """Test 8: POST readiness triggers readiness evaluation."""
    client = app.test_client()
    with app.app_context():
        payload = {
            "org_id": mc_setup["org"].id,
            "metric_type": "on_demand",
        }
        resp = client.post(
            "/api/v1/mission-control/readiness",
            json=payload,
            headers=mc_setup["headers"],
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert "overall_readiness_score" in data


def test_api_create_baseline_post(app, mc_setup):
    """Test 9: POST baselines creates a release baseline."""
    client = app.test_client()
    with app.app_context():
        payload = {
            "org_id": mc_setup["org"].id,
            "version": "v1.0.0",
            "metrics": {
                "migration_revision": "8bce79803ffc",
                "test_count": 1509,
                "warning_count": 0,
                "model_count": 120,
                "service_count": 90,
                "route_count": 200,
                "template_count": 130,
                "documentation_count": 90,
            },
            "codename": "Convergence",
        }
        resp = client.post(
            "/api/v1/mission-control/baselines",
            json=payload,
            headers=mc_setup["headers"],
        )
        assert resp.status_code == 201
        assert resp.get_json()["version"] == "v1.0.0"


def test_api_create_adr_post(app, mc_setup):
    """Test 10: POST decisions creates an architecture decision record."""
    client = app.test_client()
    with app.app_context():
        payload = {
            "org_id": mc_setup["org"].id,
            "adr_key": "ADR-001",
            "title": "Unified Blueprint Architecture",
            "decision": "All blueprints follow a common factory registration pattern.",
        }
        resp = client.post(
            "/api/v1/mission-control/decisions",
            json=payload,
            headers=mc_setup["headers"],
        )
        assert resp.status_code == 201
        assert resp.get_json()["adr_key"] == "ADR-001"
