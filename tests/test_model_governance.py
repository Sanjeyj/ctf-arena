"""
Unit and Integration tests for Phase 31 — Model Governance.
Contains 10 test cases covering ModelGovernanceRecord model, create registry, approve/restrict/retire states, hooks triggering, and REST APIs.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.model_governance_record import ModelGovernanceRecord
from app.services.model_governance_service import ModelGovernanceService
from app.services.hook_service import HookService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def gov_setup(app):
    """Fixture for model governance tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(ModelGovernanceRecord).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Gov Org", slug="gov-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="gov_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Gov Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "gov_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_model_governance_record_creation(app, gov_setup):
    """Test 1: ModelGovernanceRecord model fields."""
    with app.app_context():
        rec = ModelGovernanceRecord(
            model_name="GPT-4o-mini",
            provider="openai",
            purpose="Wargaming Scenario Generation",
            risk_level="high",
            approval_status="approved",
            evaluation_score=0.98,
            organization_id=gov_setup["org"].id
        )
        db.session.add(rec)
        db.session.commit()
        assert rec.id is not None
        assert rec.model_name == "GPT-4o-mini"
        assert rec.approval_status == "approved"


def test_model_governance_record_repr(app, gov_setup):
    """Test 2: ModelGovernanceRecord repr format."""
    with app.app_context():
        rec = ModelGovernanceRecord(model_name="Claude-3", provider="anthropic", approval_status="restricted", organization_id=gov_setup["org"].id)
        assert "Claude-3" in repr(rec)
        assert "restricted" in repr(rec)


def test_model_governance_record_to_dict(app, gov_setup):
    """Test 3: ModelGovernanceRecord serialization."""
    with app.app_context():
        rec = ModelGovernanceRecord(
            model_name="Gemini-Flash",
            provider="gemini",
            risk_level="low",
            approval_status="draft",
            evaluation_score=0.90,
            metadata_json='{"context_window": 128000}',
            organization_id=gov_setup["org"].id
        )
        d = rec.to_dict()
        assert d["model_name"] == "Gemini-Flash"
        assert d["provider"] == "gemini"
        assert d["metadata"] == {"context_window": 128000}


def test_governance_service_register(app, gov_setup):
    """Test 4: Service registers model record."""
    with app.app_context():
        rec = ModelGovernanceService.register_model("Stub-Llama", "ollama", gov_setup["org"].id, purpose="CTF hint generator", risk_level="medium")
        assert rec.id is not None
        assert rec.model_name == "Stub-Llama"
        assert rec.approval_status == "draft"


def test_governance_service_evaluate(app, gov_setup):
    """Test 5: Service evaluates model record and updates score."""
    with app.app_context():
        rec = ModelGovernanceService.register_model("Eval Model", "openai", gov_setup["org"].id)
        evaluated = ModelGovernanceService.evaluate_model(rec.id, 0.88, gov_setup["org"].id)
        assert evaluated.evaluation_score == 0.88


def test_governance_service_approve(app, gov_setup):
    """Test 6: Approve transitions status to approved."""
    with app.app_context():
        rec = ModelGovernanceService.register_model("Approve Model", "openai", gov_setup["org"].id)
        approved = ModelGovernanceService.approve(rec.id, gov_setup["org"].id)
        assert approved.approval_status == "approved"


def test_governance_service_restrict(app, gov_setup):
    """Test 7: Restrict transitions status to restricted."""
    with app.app_context():
        rec = ModelGovernanceService.register_model("Restrict Model", "openai", gov_setup["org"].id)
        restricted = ModelGovernanceService.restrict(rec.id, gov_setup["org"].id)
        assert restricted.approval_status == "restricted"


def test_governance_service_retire(app, gov_setup):
    """Test 8: Retire transitions status to retired."""
    with app.app_context():
        rec = ModelGovernanceService.register_model("Retire Model", "openai", gov_setup["org"].id)
        retired = ModelGovernanceService.retire(rec.id, gov_setup["org"].id)
        assert retired.approval_status == "retired"


def test_governance_service_hooks(app, gov_setup):
    """Test 9: Hooks fire before and after model checks."""
    before_fired = False
    after_fired = False

    def on_before(**kwargs):
        nonlocal before_fired
        before_fired = True

    def on_after(**kwargs):
        nonlocal after_fired
        after_fired = True

    HookService.register_hook("before_model_governance_check", on_before)
    HookService.register_hook("after_model_governance_check", on_after)

    with app.app_context():
        rec = ModelGovernanceService.register_model("Hook Model", "openai", gov_setup["org"].id)
        ModelGovernanceService.evaluate_model(rec.id, 0.95, gov_setup["org"].id)

    assert before_fired is True
    assert after_fired is True


def test_api_register_model(client, gov_setup):
    """Test 10: POST /api/v1/control-plane/models REST endpoint."""
    resp = client.post(
        f'/api/v1/control-plane/models?org_id={gov_setup["org"].id}',
        json={
            'model_name': 'API model',
            'provider': 'openai',
            'purpose': 'Wargaming evaluation',
            'risk_level': 'high'
        },
        headers=gov_setup["headers"]
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["model_name"] == "API model"
    assert data["approval_status"] == "draft"
