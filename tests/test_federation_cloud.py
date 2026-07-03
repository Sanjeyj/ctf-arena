"""
Unit and Integration tests for Step 4 Distributed AI Federation & Threat Reputation.
Contains 15 test cases.
"""
import pytest
import json
from app.extensions import db
from app.models.agent_node import AgentNode
from app.models.threat_reputation import ThreatReputation
from app.models.security_mesh import SecurityMesh
from app.models.organization import Organization
from app.services.reputation_cloud_service import ReputationCloudService
from app.services.federated_ai_service import FederatedAIService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password

@pytest.fixture
def federation_setup(app):
    with app.app_context():
        # Setup roles/perms
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(AgentNode).delete()
        db.session.query(ThreatReputation).delete()
        db.session.query(SecurityMesh).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Federation Org", slug="federation-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        # Create test admin user
        UserRepository.create(
            username="fed_admin",
            password_hash=hash_password("AdminPass123!"),
            display_name="Federation Admin",
            role_name="Admin"
        )

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "fed_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_threat_reputation_creation(app, federation_setup):
    """Test 1: ThreatReputation database models values and schema."""
    with app.app_context():
        rep = ThreatReputation(entity_value="198.51.100.1", category="ioc", score=85, level="critical", organization_id=federation_setup['org'].id)
        db.session.add(rep)
        db.session.commit()
        assert rep.entity_value == "198.51.100.1"
        assert "198.51.100.1" in repr(rep)

def test_threat_reputation_to_dict(app, federation_setup):
    """Test 2: ThreatReputation dict structure mapping."""
    with app.app_context():
        rep = ThreatReputation(entity_value="malware.exe", category="malware", score=90, level="critical", organization_id=federation_setup['org'].id)
        db.session.add(rep)
        db.session.commit()
        d = rep.to_dict()
        assert d['entity_value'] == "malware.exe"
        assert d['score'] == 90

def test_agent_node_creation(app, federation_setup):
    """Test 3: AgentNode fields mapping."""
    with app.app_context():
        agent = AgentNode(name="Agent East", agent_type="SOC Agent", status="active", organization_id=federation_setup['org'].id)
        db.session.add(agent)
        db.session.commit()
        assert agent.name == "Agent East"
        assert "Agent East" in repr(agent)

def test_agent_node_to_dict(app, federation_setup):
    """Test 4: AgentNode serialization schema."""
    with app.app_context():
        agent = AgentNode(name="Agent West", agent_type="CTI Agent", status="inactive", organization_id=federation_setup['org'].id)
        db.session.add(agent)
        db.session.commit()
        d = agent.to_dict()
        assert d['name'] == "Agent West"
        assert d['status'] == "inactive"

def test_reputation_service_get(app, federation_setup):
    """Test 5: ReputationCloudService retrieves reputation records."""
    with app.app_context():
        org_id = federation_setup['org'].id
        rep = ThreatReputation(entity_value="198.51.100.5", score=40, organization_id=org_id)
        db.session.add(rep)
        db.session.commit()
        
        found = ReputationCloudService.get_reputation("198.51.100.5", org_id)
        assert found.score == 40

def test_reputation_service_update(app, federation_setup):
    """Test 6: ReputationCloudService inserts/updates threat rating."""
    with app.app_context():
        org_id = federation_setup['org'].id
        rep = ReputationCloudService.update_reputation("bad-actor", 95, category="actor", organization_id=org_id)
        assert rep.level == "critical"
        
        updated = ReputationCloudService.update_reputation("bad-actor", 30, organization_id=org_id)
        assert updated.score == 30
        assert updated.level == "low"

def test_reputation_service_submit_feedback(app, federation_setup):
    """Test 7: ReputationCloudService dynamic feedback rating adjustment."""
    with app.app_context():
        org_id = federation_setup['org'].id
        rep = ReputationCloudService.update_reputation("feedback-target", 50, organization_id=org_id)
        
        # Positive feedback raises threat score
        adjusted = ReputationCloudService.submit_feedback("feedback-target", 10, organization_id=org_id)
        assert adjusted.score == 60

        # Negative feedback lowers threat score
        adjusted = ReputationCloudService.submit_feedback("feedback-target", -20, organization_id=org_id)
        assert adjusted.score == 40

def test_reputation_service_bulk_lookup(app, federation_setup):
    """Test 8: ReputationCloudService bulk lookup rankings helper."""
    with app.app_context():
        org_id = federation_setup['org'].id
        ReputationCloudService.update_reputation("a", 70, organization_id=org_id)
        ReputationCloudService.update_reputation("b", 80, organization_id=org_id)
        
        results = ReputationCloudService.bulk_lookup(["a", "b", "c"], org_id)
        assert len(results) == 3
        assert results[0]['score'] == 70
        assert results[2]['category'] == 'unknown'

def test_federated_ai_service_register(app, federation_setup):
    """Test 9: FederatedAIService registers agents."""
    with app.app_context():
        org_id = federation_setup['org'].id
        agent = FederatedAIService.register_agent("AI Coordinator Alpha", "SOC Agent", "active", org_id)
        assert agent.id is not None
        assert agent.status == "active"

def test_federated_ai_service_correlate(app, federation_setup):
    """Test 10: FederatedAIService performs cross-region correlation logic."""
    with app.app_context():
        org_id = federation_setup['org'].id
        # Register agents & meshes
        FederatedAIService.register_agent("A1", organization_id=org_id)
        mesh = SecurityMesh(source_region="us-east", destination_region="eu-west", status="active", organization_id=org_id)
        db.session.add(mesh)
        db.session.commit()
        
        # Set reputation high for threat indicator
        ReputationCloudService.update_reputation("198.51.100.100", 85, organization_id=org_id)
        
        res = FederatedAIService.correlate_intelligence("198.51.100.100", org_id)
        assert res['reputation_score'] == 85
        assert 'us-east' in res['detected_regions']
        assert len(res['recommendations']) > 0

def test_federation_api_get_agents(client, federation_setup):
    """Test 11: GET /api/v1/federation API list readout."""
    resp = client.get(f'/api/v1/cloud/federation?org_id={federation_setup["org"].id}', headers=federation_setup['headers'])
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert 'agents' in data

def test_federation_api_register_agent(client, federation_setup):
    """Test 12: POST /api/v1/federation/register API endpoint."""
    resp = client.post(
        '/api/v1/cloud/federation/register',
        json={
            'name': 'API Agent',
            'agent_type': 'CTI Agent',
            'organization_id': federation_setup['org'].id
        },
        headers=federation_setup['headers']
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data['name'] == 'API Agent'

def test_federation_api_correlate(client, federation_setup):
    """Test 13: POST /api/v1/federation/correlate threat detection API."""
    resp = client.post(
        '/api/v1/cloud/federation/correlate',
        json={
            'indicator': '198.51.100.42',
            'organization_id': federation_setup['org'].id
        },
        headers=federation_setup['headers']
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['indicator'] == '198.51.100.42'
    assert 'correlation_status' in data

def test_reputation_api_endpoints(client, federation_setup):
    """Test 14: GET and POST /api/v1/reputation lookup and update API flow."""
    # Update score
    resp = client.post(
        '/api/v1/cloud/reputation/update',
        json={
            'entity_value': 'malicious-ip',
            'score': 75,
            'category': 'ioc',
            'organization_id': federation_setup['org'].id
        },
        headers=federation_setup['headers']
    )
    assert resp.status_code == 200
    
    # Lookup score
    resp = client.get(f'/api/v1/cloud/reputation?entity=malicious-ip&org_id={federation_setup["org"].id}', headers=federation_setup['headers'])
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['score'] == 75

def test_federation_admin_dashboard_access(client, federation_setup):
    """Test 15: Render admin federated AI coordination dashboard."""
    client.post('/admin/login', data={'username': 'fed_admin', 'password': 'AdminPass123!'})
    resp = client.get(f'/admin/cloud/federation?org_id={federation_setup["org"].id}')
    assert resp.status_code == 200
    # The page renders admin.html which contains 'Admin Dashboard' in the base template
    assert b"Admin" in resp.data
