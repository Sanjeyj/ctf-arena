"""
Unit and Integration tests for Phase 24 Global Cyber Security Cloud.
Contains 15 test cases.
"""
import pytest
import json
from app.extensions import db
from app.models.cloud_region import CloudRegion
from app.models.cloud_node import CloudNode
from app.models.cloud_service import CloudService
from app.models.organization import Organization
from app.services.cloud_service_manager import CloudServiceManager
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password

@pytest.fixture
def cloud_setup(app):
    with app.app_context():
        # Setup roles/perms
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(CloudNode).delete()
        db.session.query(CloudRegion).delete()
        db.session.query(CloudService).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Cloud Org", slug="cloud-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        # Create test admin user
        UserRepository.create(
            username="cloud_admin",
            password_hash=hash_password("AdminPass123!"),
            display_name="Cloud Admin",
            role_name="Admin"
        )

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "cloud_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_cloud_region_creation(app, cloud_setup):
    """Test 1: CloudRegion model fields and representations."""
    with app.app_context():
        region = CloudRegion(name="US East", slug="us-east", region_code="us-east-1", organization_id=cloud_setup['org'].id)
        db.session.add(region)
        db.session.commit()
        assert region.name == "US East"
        assert "us-east" in repr(region)

def test_cloud_region_to_dict(app, cloud_setup):
    """Test 2: CloudRegion dict serialization format."""
    with app.app_context():
        region = CloudRegion(name="EU West", slug="eu-west", location="Dublin", organization_id=cloud_setup['org'].id)
        db.session.add(region)
        db.session.commit()
        d = region.to_dict()
        assert d['name'] == "EU West"
        assert d['slug'] == "eu-west"
        assert d['location'] == "Dublin"

def test_cloud_node_creation(app, cloud_setup):
    """Test 3: CloudNode model fields and relationship mapping."""
    with app.app_context():
        region = CloudRegion(name="Asia South", slug="asia-south", organization_id=cloud_setup['org'].id)
        db.session.add(region)
        db.session.commit()
        
        node = CloudNode(region_id=region.id, name="Mumbai SOC", node_type="SOC Node", status="online", organization_id=cloud_setup['org'].id)
        db.session.add(node)
        db.session.commit()
        
        assert node.name == "Mumbai SOC"
        assert node.region.name == "Asia South"
        assert "SOC Node" in repr(node)

def test_cloud_node_to_dict(app, cloud_setup):
    """Test 4: CloudNode serialization helper."""
    with app.app_context():
        region = CloudRegion(name="Private Cloud", slug="private-cloud", organization_id=cloud_setup['org'].id)
        db.session.add(region)
        db.session.commit()
        
        node = CloudNode(region_id=region.id, name="Private AI Node", node_type="AI Node", status="degraded", organization_id=cloud_setup['org'].id)
        db.session.add(node)
        db.session.commit()
        
        d = node.to_dict()
        assert d['name'] == "Private AI Node"
        assert d['status'] == "degraded"

def test_cloud_service_creation(app, cloud_setup):
    """Test 5: CloudService model structure validation."""
    with app.app_context():
        svc = CloudService(name="Global SIEM", service_type="SIEM", status="running", organization_id=cloud_setup['org'].id)
        db.session.add(svc)
        db.session.commit()
        assert svc.name == "Global SIEM"
        assert "running" in repr(svc)

def test_cloud_service_to_dict(app, cloud_setup):
    """Test 6: CloudService serialization converter."""
    with app.app_context():
        svc = CloudService(name="Global LMS", service_type="LMS", status="paused", organization_id=cloud_setup['org'].id)
        db.session.add(svc)
        db.session.commit()
        d = svc.to_dict()
        assert d['name'] == "Global LMS"
        assert d['status'] == "paused"

def test_manager_create_region(app, cloud_setup):
    """Test 7: CloudServiceManager creates region successfully."""
    with app.app_context():
        region = CloudServiceManager.create_region("US East 2", "us-east-2", "us-east-2", "Ohio", cloud_setup['org'].id)
        assert region.id is not None
        assert region.slug == "us-east-2"

def test_manager_create_node(app, cloud_setup):
    """Test 8: CloudServiceManager creates node correctly."""
    with app.app_context():
        region = CloudServiceManager.create_region("EU Central", "eu-central", "eu-central-1", "Frankfurt", cloud_setup['org'].id)
        node = CloudServiceManager.create_node(region.id, "Frankfurt CTI", "CTI Node", "online", cloud_setup['org'].id)
        assert node.id is not None
        assert node.status == "online"

def test_manager_create_service(app, cloud_setup):
    """Test 9: CloudServiceManager creates cloud service."""
    with app.app_context():
        service = CloudServiceManager.create_service("Fed CTI Hub", "CTI", "running", cloud_setup['org'].id)
        assert service.id is not None
        assert service.status == "running"

def test_manager_sync_replication(app, cloud_setup):
    """Test 10: CloudServiceManager replicate config sync simulator."""
    with app.app_context():
        region = CloudServiceManager.create_region("Test Region", "test-region", organization_id=cloud_setup['org'].id)
        node = CloudServiceManager.create_node(region.id, "Test Node", organization_id=cloud_setup['org'].id)
        service = CloudServiceManager.create_service("Test Service", organization_id=cloud_setup['org'].id)
        
        res = CloudServiceManager.sync_replication(cloud_setup['org'].id)
        assert res['success'] is True
        assert res['synchronized_regions'] == 1
        assert res['synchronized_nodes'] == 1
        assert res['synchronized_services'] == 1

def test_api_get_cloud_config(client, cloud_setup):
    """Test 11: GET /api/v1/cloud API configuration readout."""
    resp = client.get(f'/api/v1/cloud?org_id={cloud_setup["org"].id}', headers=cloud_setup['headers'])
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert 'regions' in data
    assert 'nodes' in data
    assert 'services' in data

def test_api_create_region(client, cloud_setup):
    """Test 12: POST /api/v1/cloud/region API endpoint."""
    resp = client.post(
        '/api/v1/cloud/region',
        json={
            'name': 'API Region',
            'slug': 'api-region',
            'organization_id': cloud_setup['org'].id
        },
        headers=cloud_setup['headers']
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data['slug'] == 'api-region'

def test_api_create_node(client, cloud_setup):
    """Test 13: POST /api/v1/cloud/node API endpoint."""
    # First create a region via manager
    with client.application.app_context():
        region = CloudServiceManager.create_region("API Target Region", "api-target-region")
        region_id = region.id
        
    resp = client.post(
        '/api/v1/cloud/node',
        json={
            'region_id': region_id,
            'name': 'API Target Node',
            'node_type': 'AI Node',
            'organization_id': cloud_setup['org'].id
        },
        headers=cloud_setup['headers']
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data['name'] == 'API Target Node'

def test_api_create_service(client, cloud_setup):
    """Test 14: POST /api/v1/cloud/service API endpoint."""
    resp = client.post(
        '/api/v1/cloud/service',
        json={
            'name': 'API Target Service',
            'service_type': 'SOC',
            'organization_id': cloud_setup['org'].id
        },
        headers=cloud_setup['headers']
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data['name'] == 'API Target Service'

def test_admin_dashboard_access(client, cloud_setup):
    """Test 15: Render admin cloud dashboard pages."""
    # Login as admin user
    client.post('/admin/login', data={'username': 'cloud_admin', 'password': 'AdminPass123!'})
    
    resp = client.get('/admin/cloud')
    assert resp.status_code == 200
    assert b"Admin" in resp.data

    resp = client.get('/admin/cloud/regions')
    assert resp.status_code == 200
    assert b"Admin" in resp.data
