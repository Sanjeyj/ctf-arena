"""
Unit and Integration tests for Step 3 Executive Reporting & AI Copilot.
"""
import pytest
import json
from app.extensions import db
from app.models.executive_report import ExecutiveReport
from app.models.organization import Organization
from app.services.executive_ai_service import ExecutiveAIService
from app.research.routes import create_jwt

@pytest.fixture
def exec_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(ExecutiveReport).delete()
        db.session.commit()

        org = Organization(name="Exec Org", slug="exec-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        report = ExecutiveReport(
            report_type="weekly", open_incidents=1, risk_score=35.0, organization_id=org.id
        )
        db.session.add(report)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "exec_admin"}, secret)

        yield {
            "org": org,
            "report": report,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_executive_report_creation(app, exec_setup):
    """Test generating and saving CISO posture reports."""
    with app.app_context():
        rep = db.session.get(ExecutiveReport, exec_setup['report'].id)
        assert rep.report_type == "weekly"
        assert rep.risk_score == 35.0

def test_executive_ai_answering_posture(app, exec_setup):
    """Test Executive AI Service parses security questions."""
    with app.app_context():
        org = exec_setup['org']
        
        # Ask about organization risk
        res = ExecutiveAIService.answer_question("What is our current risk?", org_id=org.id)
        assert "risk" in res['question']
        assert "risk" in res['summary'].lower()

        # Ask about active incidents
        res = ExecutiveAIService.answer_question("Which incidents are active?", org_id=org.id)
        assert "active" in res['summary'].lower()

def test_executive_api_endpoint(client, exec_setup):
    """Test GET /api/v1/executive REST route."""
    headers = exec_setup['headers']
    org = exec_setup['org']

    resp = client.get(f'/api/v1/executive?org_id={org.id}', headers=headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)['summary']
    assert data['open_incidents'] == 2
    assert "training_status" in data


def test_executive_report_serialization(app, exec_setup):
    """Test ExecutiveReport model serializes dictionary values correctly."""
    with app.app_context():
        rep = db.session.get(ExecutiveReport, exec_setup['report'].id)
        rd = rep.to_dict()
        assert rd['report_type'] == "weekly"
        assert rd['open_incidents'] == 1


def test_executive_ai_empty_question(app):
    """Test Executive AIService answers gracefully for unknown query topics."""
    with app.app_context():
        res = ExecutiveAIService.answer_question("Random topic")
        assert "standing by" in res['summary']


def test_executive_ai_unmatched_question(app):
    """Test Executive AIService response for gaps audits question topics."""
    with app.app_context():
        res = ExecutiveAIService.answer_question("What training gaps exist?")
        assert "gaps" in res['summary']
        assert "LMS" in res['recommendation']


def test_executive_report_by_org_filtering(client, exec_setup):
    """Test executive REST endpoint filtering returns accurate statistics fields."""
    headers = exec_setup['headers']
    # Filter with non-existent org_id
    resp = client.get('/api/v1/executive?org_id=9999', headers=headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)['summary']
    assert data['reports_count'] == 0

