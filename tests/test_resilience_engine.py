"""
Unit and Integration tests for Phase 25 Cyber Resilience Platform — Resilience Engine.
Contains 10 test cases covering model creation, service calculations, and API endpoints.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.business_process import BusinessProcess
from app.models.business_impact_analysis import BusinessImpactAnalysis
from app.models.resilience_exercise import ResilienceExercise
from app.models.third_party_vendor import ThirdPartyVendor
from app.services.resilience_engine_service import ResilienceEngineService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def engine_setup(app):
    """Fixture for resilience engine tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(BusinessImpactAnalysis).delete()
        db.session.query(BusinessProcess).delete()
        db.session.query(ResilienceExercise).delete()
        db.session.query(ThirdPartyVendor).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Engine Org", slug="engine-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="engine_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Engine Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "engine_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_business_process_creation(app, engine_setup):
    """Test 1: BusinessProcess model fields and defaults."""
    with app.app_context():
        bp = BusinessProcess(
            name="Order Management",
            owner="Ops Team",
            criticality="high",
            rto=4.0,
            rpo=2.0,
            status="active",
            organization_id=engine_setup['org'].id
        )
        db.session.add(bp)
        db.session.commit()
        assert bp.name == "Order Management"
        assert bp.criticality == "high"
        assert bp.rto == 4.0
        assert "Order Management" in repr(bp)


def test_business_process_to_dict(app, engine_setup):
    """Test 2: BusinessProcess dict serialization."""
    with app.app_context():
        bp = BusinessProcess(
            name="Customer Portal",
            owner="Engineering",
            criticality="critical",
            rto=1.0,
            rpo=0.5,
            organization_id=engine_setup['org'].id
        )
        db.session.add(bp)
        db.session.commit()
        d = bp.to_dict()
        assert d['name'] == "Customer Portal"
        assert d['criticality'] == "critical"
        assert d['rto'] == 1.0
        assert d['organization_id'] == engine_setup['org'].id


def test_bia_creation(app, engine_setup):
    """Test 3: BusinessImpactAnalysis model fields and relationship."""
    with app.app_context():
        bp = BusinessProcess(name="HR System", criticality="medium", organization_id=engine_setup['org'].id)
        db.session.add(bp)
        db.session.commit()

        bia = BusinessImpactAnalysis(
            process_id=bp.id,
            financial_impact=3,
            operational_impact=4,
            reputation_impact=2,
            recovery_priority="high",
            organization_id=engine_setup['org'].id
        )
        db.session.add(bia)
        db.session.commit()
        assert bia.financial_impact == 3
        assert bia.process.name == "HR System"
        assert bia.recovery_priority == "high"


def test_resilience_exercise_creation(app, engine_setup):
    """Test 4: ResilienceExercise model fields."""
    with app.app_context():
        ex = ResilienceExercise(
            exercise_type="tabletop",
            results="All teams responded within SLA",
            lessons_learned="Need better communication channels",
            score=78.5,
            organization_id=engine_setup['org'].id
        )
        db.session.add(ex)
        db.session.commit()
        assert ex.exercise_type == "tabletop"
        assert ex.score == 78.5
        assert "tabletop" in repr(ex)


def test_resilience_exercise_to_dict(app, engine_setup):
    """Test 5: ResilienceExercise serialization."""
    with app.app_context():
        ex = ResilienceExercise(
            exercise_type="simulation",
            score=91.0,
            organization_id=engine_setup['org'].id
        )
        db.session.add(ex)
        db.session.commit()
        d = ex.to_dict()
        assert d['exercise_type'] == "simulation"
        assert d['score'] == 91.0


def test_resilience_engine_calculate_score_empty(app, engine_setup):
    """Test 6: ResilienceEngineService defaults with no data."""
    with app.app_context():
        result = ResilienceEngineService.calculate_resilience_score(engine_setup['org'].id)
        assert 'resilience_score' in result
        assert result['resilience_score'] > 0.0


def test_resilience_engine_with_data(app, engine_setup):
    """Test 7: ResilienceEngineService computes correctly with exercises and vendors."""
    with app.app_context():
        org_id = engine_setup['org'].id
        
        ex = ResilienceExercise(exercise_type="drill", score=90.0, organization_id=org_id)
        bp = BusinessProcess(name="CRM", criticality="critical", rto=3.0, status="active", organization_id=org_id)
        v = ThirdPartyVendor(vendor_name="CloudProvider", risk_score=20.0, organization_id=org_id)
        db.session.add_all([ex, bp, v])
        db.session.commit()

        result = ResilienceEngineService.calculate_resilience_score(org_id)
        assert result['resilience_score'] > 0.0
        assert 'components' in result


def test_resilience_engine_forecast(app, engine_setup):
    """Test 8: ResilienceEngineService forecast failure method."""
    with app.app_context():
        org_id = engine_setup['org'].id
        bp = BusinessProcess(name="Supply Chain", criticality="critical", organization_id=org_id)
        db.session.add(bp)
        db.session.commit()

        bia = BusinessImpactAnalysis(
            process_id=bp.id,
            financial_impact=5,
            recovery_priority="critical",
            organization_id=org_id
        )
        db.session.add(bia)
        db.session.commit()

        result = ResilienceEngineService.forecast_failure(org_id)
        assert 'failure_probability_pct' in result
        assert result['estimated_downtime_loss_usd'] > 0.0


def test_resilience_engine_recommend_controls(app, engine_setup):
    """Test 9: ResilienceEngineService recommend_controls output."""
    with app.app_context():
        result = ResilienceEngineService.recommend_controls(engine_setup['org'].id)
        assert 'recommended_actions' in result
        assert isinstance(result['recommended_actions'], list)


def test_resilience_api_get_processes(client, engine_setup):
    """Test 10: GET /api/v1/resilience/processes returns valid list."""
    resp = client.get(
        f'/api/v1/resilience/processes?org_id={engine_setup["org"].id}',
        headers=engine_setup['headers']
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data, list)
