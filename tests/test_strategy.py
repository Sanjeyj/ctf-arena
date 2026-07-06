"""
Unit and Integration tests for Phase 29 Global Cyber Command Center — Strategy.
Contains 15 test cases covering StrategicObjective and ThreatCampaignGlobal models, StrategicService, and API endpoints.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.strategic_objective import StrategicObjective
from app.models.threat_campaign_global import ThreatCampaignGlobal
from app.services.strategic_service import StrategicService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def strat_setup(app):
    """Fixture for strategic operations tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(StrategicObjective).delete()
        db.session.query(ThreatCampaignGlobal).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Strat Org", slug="strat-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="strat_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Strat Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "strat_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_strategic_objective_creation(app, strat_setup):
    """Test 1: StrategicObjective model fields."""
    with app.app_context():
        obj = StrategicObjective(
            objective="Defeat all APTs",
            priority=1,
            progress=0.45,
            status="in_progress",
            organization_id=strat_setup["org"].id
        )
        db.session.add(obj)
        db.session.commit()
        assert obj.id is not None
        assert obj.objective == "Defeat all APTs"
        assert obj.priority == 1
        assert obj.progress == 0.45
        assert obj.status == "in_progress"


def test_strategic_objective_repr(app, strat_setup):
    """Test 2: StrategicObjective repr handles long objectives nicely."""
    with app.app_context():
        obj = StrategicObjective(
            objective="Establish a highly secure multi-tenant operational pipeline for defense",
            priority=2,
            organization_id=strat_setup["org"].id
        )
        assert "Establish" in repr(obj)
        assert "priority=2" in repr(obj)


def test_strategic_objective_to_dict(app, strat_setup):
    """Test 3: StrategicObjective serialization."""
    with app.app_context():
        obj = StrategicObjective(
            objective="Achieve full compliance",
            priority=3,
            progress=1.0,
            status="achieved",
            organization_id=strat_setup["org"].id
        )
        d = obj.to_dict()
        assert d["objective"] == "Achieve full compliance"
        assert d["priority"] == 3
        assert d["progress"] == 1.0
        assert d["status"] == "achieved"


def test_threat_campaign_global_creation(app, strat_setup):
    """Test 4: ThreatCampaignGlobal model fields."""
    with app.app_context():
        tc = ThreatCampaignGlobal(
            campaign_name="Operation Red Storm",
            region="EMEA",
            impact=0.8,
            confidence=0.75,
            organization_id=strat_setup["org"].id
        )
        db.session.add(tc)
        db.session.commit()
        assert tc.id is not None
        assert tc.campaign_name == "Operation Red Storm"
        assert tc.region == "EMEA"
        assert tc.impact == 0.8
        assert tc.confidence == 0.75


def test_threat_campaign_global_repr(app, strat_setup):
    """Test 5: ThreatCampaignGlobal repr output."""
    with app.app_context():
        tc = ThreatCampaignGlobal(campaign_name="Op Titan", region="APAC", organization_id=strat_setup["org"].id)
        assert "Op Titan" in repr(tc)
        assert "APAC" in repr(tc)


def test_threat_campaign_global_to_dict(app, strat_setup):
    """Test 6: ThreatCampaignGlobal serialization."""
    with app.app_context():
        tc = ThreatCampaignGlobal(
            campaign_name="SolarFlare",
            region="Americas",
            impact=0.6,
            confidence=0.7,
            organization_id=strat_setup["org"].id
        )
        d = tc.to_dict()
        assert d["campaign_name"] == "SolarFlare"
        assert d["region"] == "Americas"
        assert d["impact"] == 0.6
        assert d["confidence"] == 0.7


def test_strategic_service_prioritize_order(app, strat_setup):
    """Test 7: Prioritize returns objectives ordered ascending by priority."""
    with app.app_context():
        o1 = StrategicObjective(objective="Low P", priority=5, organization_id=strat_setup["org"].id)
        o2 = StrategicObjective(objective="High P", priority=1, organization_id=strat_setup["org"].id)
        o3 = StrategicObjective(objective="Mid P", priority=3, organization_id=strat_setup["org"].id)
        db.session.add_all([o1, o2, o3])
        db.session.commit()

        ordered = StrategicService.prioritize(strat_setup["org"].id)
        assert ordered[0].objective == "High P"
        assert ordered[1].objective == "Mid P"
        assert ordered[2].objective == "Low P"


def test_strategic_service_prioritize_empty(app, strat_setup):
    """Test 8: Prioritize handles empty org gracefully."""
    with app.app_context():
        assert StrategicService.prioritize(strat_setup["org"].id) == []


def test_strategic_service_evaluate_on_track(app, strat_setup):
    """Test 9: Evaluate returns health='on_track' if progress >= 0.5."""
    with app.app_context():
        obj = StrategicObjective(objective="Obj1", progress=0.6, organization_id=strat_setup["org"].id)
        db.session.add(obj)
        db.session.commit()

        res = StrategicService.evaluate(obj.id)
        assert res["health"] == "on_track"


def test_strategic_service_evaluate_at_risk(app, strat_setup):
    """Test 10: Evaluate returns health='at_risk' if progress < 0.5."""
    with app.app_context():
        obj = StrategicObjective(objective="Obj2", progress=0.3, organization_id=strat_setup["org"].id)
        db.session.add(obj)
        db.session.commit()

        res = StrategicService.evaluate(obj.id)
        assert res["health"] == "at_risk"


def test_strategic_service_evaluate_not_found(app):
    """Test 11: Evaluate returns error dictionary for invalid objective ID."""
    with app.app_context():
        res = StrategicService.evaluate(99999)
        assert "error" in res


def test_strategic_service_report_empty(app, strat_setup):
    """Test 12: Report returns empty stats for new org."""
    with app.app_context():
        res = StrategicService.report(strat_setup["org"].id)
        assert res["total"] == 0
        assert res["avg_progress"] == 0.0


def test_strategic_service_report_calculated(app, strat_setup):
    """Test 13: Report compiles exact status counts and average progress."""
    with app.app_context():
        o1 = StrategicObjective(objective="O1", status="achieved", progress=1.0, organization_id=strat_setup["org"].id)
        o2 = StrategicObjective(objective="O2", status="in_progress", progress=0.5, organization_id=strat_setup["org"].id)
        o3 = StrategicObjective(objective="O3", status="open", progress=0.0, organization_id=strat_setup["org"].id)
        db.session.add_all([o1, o2, o3])
        db.session.commit()

        res = StrategicService.report(strat_setup["org"].id)
        assert res["total"] == 3
        assert res["achieved"] == 1
        assert res["in_progress"] == 1
        assert res["open"] == 1
        assert res["avg_progress"] == 0.5


def test_api_get_strategy(client, strat_setup):
    """Test 14: GET /api/v1/strategy REST endpoint."""
    with client.application.app_context():
        obj = StrategicObjective(objective="API Goal", organization_id=strat_setup["org"].id)
        db.session.add(obj)
        db.session.commit()

    resp = client.get(
        f'/api/v1/strategy?org_id={strat_setup["org"].id}',
        headers=strat_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["objective"] == "API Goal"


def test_api_strategy_missing_org(client, strat_setup):
    """Test 15: GET /api/v1/strategy returns 400 without org_id."""
    resp = client.get('/api/v1/strategy', headers=strat_setup["headers"])
    assert resp.status_code == 400
