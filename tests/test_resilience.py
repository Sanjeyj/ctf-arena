"""
Unit and Integration tests for Step 3 Organizational Resilience Engine.
Contains 10 test cases.
"""
import pytest
import json
import datetime
from app.extensions import db
from app.models.resilience_score import ResilienceScore
from app.models.compliance_control import ComplianceControl
from app.models.governance_framework import GovernanceFramework
from app.models.incident import Incident
from app.models.attack_simulation import AttackSimulation
from app.models.organization import Organization
from app.services.resilience_service import ResilienceService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password

@pytest.fixture
def resilience_setup(app):
    with app.app_context():
        # Setup roles/perms
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(ResilienceScore).delete()
        db.session.query(ComplianceControl).delete()
        db.session.query(GovernanceFramework).delete()
        db.session.query(Incident).delete()
        db.session.query(AttackSimulation).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Resilience Org", slug="resilience-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        # Create test admin user
        try:
            UserRepository.create(
                username="resilience_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Resilience Admin",
                role_name="Admin"
            )
        except Exception:
            pass  # User may already exist from a prior test

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "resilience_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_resilience_score_creation(app, resilience_setup):
    """Test 1: ResilienceScore model attributes mapping."""
    with app.app_context():
        score = ResilienceScore(
            response_time=90.0,
            controls=85.5,
            incidents=95.0,
            training=80.0,
            risk=70.0,
            resilience=85.2,
            organization_id=resilience_setup['org'].id
        )
        db.session.add(score)
        db.session.commit()
        assert score.resilience == 85.2
        assert "85.2" in repr(score)

def test_resilience_score_to_dict(app, resilience_setup):
    """Test 2: ResilienceScore serialization map."""
    with app.app_context():
        score = ResilienceScore(
            response_time=90.0,
            controls=85.5,
            incidents=95.0,
            training=80.0,
            risk=70.0,
            resilience=85.2,
            organization_id=resilience_setup['org'].id
        )
        db.session.add(score)
        db.session.commit()
        d = score.to_dict()
        assert d['resilience'] == 85.2
        assert d['response_time'] == 90.0

def test_resilience_service_calculate_default(app, resilience_setup):
    """Test 3: ResilienceService computes index with empty database metrics (fallbacks)."""
    with app.app_context():
        score = ResilienceService.calculate_resilience(resilience_setup['org'].id)
        assert score.id is not None
        assert score.resilience > 0.0

def test_resilience_service_calculate_with_data(app, resilience_setup):
    """Test 4: ResilienceService computes index with populated metrics."""
    with app.app_context():
        org_id = resilience_setup['org'].id
        # Create compliance controls
        fw = GovernanceFramework(name="NIST", description="NIST", organization_id=org_id)
        db.session.add(fw)
        db.session.commit()
        
        # 1 passed control, 1 failed control -> 50%
        c1 = ComplianceControl(framework_id=fw.id, control_code="A", status="passed", organization_id=org_id)
        c2 = ComplianceControl(framework_id=fw.id, control_code="B", status="failed", organization_id=org_id)
        db.session.add_all([c1, c2])
        db.session.commit()

        # Create incidents
        sim = AttackSimulation(name="Sim", description="Sim", organization_id=org_id)
        db.session.add(sim)
        db.session.commit()
        
        inc = Incident(
            title="Inc", 
            simulation_id=sim.id, 
            status="resolved", 
            detected_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=30),
            resolved_at=datetime.datetime.utcnow()
        )
        db.session.add(inc)
        db.session.commit()

        score = ResilienceService.calculate_resilience(org_id)
        assert score.controls == 50.0  # 1 passed of 2 total
        assert score.resilience > 0.0

def test_resilience_service_get_latest(app, resilience_setup):
    """Test 5: ResilienceService fetches latest scorecard record."""
    with app.app_context():
        org_id = resilience_setup['org'].id
        score = ResilienceService.calculate_resilience(org_id)
        latest = ResilienceService.get_latest_score(org_id)
        assert latest.id == score.id

def test_resilience_service_get_history(app, resilience_setup):
    """Test 6: ResilienceService fetches score history list."""
    with app.app_context():
        org_id = resilience_setup['org'].id
        s1 = ResilienceService.calculate_resilience(org_id)
        s2 = ResilienceService.calculate_resilience(org_id)
        history = ResilienceService.get_history(org_id)
        assert len(history) >= 2

def test_resilience_api_get_score(client, resilience_setup):
    """Test 7: GET /api/v1/resilience API endpoint."""
    resp = client.get(f'/api/v1/resilience?org_id={resilience_setup["org"].id}', headers=resilience_setup['headers'])
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert 'resilience' in data

def test_resilience_api_calculate_score(client, resilience_setup):
    """Test 8: POST /api/v1/resilience/calculate API endpoint."""
    resp = client.post(
        '/api/v1/resilience/calculate',
        json={'organization_id': resilience_setup['org'].id},
        headers=resilience_setup['headers']
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert 'resilience' in data

def test_resilience_api_rejects_missing_org(client, resilience_setup):
    """Test 9: GET/POST API endpoints require correct parameters."""
    resp = client.get('/api/v1/resilience', headers=resilience_setup['headers'])
    assert resp.status_code == 400
    
    resp = client.post('/api/v1/resilience/calculate', json={}, headers=resilience_setup['headers'])
    assert resp.status_code == 400

def test_resilience_admin_dashboard_access(client, resilience_setup):
    """Test 10: Render admin resilience scorecard dashboard."""
    client.post('/admin/login', data={'username': 'resilience_admin', 'password': 'AdminPass123!'})
    resp = client.get(f'/admin/cloud/resilience?org_id={resilience_setup["org"].id}')
    assert resp.status_code == 200
    assert b"Admin" in resp.data

