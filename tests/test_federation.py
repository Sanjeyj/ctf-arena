"""
Unit and Integration tests for Step 4 Federation.
"""
import pytest
import json
from app.extensions import db
from app.models.organization_trust import OrganizationTrust
from app.models.organization import Organization
from app.research.routes import create_jwt

@pytest.fixture
def fed_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(OrganizationTrust).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org1 = Organization(name="Federation Org 1", slug="fed-org-1", plan_type="enterprise")
        org2 = Organization(name="Federation Org 2", slug="fed-org-2", plan_type="enterprise")
        db.session.add_all([org1, org2])
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "fed_admin"}, secret)

        yield {
            "org1": org1,
            "org2": org2,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_trust_link_creation(app, fed_setup):
    """Test establishing trusted connection bridges between organizations."""
    with app.app_context():
        org1 = fed_setup['org1']
        org2 = fed_setup['org2']

        trust = OrganizationTrust(
            source_org_id=org1.id,
            target_org_id=org2.id,
            relationship="trusted",
            capabilities="challenge_sharing, scoreboard_sharing"
        )
        db.session.add(trust)
        db.session.commit()

        assert trust.id is not None
        assert trust.relationship == "trusted"
        assert "scoreboard_sharing" in trust.capabilities

        # Check relationships backref
        assert org1.trusts_initiated[0].id == trust.id
        assert org2.trusts_received[0].id == trust.id

def test_federation_api_endpoints(client, fed_setup):
    """Test GET /api/v1/federation REST route."""
    headers = fed_setup['headers']
    org1 = fed_setup['org1']
    org2 = fed_setup['org2']

    # Seed bridge
    with client.application.app_context():
        trust = OrganizationTrust(
            source_org_id=org1.id,
            target_org_id=org2.id,
            relationship="pending",
            capabilities="research_exchange"
        )
        db.session.add(trust)
        db.session.commit()

    resp = client.get(f'/api/v1/federation?org_id={org1.id}', headers=headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['count'] == 1
    assert data['federation_links'][0]['relationship'] == "pending"
    assert "research_exchange" in data['federation_links'][0]['capabilities']


def test_trust_link_relationship_defaults(app, fed_setup):
    """Test trust bridge initializes status as pending by default."""
    with app.app_context():
        org1 = fed_setup['org1']
        org2 = fed_setup['org2']
        trust = OrganizationTrust(source_org_id=org1.id, target_org_id=org2.id)
        db.session.add(trust)
        db.session.commit()
        assert trust.relationship == "pending"


def test_trust_link_capabilities_empty(app, fed_setup):
    """Test trust link initialized with no capabilities returns empty list serialization."""
    with app.app_context():
        org1 = fed_setup['org1']
        org2 = fed_setup['org2']
        trust = OrganizationTrust(source_org_id=org1.id, target_org_id=org2.id, capabilities=None)
        db.session.add(trust)
        db.session.commit()
        assert trust.to_dict()['capabilities'] == []


def test_federation_api_missing_token(client, fed_setup):
    """Test GET /api/v1/federation triggers 401 unauthorized when Bearer token is omitted."""
    org1 = fed_setup['org1']
    resp = client.get(f'/api/v1/federation?org_id={org1.id}')
    assert resp.status_code == 401

