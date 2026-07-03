"""
Unit and Integration tests for Step 1 Bug Bounty Platform.
"""
import pytest
import json
from app.extensions import db
from app.models.program import Program
from app.models.vulnerability_report import VulnerabilityReport
from app.models.bounty_reward import BountyReward
from app.models.disclosure import Disclosure
from app.models.organization import Organization
from app.models.user import User
from app.services.auth_service import hash_password
from app.research.routes import create_jwt

@pytest.fixture
def bounty_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(BountyReward).delete()
        db.session.query(Disclosure).delete()
        db.session.query(VulnerabilityReport).delete()
        db.session.query(Program).delete()
        db.session.commit()

        org = Organization(name="Bounty Org", slug="bounty-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        user = User(username="bounty_hunter", email="hunter@bounty.net", password_hash=hash_password("hunter123"))
        db.session.add(user)
        db.session.commit()

        program = Program(
            name="CTF Core Program",
            description="Testing core web portal scope",
            program_type="public",
            reward_min=100,
            reward_max=1000,
            organization_id=org.id
        )
        db.session.add(program)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "bounty_hunter"}, secret)

        yield {
            "org": org,
            "user": user,
            "program": program,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_program_creation(app, bounty_setup):
    """Test Program model initialization and retrieval."""
    with app.app_context():
        p = db.session.get(Program, bounty_setup['program'].id)
        assert p.name == "CTF Core Program"
        assert p.program_type == "public"
        assert p.reward_max == 1000

def test_vulnerability_report_lifecycle(app, bounty_setup):
    """Test VulnerabilityReport creation, CVSS mapping, and relationships."""
    with app.app_context():
        prog = bounty_setup['program']
        user = bounty_setup['user']
        org = bounty_setup['org']

        report = VulnerabilityReport(
            program_id=prog.id,
            researcher_id=user.id,
            title="Reflected XSS in query search",
            description="Parameter q displays raw scripts",
            cvss_score=6.5,
            severity="medium",
            status="submitted",
            organization_id=org.id
        )
        db.session.add(report)
        db.session.commit()

        assert report.id is not None
        assert report.status == "submitted"
        assert report.severity == "medium"
        assert len(prog.reports.all()) == 1

        # Test rewards attachment
        reward = BountyReward(report_id=report.id, amount=300, payment_status="paid")
        db.session.add(reward)
        db.session.commit()

        assert report.rewards.count() == 1
        assert report.rewards.first().amount == 300

        # Test disclosure association
        disc = Disclosure(report_id=report.id, disclosure_type="coordinated", public_url="http://advisories.net/1")
        db.session.add(disc)
        db.session.commit()

        assert report.disclosures.count() == 1
        assert report.disclosures.first().disclosure_type == "coordinated"

def test_bounties_api_endpoints(client, bounty_setup):
    """Test bug bounty list and submission REST endpoints."""
    headers = bounty_setup['headers']
    prog = bounty_setup['program']
    user = bounty_setup['user']

    # 1. Access without authorization
    resp = client.get('/api/v1/bounties')
    assert resp.status_code == 401

    # 2. Get list (should be empty initially)
    resp = client.get('/api/v1/bounties', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data)['count'] == 0

    # 3. Submit report
    resp = client.post('/api/v1/bounties', data=json.dumps({
        "program_id": prog.id,
        "researcher_id": user.id,
        "title": "Remote Code Execution via file import",
        "description": "Explaining payload uploads...",
        "cvss_score": 9.8,
        "org_id": prog.organization_id
    }), content_type='application/json', headers=headers)
    assert resp.status_code == 201
    
    data = json.loads(resp.data)['vulnerability_report']
    assert data['severity'] == "critical"
    assert data['cvss_score'] == 9.8

    # 4. Check list again
    resp = client.get('/api/v1/bounties', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data)['count'] == 1
