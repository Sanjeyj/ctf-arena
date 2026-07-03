"""
Unit and Integration tests for Phase 25 Cyber Resilience Platform — Business Continuity.
Contains 8 test cases covering disaster recovery plans, BCP services, and RTO/RPO evaluation.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.business_process import BusinessProcess
from app.models.disaster_recovery_plan import DisasterRecoveryPlan
from app.services.bcm_service import BCMService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def bcp_setup(app):
    """Fixture for BCP tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(DisasterRecoveryPlan).delete()
        db.session.query(BusinessProcess).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="BCP Org", slug="bcp-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="bcp_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="BCP Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "bcp_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_disaster_recovery_plan_creation(app, bcp_setup):
    """Test 1: DisasterRecoveryPlan model fields and defaults."""
    with app.app_context():
        plan = DisasterRecoveryPlan(
            plan_name="Website Failover",
            strategy="Warm standby activation",
            priority=1,
            approval_status="draft",
            organization_id=bcp_setup['org'].id
        )
        db.session.add(plan)
        db.session.commit()
        assert plan.plan_name == "Website Failover"
        assert plan.approval_status == "draft"
        assert "Website Failover" in repr(plan)


def test_disaster_recovery_plan_to_dict(app, bcp_setup):
    """Test 2: DisasterRecoveryPlan dict serialization."""
    with app.app_context():
        plan = DisasterRecoveryPlan(
            plan_name="Database Backup",
            strategy="Cold restore from S3",
            priority=2,
            organization_id=bcp_setup['org'].id
        )
        db.session.add(plan)
        db.session.commit()
        d = plan.to_dict()
        assert d['plan_name'] == "Database Backup"
        assert d['priority'] == 2
        assert d['approval_status'] == "draft"


def test_bcm_service_generate_plan(app, bcp_setup):
    """Test 3: BCMService.generate_plan creates and persists DRP record."""
    with app.app_context():
        plan = BCMService.generate_plan(
            plan_name="Email Recovery Plan",
            strategy="Failover to backup MX",
            recovery_steps=["1. Switch DNS MX records", "2. Verify mail flow"],
            priority=3,
            organization_id=bcp_setup['org'].id
        )
        assert plan.id is not None
        assert plan.plan_name == "Email Recovery Plan"
        assert plan.priority == 3


def test_bcm_service_evaluate_rto_no_violations(app, bcp_setup):
    """Test 4: BCMService.evaluate_rto shows 100% compliance with no low-RTO processes."""
    with app.app_context():
        bp = BusinessProcess(
            name="Reporting Module", criticality="low", rto=24.0, status="active",
            organization_id=bcp_setup['org'].id
        )
        db.session.add(bp)
        db.session.commit()
        result = BCMService.evaluate_rto(bcp_setup['org'].id)
        assert result['compliance_rate_pct'] == 100.0
        assert result['violations'] == []


def test_bcm_service_evaluate_rto_with_violation(app, bcp_setup):
    """Test 5: BCMService.evaluate_rto detects sub-2h RTO processes as violations."""
    with app.app_context():
        bp = BusinessProcess(
            name="Payment Gateway", criticality="critical", rto=1.0, status="active",
            organization_id=bcp_setup['org'].id
        )
        db.session.add(bp)
        db.session.commit()
        result = BCMService.evaluate_rto(bcp_setup['org'].id)
        assert len(result['violations']) > 0
        assert result['violations'][0]['name'] == "Payment Gateway"


def test_bcm_service_evaluate_rpo_no_violations(app, bcp_setup):
    """Test 6: BCMService.evaluate_rpo shows 100% compliance with rpo > 1 hour."""
    with app.app_context():
        bp = BusinessProcess(
            name="Inventory System", criticality="medium", rpo=4.0, status="active",
            organization_id=bcp_setup['org'].id
        )
        db.session.add(bp)
        db.session.commit()
        result = BCMService.evaluate_rpo(bcp_setup['org'].id)
        assert result['compliance_rate_pct'] == 100.0
        assert result['violations'] == []


def test_api_create_process(client, bcp_setup):
    """Test 7: POST /api/v1/resilience/processes creates a process record."""
    resp = client.post(
        '/api/v1/resilience/processes',
        json={
            'name': 'Finance Ledger',
            'owner': 'CFO',
            'criticality': 'critical',
            'rto': 2.0,
            'rpo': 1.0,
            'organization_id': bcp_setup['org'].id
        },
        headers=bcp_setup['headers']
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data['name'] == 'Finance Ledger'
    assert data['criticality'] == 'critical'


def test_api_create_process_missing_name(client, bcp_setup):
    """Test 8: POST /api/v1/resilience/processes rejects missing name."""
    resp = client.post(
        '/api/v1/resilience/processes',
        json={'criticality': 'high'},
        headers=bcp_setup['headers']
    )
    assert resp.status_code == 400
