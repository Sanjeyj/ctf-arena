"""
Unit and Integration tests for Step 2 Security Mesh Federation & Route latency.
Contains 14 test cases.
"""
import pytest
import json
from app.extensions import db
from app.models.security_mesh import SecurityMesh
from app.models.mesh_route import MeshRoute
from app.models.organization import Organization
from app.services.mesh_service import MeshService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password

@pytest.fixture
def mesh_setup(app):
    with app.app_context():
        # Setup roles/perms
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(SecurityMesh).delete()
        db.session.query(MeshRoute).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Mesh Org", slug="mesh-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        # Create test admin user
        UserRepository.create(
            username="mesh_admin",
            password_hash=hash_password("AdminPass123!"),
            display_name="Mesh Admin",
            role_name="Admin"
        )

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "mesh_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_security_mesh_creation(app, mesh_setup):
    """Test 1: SecurityMesh model registration and representation."""
    with app.app_context():
        mesh = SecurityMesh(source_region="us-east", destination_region="eu-west", trust_level="trusted", status="active", organization_id=mesh_setup['org'].id)
        db.session.add(mesh)
        db.session.commit()
        assert mesh.source_region == "us-east"
        assert "us-east" in repr(mesh)

def test_security_mesh_to_dict(app, mesh_setup):
    """Test 2: SecurityMesh dict serialization helper."""
    with app.app_context():
        mesh = SecurityMesh(source_region="asia-south", destination_region="private-cloud", trust_level="restricted", status="degraded", organization_id=mesh_setup['org'].id)
        db.session.add(mesh)
        db.session.commit()
        d = mesh.to_dict()
        assert d['source_region'] == "asia-south"
        assert d['trust_level'] == "restricted"

def test_mesh_route_creation(app, mesh_setup):
    """Test 3: MeshRoute model database mappings."""
    with app.app_context():
        route = MeshRoute(source_node="US-SOC-1", destination_node="EU-SOC-1", weight=2, latency=25.5, status="active", organization_id=mesh_setup['org'].id)
        db.session.add(route)
        db.session.commit()
        assert route.source_node == "US-SOC-1"
        assert route.latency == 25.5
        assert "US-SOC-1" in repr(route)

def test_mesh_route_to_dict(app, mesh_setup):
    """Test 4: MeshRoute serialization dict schema."""
    with app.app_context():
        route = MeshRoute(source_node="US-AI-1", destination_node="ASIA-AI-1", weight=5, latency=120.0, status="degraded", organization_id=mesh_setup['org'].id)
        db.session.add(route)
        db.session.commit()
        d = route.to_dict()
        assert d['source_node'] == "US-AI-1"
        assert d['latency'] == 120.0

def test_mesh_service_establish_mesh(app, mesh_setup):
    """Test 5: MeshService establishes mesh connection."""
    with app.app_context():
        mesh = MeshService.establish_mesh("us-east", "asia-south", "federated", "active", mesh_setup['org'].id)
        assert mesh.id is not None
        assert mesh.trust_level == "federated"

def test_mesh_service_add_route(app, mesh_setup):
    """Test 6: MeshService registers router link weight."""
    with app.app_context():
        route = MeshService.add_route("US-SOC-1", "ASIA-SOC-1", 1, 10.0, "active", mesh_setup['org'].id)
        assert route.id is not None
        assert route.latency == 10.0

def test_mesh_service_update_mesh_status(app, mesh_setup):
    """Test 7: MeshService updates trust tunnel state."""
    with app.app_context():
        mesh = MeshService.establish_mesh("us-east", "eu-west", organization_id=mesh_setup['org'].id)
        updated = MeshService.update_mesh_status(mesh.id, "degraded")
        assert updated.status == "degraded"

def test_mesh_service_update_route_status(app, mesh_setup):
    """Test 8: MeshService updates route weight status."""
    with app.app_context():
        route = MeshService.add_route("US-AI-1", "EU-AI-1", organization_id=mesh_setup['org'].id)
        updated = MeshService.update_route_status(route.id, "offline")
        assert updated.status == "offline"

def test_mesh_service_calculate_optimal_path(app, mesh_setup):
    """Test 9: MeshService computes optimal latency shortest path."""
    with app.app_context():
        MeshService.add_route("US-SOC-1", "EU-SOC-1", weight=1, latency=20.0, organization_id=mesh_setup['org'].id)
        res = MeshService.calculate_optimal_path("US-SOC-1", "EU-SOC-1", mesh_setup['org'].id)
        assert res['total_latency'] == 20.0
        assert res['path'] == ["US-SOC-1", "EU-SOC-1"]

def test_mesh_api_get_mesh(client, mesh_setup):
    """Test 10: GET /api/v1/mesh configuration readout."""
    resp = client.get(f'/api/v1/mesh?org_id={mesh_setup["org"].id}', headers=mesh_setup['headers'])
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert 'meshes' in data
    assert 'routes' in data

def test_mesh_api_establish_mesh(client, mesh_setup):
    """Test 11: POST /api/v1/mesh/establish endpoint."""
    resp = client.post(
        '/api/v1/mesh/establish',
        json={
            'source_region': 'us-east',
            'destination_region': 'asia-south',
            'organization_id': mesh_setup['org'].id
        },
        headers=mesh_setup['headers']
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data['source_region'] == 'us-east'

def test_mesh_api_add_route(client, mesh_setup):
    """Test 12: POST /api/v1/mesh/route endpoint."""
    resp = client.post(
        '/api/v1/mesh/route',
        json={
            'source_node': 'node-a',
            'destination_node': 'node-b',
            'weight': 3,
            'latency': 45.0,
            'organization_id': mesh_setup['org'].id
        },
        headers=mesh_setup['headers']
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data['source_node'] == 'node-a'

def test_mesh_api_optimize_path(client, mesh_setup):
    """Test 13: POST /api/v1/mesh/optimize path calculation."""
    # First create route with the same org_id to ensure the filter matches
    with client.application.app_context():
        MeshService.add_route("node-x", "node-y", latency=12.5, organization_id=mesh_setup['org'].id)

    resp = client.post(
        '/api/v1/mesh/optimize',
        json={
            'source_node': 'node-x',
            'destination_node': 'node-y',
            'organization_id': mesh_setup['org'].id
        },
        headers=mesh_setup['headers']
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['total_latency'] == 12.5


def test_mesh_admin_dashboard_access(client, mesh_setup):
    """Test 14: Render admin security mesh dashboard."""
    # Login as admin user
    client.post('/admin/login', data={'username': 'mesh_admin', 'password': 'AdminPass123!'})
    resp = client.get('/admin/cloud/mesh')
    assert resp.status_code == 200
    assert b"Admin" in resp.data

