"""
Unit and Integration tests for Phase 25 Cyber Resilience Platform — Vendor Risk.
Contains 8 test cases covering vendor model creation, services, and API endpoints.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.third_party_vendor import ThirdPartyVendor
from app.models.vendor_assessment import VendorAssessment
from app.services.vendor_risk_service import VendorRiskService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def vendor_setup(app):
    """Fixture for vendor risk tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(VendorAssessment).delete()
        db.session.query(ThirdPartyVendor).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Vendor Org", slug="vendor-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="vendor_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Vendor Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "vendor_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_third_party_vendor_creation(app, vendor_setup):
    """Test 1: ThirdPartyVendor model fields and defaults."""
    with app.app_context():
        vendor = ThirdPartyVendor(
            vendor_name="Cloudflare",
            service_type="CDN",
            risk_score=15.0,
            contract_status="active",
            organization_id=vendor_setup['org'].id
        )
        db.session.add(vendor)
        db.session.commit()
        assert vendor.vendor_name == "Cloudflare"
        assert vendor.risk_score == 15.0
        assert "Cloudflare" in repr(vendor)


def test_third_party_vendor_to_dict(app, vendor_setup):
    """Test 2: ThirdPartyVendor dict serialization."""
    with app.app_context():
        vendor = ThirdPartyVendor(
            vendor_name="AWS",
            service_type="cloud",
            risk_score=20.0,
            contract_status="active",
            organization_id=vendor_setup['org'].id
        )
        db.session.add(vendor)
        db.session.commit()
        d = vendor.to_dict()
        assert d['vendor_name'] == "AWS"
        assert d['service_type'] == "cloud"
        assert d['risk_score'] == 20.0


def test_vendor_assessment_creation(app, vendor_setup):
    """Test 3: VendorAssessment model fields and relationship."""
    with app.app_context():
        vendor = ThirdPartyVendor(
            vendor_name="Salesforce",
            risk_score=30.0,
            organization_id=vendor_setup['org'].id
        )
        db.session.add(vendor)
        db.session.commit()

        assessment = VendorAssessment(
            vendor_id=vendor.id,
            assessment_score=85.0,
            compliance_score=90.0,
            recommendations="Enable MFA for all vendor access.",
            organization_id=vendor_setup['org'].id
        )
        db.session.add(assessment)
        db.session.commit()
        assert assessment.assessment_score == 85.0
        assert assessment.vendor.vendor_name == "Salesforce"


def test_vendor_assessment_to_dict(app, vendor_setup):
    """Test 4: VendorAssessment dict serialization."""
    with app.app_context():
        vendor = ThirdPartyVendor(
            vendor_name="Slack",
            risk_score=25.0,
            organization_id=vendor_setup['org'].id
        )
        db.session.add(vendor)
        db.session.commit()

        assessment = VendorAssessment(
            vendor_id=vendor.id,
            assessment_score=70.0,
            compliance_score=80.0,
            organization_id=vendor_setup['org'].id
        )
        db.session.add(assessment)
        db.session.commit()
        d = assessment.to_dict()
        assert d['assessment_score'] == 70.0
        assert d['compliance_score'] == 80.0


def test_vendor_risk_service_assess_vendor(app, vendor_setup):
    """Test 5: VendorRiskService.assess_vendor creates and persists vendor."""
    with app.app_context():
        vendor = VendorRiskService.assess_vendor(
            vendor_name="Okta",
            service_type="IAM",
            initial_risk=35.0,
            organization_id=vendor_setup['org'].id
        )
        assert vendor.id is not None
        assert vendor.vendor_name == "Okta"
        assert vendor.risk_score == 35.0


def test_vendor_risk_service_update_score(app, vendor_setup):
    """Test 6: VendorRiskService.update_score recalculates risk from audit."""
    with app.app_context():
        vendor = VendorRiskService.assess_vendor(
            vendor_name="Zoom",
            service_type="conferencing",
            initial_risk=70.0,
            organization_id=vendor_setup['org'].id
        )
        # After a good audit, risk should decrease
        updated = VendorRiskService.update_score(vendor.id, compliance_score=90.0, assessment_score=88.0)
        # risk = 100 - (90*0.5 + 88*0.5) = 100 - 89 = 11.0
        assert updated.risk_score < 70.0
        assert updated.risk_score == 11.0


def test_api_get_vendors(client, vendor_setup):
    """Test 7: GET /api/v1/vendors returns a list."""
    resp = client.get(
        f'/api/v1/vendors?org_id={vendor_setup["org"].id}',
        headers=vendor_setup['headers']
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data, list)


def test_api_post_vendor(client, vendor_setup):
    """Test 8: POST /api/v1/vendors creates a vendor entry."""
    resp = client.post(
        '/api/v1/vendors',
        json={
            'vendor_name': 'PagerDuty',
            'service_type': 'alerting',
            'risk_score': 22.5,
            'organization_id': vendor_setup['org'].id
        },
        headers=vendor_setup['headers']
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data['vendor_name'] == 'PagerDuty'
    assert data['risk_score'] == 22.5
