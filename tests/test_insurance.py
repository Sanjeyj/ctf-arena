"""
Unit and Integration tests for Phase 25 Cyber Resilience Platform — Cyber Insurance.
Contains 8 test cases covering insurance model, services, and API endpoints.
"""
import pytest
import json
import datetime
from app.extensions import db
from app.models.organization import Organization
from app.models.insurance_policy import InsurancePolicy
from app.models.business_process import BusinessProcess
from app.models.business_impact_analysis import BusinessImpactAnalysis
from app.services.insurance_service import InsuranceService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def insurance_setup(app):
    """Fixture for cyber insurance tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(BusinessImpactAnalysis).delete()
        db.session.query(BusinessProcess).delete()
        db.session.query(InsurancePolicy).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Insurance Org", slug="insurance-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="insurance_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Insurance Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "insurance_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_insurance_policy_creation(app, insurance_setup):
    """Test 1: InsurancePolicy model fields and defaults."""
    with app.app_context():
        policy = InsurancePolicy(
            provider="CyberGuard Insurance",
            coverage=1000000.0,
            deductible=25000.0,
            renewal_date=datetime.datetime(2027, 1, 1),
            organization_id=insurance_setup['org'].id
        )
        db.session.add(policy)
        db.session.commit()
        assert policy.provider == "CyberGuard Insurance"
        assert policy.coverage == 1000000.0
        assert policy.deductible == 25000.0
        assert "CyberGuard Insurance" in repr(policy)


def test_insurance_policy_to_dict(app, insurance_setup):
    """Test 2: InsurancePolicy dict serialization."""
    with app.app_context():
        policy = InsurancePolicy(
            provider="SecureShield Co.",
            coverage=500000.0,
            deductible=10000.0,
            organization_id=insurance_setup['org'].id
        )
        db.session.add(policy)
        db.session.commit()
        d = policy.to_dict()
        assert d['provider'] == "SecureShield Co."
        assert d['coverage'] == 500000.0
        assert d['deductible'] == 10000.0


def test_insurance_service_estimate_losses_no_data(app, insurance_setup):
    """Test 3: InsuranceService.estimate_losses returns default baseline with no BIA."""
    with app.app_context():
        losses = InsuranceService.estimate_losses(insurance_setup['org'].id)
        assert losses == 250000.0  # default baseline


def test_insurance_service_estimate_losses_with_bia(app, insurance_setup):
    """Test 4: InsuranceService.estimate_losses computes from BIA data."""
    with app.app_context():
        org_id = insurance_setup['org'].id
        bp = BusinessProcess(name="E-Commerce Checkout", criticality="critical", organization_id=org_id)
        db.session.add(bp)
        db.session.commit()
        bia = BusinessImpactAnalysis(
            process_id=bp.id,
            financial_impact=4,  # $400,000 exposure
            organization_id=org_id
        )
        db.session.add(bia)
        db.session.commit()
        losses = InsuranceService.estimate_losses(org_id)
        assert losses == 400000.0


def test_insurance_service_estimate_coverage_empty(app, insurance_setup):
    """Test 5: InsuranceService.estimate_coverage returns 0.0 with no policies."""
    with app.app_context():
        coverage = InsuranceService.estimate_coverage(insurance_setup['org'].id)
        assert coverage == 0.0


def test_insurance_service_estimate_coverage_with_policies(app, insurance_setup):
    """Test 6: InsuranceService.estimate_coverage sums active policy coverages."""
    with app.app_context():
        org_id = insurance_setup['org'].id
        p1 = InsurancePolicy(provider="Carrier A", coverage=300000.0, deductible=5000.0, organization_id=org_id)
        p2 = InsurancePolicy(provider="Carrier B", coverage=200000.0, deductible=5000.0, organization_id=org_id)
        db.session.add_all([p1, p2])
        db.session.commit()
        coverage = InsuranceService.estimate_coverage(org_id)
        assert coverage == 500000.0


def test_insurance_service_recommend_policy_gap(app, insurance_setup):
    """Test 7: InsuranceService.recommend_policy identifies gap and suggestions."""
    with app.app_context():
        org_id = insurance_setup['org'].id
        # Create a BIA with high financial impact, no policy coverage
        bp = BusinessProcess(name="Core API", criticality="critical", organization_id=org_id)
        db.session.add(bp)
        db.session.commit()
        bia = BusinessImpactAnalysis(
            process_id=bp.id,
            financial_impact=5,  # $500,000 exposure
            organization_id=org_id
        )
        db.session.add(bia)
        db.session.commit()
        rec = InsuranceService.recommend_policy(org_id)
        assert rec['coverage_gap'] > 0.0
        assert len(rec['recommendations']) > 0


def test_api_get_insurance(client, insurance_setup):
    """Test 8: GET /api/v1/insurance?org_id=X returns coverage recommendations."""
    resp = client.get(
        f'/api/v1/insurance?org_id={insurance_setup["org"].id}',
        headers=insurance_setup['headers']
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert 'estimated_losses' in data
    assert 'recommendations' in data
