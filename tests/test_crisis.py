"""
Unit and Integration tests for Phase 25 Cyber Resilience Platform — Crisis Management.
Contains 8 test cases covering crisis events, service lifecycle, and API endpoints.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.crisis_event import CrisisEvent
from app.services.crisis_service import CrisisService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def crisis_setup(app):
    """Fixture for crisis management tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(CrisisEvent).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Crisis Org", slug="crisis-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="crisis_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Crisis Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "crisis_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_crisis_event_creation(app, crisis_setup):
    """Test 1: CrisisEvent model fields and defaults."""
    with app.app_context():
        event = CrisisEvent(
            event_name="DDoS on API Gateway",
            severity="high",
            status="active",
            impact_score=50.0,
            organization_id=crisis_setup['org'].id
        )
        db.session.add(event)
        db.session.commit()
        assert event.event_name == "DDoS on API Gateway"
        assert event.severity == "high"
        assert event.status == "active"
        assert "DDoS on API Gateway" in repr(event)


def test_crisis_event_to_dict(app, crisis_setup):
    """Test 2: CrisisEvent dict serialization."""
    with app.app_context():
        event = CrisisEvent(
            event_name="Data Breach",
            severity="critical",
            status="active",
            impact_score=80.0,
            organization_id=crisis_setup['org'].id
        )
        db.session.add(event)
        db.session.commit()
        d = event.to_dict()
        assert d['event_name'] == "Data Breach"
        assert d['severity'] == "critical"
        assert d['impact_score'] == 80.0


def test_crisis_service_declare(app, crisis_setup):
    """Test 3: CrisisService.declare_crisis creates an active event."""
    with app.app_context():
        event = CrisisService.declare_crisis(
            event_name="Ransomware Incident",
            severity="critical",
            organization_id=crisis_setup['org'].id
        )
        assert event.id is not None
        assert event.status == "active"
        assert event.severity == "critical"
        assert event.impact_score == 80.0  # critical = 80


def test_crisis_service_declare_high(app, crisis_setup):
    """Test 4: CrisisService.declare_crisis assigns correct impact for high severity."""
    with app.app_context():
        event = CrisisService.declare_crisis(
            event_name="Supply Chain Disruption",
            severity="high",
            organization_id=crisis_setup['org'].id
        )
        assert event.impact_score == 50.0  # high = 50


def test_crisis_service_coordinate(app, crisis_setup):
    """Test 5: CrisisService.coordinate reduces impact score."""
    with app.app_context():
        event = CrisisService.declare_crisis(
            event_name="Phishing Campaign",
            severity="medium",
            organization_id=crisis_setup['org'].id
        )
        initial_score = event.impact_score
        result = CrisisService.coordinate(event.id, "Blocked malicious IPs via firewall rules.")
        assert result['current_impact_score'] < initial_score


def test_crisis_service_resolve(app, crisis_setup):
    """Test 6: CrisisService.resolve closes a crisis event."""
    with app.app_context():
        event = CrisisService.declare_crisis(
            event_name="Insider Threat",
            severity="high",
            organization_id=crisis_setup['org'].id
        )
        resolved = CrisisService.resolve(event.id)
        assert resolved.status == "resolved"
        assert resolved.impact_score == 0.0


def test_api_get_crisis(client, crisis_setup):
    """Test 7: GET /api/v1/crisis returns valid list."""
    resp = client.get(
        f'/api/v1/crisis?org_id={crisis_setup["org"].id}',
        headers=crisis_setup['headers']
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data, list)


def test_api_post_crisis(client, crisis_setup):
    """Test 8: POST /api/v1/crisis declares a new crisis event."""
    resp = client.post(
        '/api/v1/crisis',
        json={
            'event_name': 'API Service Outage',
            'severity': 'high',
            'organization_id': crisis_setup['org'].id
        },
        headers=crisis_setup['headers']
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data['event_name'] == 'API Service Outage'
    assert data['status'] == 'active'
