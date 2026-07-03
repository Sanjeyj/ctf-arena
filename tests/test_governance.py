"""
Unit and Integration tests for Step 2 & 6 Governance Policies and AI.
Contains 11 test cases.
"""
import pytest
import json
import datetime
from app.extensions import db
from app.models.policy import Policy
from app.models.policy_acknowledgement import PolicyAcknowledgement
from app.models.risk_register import RiskRegister
from app.models.user import User
from app.models.organization import Organization
from app.services.analytics_service import AnalyticsService
from app.services.governance_ai_service import GovernanceAIService
from app.research.routes import create_jwt

@pytest.fixture
def governance_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(PolicyAcknowledgement).delete()
        db.session.query(Policy).delete()
        db.session.query(RiskRegister).delete()
        db.session.query(User).delete()
        db.session.commit()

        org = Organization(name="Gov Org", slug="gov-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        user = User(username="analyst_alice", email="alice@gov.net", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        policy = Policy(title="Token Management Mandate", content="Exp policy", status="approved", organization_id=org.id)
        db.session.add(policy)
        db.session.commit()

        ack = PolicyAcknowledgement(policy_id=policy.id, user_id=user.id, acknowledged_at=datetime.datetime.utcnow(), organization_id=org.id)
        db.session.add(ack)
        db.session.commit()

        risk = RiskRegister(scenario="Unauthorized Key Exposure", impact=4, likelihood=3, risk_score=12, organization_id=org.id)
        db.session.add(risk)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "gov_admin"}, secret)

        yield {
            "org": org,
            "user": user,
            "policy": policy,
            "ack": ack,
            "risk": risk,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_policy_creation(app, governance_setup):
    """Test 1: Policy database parameters and status draft workflows."""
    with app.app_context():
        p = db.session.get(Policy, governance_setup['policy'].id)
        assert p.title == "Token Management Mandate"
        assert p.status == "approved"

def test_policy_repr(app, governance_setup):
    """Test 2: Policy model representation string."""
    with app.app_context():
        p = db.session.get(Policy, governance_setup['policy'].id)
        assert "Token Management" in repr(p)

def test_policy_acknowledgement_creation(app, governance_setup):
    """Test 3: PolicyAcknowledgement relation logs storage."""
    with app.app_context():
        ack = db.session.get(PolicyAcknowledgement, governance_setup['ack'].id)
        assert ack.policy_id == governance_setup['policy'].id
        assert ack.user_id == governance_setup['user'].id

def test_policy_acknowledgement_repr(app, governance_setup):
    """Test 4: PolicyAcknowledgement model representation string."""
    with app.app_context():
        ack = db.session.get(PolicyAcknowledgement, governance_setup['ack'].id)
        assert "user_id" in repr(ack)

def test_risk_register_creation(app, governance_setup):
    """Test 5: RiskRegister scenario likelihood and impact assessment scoring."""
    with app.app_context():
        r = db.session.get(RiskRegister, governance_setup['risk'].id)
        assert r.scenario == "Unauthorized Key Exposure"
        assert r.risk_score == 12

def test_risk_register_repr(app, governance_setup):
    """Test 6: RiskRegister model representation string."""
    with app.app_context():
        r = db.session.get(RiskRegister, governance_setup['risk'].id)
        assert "Unauthorized Key Exposure" in repr(r)

def test_governance_ai_gaps_question(app, governance_setup):
    """Test 7: Governance AIService resolves compliance gaps topics."""
    with app.app_context():
        res = GovernanceAIService.answer_governance_question("What compliance gaps remain?", org_id=governance_setup['org'].id)
        assert "gaps" in res['summary'].lower()

def test_governance_ai_controls_question(app, governance_setup):
    """Test 8: Governance AIService resolves failed controls topics."""
    with app.app_context():
        res = GovernanceAIService.answer_governance_question("Which controls failed?", org_id=governance_setup['org'].id)
        assert "controls" in res['summary'].lower()

def test_governance_ai_risks_question(app, governance_setup):
    """Test 9: Governance AIService lists risk registers priorities."""
    with app.app_context():
        res = GovernanceAIService.answer_governance_question("What risks exist?", org_id=governance_setup['org'].id)
        assert "threat" in res['summary'].lower()

def test_governance_ai_fallback_question(app, governance_setup):
    """Test 10: Governance AIService handles fallback question parameters."""
    with app.app_context():
        res = GovernanceAIService.answer_governance_question("Random topic")
        assert "dashboard active" in res['summary']


def test_governance_rest_endpoint_maturity(client, governance_setup):
    """Test 11: GET /api/v1/governance returns maturity indices statistics."""
    headers = governance_setup['headers']
    resp = client.get('/api/v1/governance', headers=headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "maturity_index" in data
    assert data['policies_count'] == 1
