"""
Unit and Integration tests for Step 1 & 8 GRC Compliance & Audits.
Contains 11 test cases.
"""
import pytest
import json
from app.extensions import db
from app.models.governance_framework import GovernanceFramework
from app.models.compliance_control import ComplianceControl
from app.models.audit_finding import AuditFinding
from app.models.organization import Organization
from app.research.routes import create_jwt

@pytest.fixture
def compliance_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(AuditFinding).delete()
        db.session.query(ComplianceControl).delete()
        db.session.query(GovernanceFramework).delete()
        db.session.commit()

        org = Organization(name="GRC Org", slug="grc-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        fw = GovernanceFramework(name="ISO27001", description="ISO standard", organization_id=org.id)
        db.session.add(fw)
        db.session.commit()

        ctrl = ComplianceControl(framework_id=fw.id, control_code="A.12.6.1", status="passed", organization_id=org.id)
        db.session.add(ctrl)
        db.session.commit()

        finding = AuditFinding(control_id=ctrl.id, title="Credential Leak Gaps", severity="high", status="open", organization_id=org.id)
        db.session.add(finding)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "grc_admin"}, secret)

        yield {
            "org": org,
            "fw": fw,
            "ctrl": ctrl,
            "finding": finding,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_governance_framework_creation(app, compliance_setup):
    """Test 1: GovernanceFramework database attributes insertion."""
    with app.app_context():
        fw = db.session.get(GovernanceFramework, compliance_setup['fw'].id)
        assert fw.name == "ISO27001"
        assert "ISO standard" in fw.description

def test_governance_framework_repr(app, compliance_setup):
    """Test 2: GovernanceFramework model representation string."""
    with app.app_context():
        fw = db.session.get(GovernanceFramework, compliance_setup['fw'].id)
        assert "ISO27001" in repr(fw)

def test_compliance_control_creation(app, compliance_setup):
    """Test 3: ComplianceControl mapped parameters database storage."""
    with app.app_context():
        ctrl = db.session.get(ComplianceControl, compliance_setup['ctrl'].id)
        assert ctrl.control_code == "A.12.6.1"
        assert ctrl.status == "passed"

def test_compliance_control_repr(app, compliance_setup):
    """Test 4: ComplianceControl model representation string."""
    with app.app_context():
        ctrl = db.session.get(ComplianceControl, compliance_setup['ctrl'].id)
        assert "A.12.6.1" in repr(ctrl)

def test_compliance_control_cascade_delete(app, compliance_setup):
    """Test 5: ComplianceControl foreign keys cascade deletion."""
    with app.app_context():
        fw_id = compliance_setup['fw'].id
        db.session.delete(db.session.get(GovernanceFramework, fw_id))
        db.session.commit()
        assert ComplianceControl.query.filter_by(framework_id=fw_id).count() == 0

def test_audit_finding_creation(app, compliance_setup):
    """Test 6: AuditFinding gap record creation status and attributes."""
    with app.app_context():
        f = db.session.get(AuditFinding, compliance_setup['finding'].id)
        assert f.title == "Credential Leak Gaps"
        assert f.status == "open"

def test_audit_finding_repr(app, compliance_setup):
    """Test 7: AuditFinding representation string."""
    with app.app_context():
        f = db.session.get(AuditFinding, compliance_setup['finding'].id)
        assert "Credential Leak Gaps" in repr(f)

def test_audit_finding_cascade_delete(app, compliance_setup):
    """Test 8: AuditFinding cascade deletes on parent control drop."""
    with app.app_context():
        ctrl_id = compliance_setup['ctrl'].id
        db.session.delete(db.session.get(ComplianceControl, ctrl_id))
        db.session.commit()
        assert AuditFinding.query.filter_by(control_id=ctrl_id).count() == 0

def test_compliance_rest_endpoint_scoring(client, compliance_setup):
    """Test 9: GET /api/v1/compliance returns accurate percentage scores."""
    headers = compliance_setup['headers']
    resp = client.get('/api/v1/compliance', headers=headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['compliance_score'] == 100.0
    assert data['passed'] == 1

def test_audits_rest_endpoint_list(client, compliance_setup):
    """Test 10: GET /api/v1/audits returns configured findings list."""
    headers = compliance_setup['headers']
    resp = client.get('/api/v1/audits', headers=headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['count'] == 1
    assert data['audit_findings'][0]['title'] == "Credential Leak Gaps"

def test_audits_rest_endpoint_requires_auth(client):
    """Test 11: GET /api/v1/audits rejects requests with missing JWT tokens."""
    resp = client.get('/api/v1/audits')
    assert resp.status_code == 401
