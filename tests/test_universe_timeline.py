"""
Unit and Integration tests for Phase 30 — Universe Timeline.
Contains 13 test cases covering UniverseEvent model validation, events timeline tracking, replays, and summaries.
"""
import pytest
import json
import datetime
from app.extensions import db
from app.models.organization import Organization
from app.models.defense_universe import DefenseUniverse
from app.models.universe_scenario import UniverseScenario
from app.models.universe_simulation import UniverseSimulation
from app.models.universe_event import UniverseEvent
from app.services.universe_service import UniverseService
from app.services.scenario_engine_service import ScenarioEngineService
from app.services.universe_timeline_service import UniverseTimelineService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def time_setup(app):
    """Fixture for timeline tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(UniverseEvent).delete()
        db.session.query(UniverseSimulation).delete()
        db.session.query(UniverseScenario).delete()
        db.session.query(DefenseUniverse).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Timeline Org", slug="time-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        uni = UniverseService.create_universe("Time Uni", org.id)
        scen = ScenarioEngineService.create_scenario(uni.id, "S1", "ransomware_outage", org.id)
        sim = ScenarioEngineService.simulate(scen.id, org.id)

        try:
            UserRepository.create(
                username="time_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Time Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "time_admin"}, secret)

        yield {
            "org": org,
            "uni": uni,
            "scen": scen,
            "sim": sim,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_universe_event_creation(app, time_setup):
    """Test 1: UniverseEvent model fields."""
    with app.app_context():
        event = UniverseEvent(
            simulation_id=time_setup["sim"].id,
            event_type="outage",
            domain="cloud",
            severity="high",
            description="DNS server unreachable.",
            score_delta=-0.1,
            event_time=datetime.datetime.utcnow(),
            organization_id=time_setup["org"].id
        )
        db.session.add(event)
        db.session.commit()
        assert event.id is not None
        assert event.event_type == "outage"
        assert event.score_delta == -0.1


def test_universe_event_repr(app, time_setup):
    """Test 2: UniverseEvent repr format."""
    with app.app_context():
        event = UniverseEvent(event_type="reboot", simulation_id=1, organization_id=time_setup["org"].id)
        assert "reboot" in repr(event)


def test_universe_event_to_dict(app, time_setup):
    """Test 3: UniverseEvent serialization."""
    with app.app_context():
        now = datetime.datetime.utcnow()
        event = UniverseEvent(
            simulation_id=time_setup["sim"].id,
            event_type="incident",
            domain="soc",
            severity="critical",
            description="Active breach.",
            score_delta=-0.2,
            event_time=now,
            organization_id=time_setup["org"].id
        )
        d = event.to_dict()
        assert d["event_type"] == "incident"
        assert d["domain"] == "soc"
        assert d["severity"] == "critical"
        assert d["event_time"] == now.isoformat()


def test_timeline_service_append(app, time_setup):
    """Test 4: Append adds an event with UTC timestamp."""
    with app.app_context():
        evt = UniverseTimelineService.append_event(
            time_setup["sim"].id, "test_event", "Description of test event",
            time_setup["org"].id, "soc", "info", -0.05
        )
        assert evt.id is not None
        assert evt.event_type == "test_event"
        assert evt.score_delta == -0.05


def test_timeline_service_get_timeline(app, time_setup):
    """Test 5: Get timeline lists simulation chronological events."""
    with app.app_context():
        UniverseTimelineService.append_event(time_setup["sim"].id, "e1", "desc1", time_setup["org"].id)
        events = UniverseTimelineService.get_timeline(time_setup["sim"].id, time_setup["org"].id)
        # Event from simulation start + our append = 2 events
        assert len(events) >= 2


def test_timeline_service_replay(app, time_setup):
    """Test 6: Replay runs chronological playback score updates."""
    with app.app_context():
        # Clear database events to make test clean
        db.session.query(UniverseEvent).delete()
        db.session.commit()

        UniverseTimelineService.append_event(time_setup["sim"].id, "e1", "desc1", time_setup["org"].id, score_delta=-0.05)
        UniverseTimelineService.append_event(time_setup["sim"].id, "e2", "desc2", time_setup["org"].id, score_delta=-0.1)

        rep = UniverseTimelineService.replay(time_setup["sim"].id, time_setup["org"].id)
        assert rep["total_steps"] == 2
        # Initial is 1.0 -> 0.95 -> 0.85
        assert rep["replay_timeline"][0]["simulated_score"] == 0.95
        assert rep["replay_timeline"][1]["simulated_score"] == 0.85


def test_timeline_service_summarize_valid(app, time_setup):
    """Test 7: Summarize returns outcome summary metrics."""
    with app.app_context():
        db.session.query(UniverseEvent).delete()
        db.session.commit()

        UniverseTimelineService.append_event(time_setup["sim"].id, "e1", "desc1", time_setup["org"].id, severity="critical", score_delta=-0.15)
        
        summary = UniverseTimelineService.summarize(time_setup["sim"].id, time_setup["org"].id)
        assert summary["total_events"] == 1
        assert summary["net_impact"] == -0.15
        assert summary["critical_events"] == 1


def test_timeline_service_summarize_not_found(app):
    """Test 8: Summarize returns None for invalid simulation ID."""
    with app.app_context():
        assert UniverseTimelineService.summarize(99999, 1) is None


def test_timeline_service_compare_runs(app, time_setup):
    """Test 9: Compare runs returns final score variance."""
    with app.app_context():
        sim1 = time_setup["sim"]
        sim2 = ScenarioEngineService.simulate(time_setup["scen"].id, time_setup["org"].id)

        # Force distinct final scores for verification
        sim1.final_score = 0.85
        sim2.final_score = 0.65
        db.session.commit()

        # Mock event logs for summary
        UniverseTimelineService.append_event(sim1.id, "e1", "d1", time_setup["org"].id, score_delta=-0.15)
        UniverseTimelineService.append_event(sim2.id, "e2", "d2", time_setup["org"].id, score_delta=-0.35)

        comp = UniverseTimelineService.compare_runs(sim1.id, sim2.id, time_setup["org"].id)
        assert comp["variance"] == 0.2


def test_timeline_service_compare_runs_unauthorized(app, time_setup):
    """Test 10: Compare runs enforces tenant scoping boundary check."""
    with app.app_context():
        sim1 = time_setup["sim"]
        res = UniverseTimelineService.compare_runs(sim1.id, sim1.id, 99999)
        assert "error" in res


def test_api_get_timeline(client, time_setup):
    """Test 11: GET /api/v1/universe/simulations/<id>/timeline REST endpoint."""
    resp = client.get(
        f'/api/v1/universe/simulations/{time_setup["sim"].id}/timeline?org_id={time_setup["org"].id}',
        headers=time_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1


def test_api_get_simulation_detail(client, time_setup):
    """Test 12: GET /api/v1/universe/simulations/<id> REST endpoint."""
    resp = client.get(
        f'/api/v1/universe/simulations/{time_setup["sim"].id}?org_id={time_setup["org"].id}',
        headers=time_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["id"] == time_setup["sim"].id


def test_timeline_chronological_ordering(app, time_setup):
    """Test 13: Timeline lists events ordered chronological ascending."""
    with app.app_context():
        db.session.query(UniverseEvent).delete()
        db.session.commit()

        e1 = UniverseTimelineService.append_event(time_setup["sim"].id, "e1", "d1", time_setup["org"].id)
        e2 = UniverseTimelineService.append_event(time_setup["sim"].id, "e2", "d2", time_setup["org"].id)

        # Force e1 time to be earlier
        e1.event_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
        e2.event_time = datetime.datetime.utcnow()
        db.session.commit()

        events = UniverseTimelineService.get_timeline(time_setup["sim"].id, time_setup["org"].id)
        assert events[0].event_type == "e1"
        assert events[1].event_type == "e2"
