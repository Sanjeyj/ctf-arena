"""
Unit and Integration tests for Phase 26 Autonomous Cyber Enterprise — AI Decision Engine.
Contains 10 test cases covering decisions model, approvals, and copilot endpoints.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.autonomous_decision import AutonomousDecision
from app.models.enterprise_goal import EnterpriseGoal
from app.models.digital_worker import DigitalWorker
from app.services.decision_engine_service import DecisionEngineService
from app.services.executive_ai_orchestrator import ExecutiveAIOrchestrator
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def decision_setup(app):
    """Fixture for decision engine tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(AutonomousDecision).delete()
        db.session.query(EnterpriseGoal).delete()
        db.session.query(DigitalWorker).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Decision Org", slug="decision-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="decision_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Decision Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "decision_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_autonomous_decision_creation(app, decision_setup):
    """Test 1: AutonomousDecision model fields."""
    with app.app_context():
        decision = AutonomousDecision(
            decision_type="Quarantine Host",
            confidence=0.91,
            recommendation="Isolate server 10.0.0.5 immediately.",
            approval_status="pending_approval",
            organization_id=decision_setup['org'].id
        )
        db.session.add(decision)
        db.session.commit()
        assert decision.decision_type == "Quarantine Host"
        assert decision.confidence == 0.91
        assert "Quarantine Host" in repr(decision)


def test_autonomous_decision_to_dict(app, decision_setup):
    """Test 2: AutonomousDecision dict serialization."""
    with app.app_context():
        decision = AutonomousDecision(
            decision_type="Revoke Credentials",
            confidence=0.85,
            recommendation="Disable account compromised_user.",
            organization_id=decision_setup['org'].id
        )
        db.session.add(decision)
        db.session.commit()
        d = decision.to_dict()
        assert d['decision_type'] == "Revoke Credentials"
        assert d['confidence'] == 0.85


def test_decision_service_evaluate(app, decision_setup):
    """Test 3: DecisionEngineService.evaluate registers a decision."""
    with app.app_context():
        decision = DecisionEngineService.evaluate(
            decision_type="Patch Vulnerability",
            recommendation="Apply hotfix patch CVE-2026-1024.",
            confidence=0.95,
            organization_id=decision_setup['org'].id
        )
        assert decision.id is not None
        assert decision.approval_status == "pending_approval"


def test_decision_service_recommend_high_confidence(app, decision_setup):
    """Test 4: DecisionEngineService.recommend recommends approval for high confidence."""
    with app.app_context():
        decision = DecisionEngineService.evaluate(
            decision_type="Block Malicious IP",
            recommendation="Block 198.51.100.45",
            confidence=0.90,
            organization_id=decision_setup['org'].id
        )
        rec = DecisionEngineService.recommend(decision.id)
        assert rec['engine_verdict'] == "approve"
        assert rec['requires_auth_factor'] is False


def test_decision_service_recommend_low_confidence(app, decision_setup):
    """Test 5: DecisionEngineService.recommend flags manual review for low confidence."""
    with app.app_context():
        decision = DecisionEngineService.evaluate(
            decision_type="Demote User",
            recommendation="Demote admin account to auditor.",
            confidence=0.65,
            organization_id=decision_setup['org'].id
        )
        rec = DecisionEngineService.recommend(decision.id)
        assert rec['engine_verdict'] == "request_manual_review"
        assert rec['requires_auth_factor'] is True


def test_decision_service_approve(app, decision_setup):
    """Test 6: DecisionEngineService.approve sets approval_status."""
    with app.app_context():
        decision = DecisionEngineService.evaluate(
            decision_type="Scale Deployments",
            recommendation="Add 3 nodes to cluster.",
            confidence=0.85,
            organization_id=decision_setup['org'].id
        )
        approved = DecisionEngineService.approve(decision.id)
        assert approved.approval_status == "approved"


def test_executive_summarize_empty(app, decision_setup):
    """Test 7: ExecutiveAIOrchestrator.summarize_enterprise defaults with no goals."""
    with app.app_context():
        summary = ExecutiveAIOrchestrator.summarize_enterprise(decision_setup['org'].id)
        assert summary['goals_count'] == 0
        assert summary['digital_workers_count'] == 0
        assert summary['average_goal_progress_pct'] == 85.0


def test_executive_summarize_with_data(app, decision_setup):
    """Test 8: ExecutiveAIOrchestrator.summarize_enterprise calculates progress averages."""
    with app.app_context():
        org_id = decision_setup['org'].id
        goal = EnterpriseGoal(objective="Improve compliance", progress=60.0, organization_id=org_id)
        worker = DigitalWorker(worker_name="BotA", specialization="Sigma Parser", performance_score=95.0, organization_id=org_id)
        db.session.add_all([goal, worker])
        db.session.commit()

        summary = ExecutiveAIOrchestrator.summarize_enterprise(org_id)
        assert summary['goals_count'] == 1
        assert summary['average_goal_progress_pct'] == 60.0
        assert summary['average_performance_score_pct'] == 95.0


def test_executive_recommend_priorities(app, decision_setup):
    """Test 9: ExecutiveAIOrchestrator.recommend_priorities filters goals needing progress."""
    with app.app_context():
        org_id = decision_setup['org'].id
        goal = EnterpriseGoal(objective="Patch Servers", target_score=90.0, progress=75.0, organization_id=org_id)
        db.session.add(goal)
        db.session.commit()

        recs = ExecutiveAIOrchestrator.recommend_priorities(org_id)
        assert len(recs) == 1
        assert "Patch Servers" in recs[0]


def test_api_get_decisions(client, decision_setup):
    """Test 10: GET /api/v1/decisions lists all decisions."""
    resp = client.get(
        f'/api/v1/decisions?org_id={decision_setup["org"].id}',
        headers=decision_setup['headers']
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data, list)
