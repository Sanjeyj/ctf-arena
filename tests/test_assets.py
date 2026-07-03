"""
Unit and Integration tests for Step 2 Asset Management.
"""
import pytest
import json
from app.extensions import db
from app.models.asset import Asset
from app.models.asset_group import AssetGroup
from app.models.asset_tag import AssetTag
from app.models.organization import Organization
from app.services.asset_service import AssetService
from app.research.routes import create_jwt

@pytest.fixture
def asset_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(AssetTag).delete()
        db.session.query(Asset).delete()
        db.session.query(AssetGroup).delete()
        db.session.commit()

        org = Organization(name="Asset Org", slug="asset-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        group = AssetGroup(name="DMZ Servers", description="Public facing servers", organization_id=org.id)
        db.session.add(group)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "asset_admin"}, secret)

        yield {
            "org": org,
            "group": group,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_asset_discovery(app, asset_setup):
    """Test discovering and configuring inventory assets."""
    with app.app_context():
        org = asset_setup['org']
        group = asset_setup['group']
        
        asset = AssetService.discover(
            name="Web-Server-01", type_label="server", criticality=8, ip_address="10.0.1.5", org_id=org.id
        )
        asset.group_id = group.id
        db.session.commit()

        assert asset.id is not None
        assert asset.name == "Web-Server-01"
        assert asset.criticality == 8
        assert asset.group.name == "DMZ Servers"

def test_asset_tags_assignment(app, asset_setup):
    """Test assigning tags to active assets."""
    with app.app_context():
        org = asset_setup['org']
        asset = AssetService.discover(name="Db-Core", type_label="server", org_id=org.id)

        tags = {"env": "prod", "owner": "secops"}
        assigned = AssetService.assign_tags(asset.id, tags, org_id=org.id)
        assert len(assigned) == 2
        assert asset.tags.filter_by(key="env").first().value == "prod"

def test_critical_assets_filter(app, asset_setup):
    """Test querying only high criticality target elements (criticality >= 7)."""
    with app.app_context():
        org = asset_setup['org']
        # Critical
        AssetService.discover("Core-Router", criticality=9, org_id=org.id)
        # Non-critical
        AssetService.discover("User-Workstation", criticality=3, org_id=org.id)

        criticals = AssetService.critical_assets(org.id)
        assert len(criticals) == 1
        assert criticals[0].name == "Core-Router"

def test_assets_api_endpoints(client, asset_setup):
    """Test REST endpoints for assets management."""
    headers = asset_setup['headers']
    org = asset_setup['org']

    resp = client.get('/api/v1/assets', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data)['count'] == 0

    resp = client.post('/api/v1/assets', data=json.dumps({
        "name": "Cloud-Storage-Bucket",
        "type_label": "cloud",
        "criticality": 7,
        "org_id": org.id
    }), content_type='application/json', headers=headers)
    assert resp.status_code == 201

    resp = client.get('/api/v1/assets', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data)['count'] == 1


def test_asset_discovery_invalid_criticality(app, asset_setup):
    """Test discovering asset stores default values."""
    with app.app_context():
        org = asset_setup['org']
        asset = AssetService.discover(name="Default-Asset", org_id=org.id)
        assert asset.criticality == 5


def test_asset_discovery_duplicate_name_fails(app, asset_setup):
    """Test creating duplicate asset names raises database IntegrityError."""
    with app.app_context():
        org = asset_setup['org']
        AssetService.discover(name="Dup-Asset", org_id=org.id)
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            AssetService.discover(name="Dup-Asset", org_id=org.id)


def test_asset_group_serialization(app, asset_setup):
    """Test AssetGroup model dictionary serialization."""
    with app.app_context():
        group = asset_setup['group']
        gd = group.to_dict()
        assert gd['name'] == "DMZ Servers"
        assert "description" in gd


def test_asset_tag_serialization(app, asset_setup):
    """Test AssetTag dictionary serialization includes asset identification."""
    with app.app_context():
        org = asset_setup['org']
        asset = AssetService.discover(name="Tag-Asset", org_id=org.id)
        tag = AssetTag(asset_id=asset.id, key="tier", value="critical", organization_id=org.id)
        db.session.add(tag)
        db.session.commit()
        td = tag.to_dict()
        assert td['asset_id'] == asset.id
        assert td['key'] == "tier"

