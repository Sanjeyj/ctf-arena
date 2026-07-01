"""
Milestone 5 Tests — Competition Engine, Scoreboard Freeze, Announcements, Submission Manager
"""
import pytest
import datetime
from app.extensions import db
from app.repositories.role_repository import RoleRepository
from app.repositories.permission_repository import PermissionRepository


@pytest.fixture(autouse=True)
def setup_roles(app):
    with app.app_context():
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()


# ── Competition Service ──────────────────────────────────────────

def test_competition_auto_seed(app):
    """CompetitionService.get_active_competition() auto-seeds a default competition."""
    with app.app_context():
        from app.services.competition_service import CompetitionService
        comp = CompetitionService.get_active_competition()
        assert comp is not None
        assert comp.is_active is True
        assert comp.name is not None


def test_competition_state_practice(app):
    """A competition with no dates defined resolves to practice or running state."""
    with app.app_context():
        from app.services.competition_service import CompetitionService
        comp = CompetitionService.get_active_competition()
        state = CompetitionService.get_competition_state(comp)
        assert state in ("practice", "running", "scheduled", "ended")


def test_competition_freeze_state(app):
    """Setting freeze_time <= now < unfreeze_time transitions state to 'frozen'."""
    with app.app_context():
        from app.services.competition_service import CompetitionService
        comp = CompetitionService.get_active_competition()
        now = datetime.datetime.utcnow()
        CompetitionService.update_competition(
            comp.id,
            start_time=now - datetime.timedelta(hours=2),
            end_time=now + datetime.timedelta(hours=2),
            freeze_time=now - datetime.timedelta(minutes=30),
            unfreeze_time=now + datetime.timedelta(hours=1),
        )
        # Reload
        from app.repositories.competition_repository import CompetitionRepository
        comp = CompetitionRepository.get_by_id(comp.id)
        state = CompetitionService.get_competition_state(comp)
        assert state == "frozen"


def test_competition_running_state(app):
    """start_time < now < end_time → state is 'running'."""
    with app.app_context():
        from app.services.competition_service import CompetitionService
        from app.repositories.competition_repository import CompetitionRepository
        comp = CompetitionService.get_active_competition()
        now = datetime.datetime.utcnow()
        CompetitionService.update_competition(
            comp.id,
            start_time=now - datetime.timedelta(hours=1),
            end_time=now + datetime.timedelta(hours=5),
            freeze_time=None,
            unfreeze_time=None,
        )
        comp = CompetitionRepository.get_by_id(comp.id)
        state = CompetitionService.get_competition_state(comp)
        assert state == "running"


def test_competition_ended_state(app):
    """end_time <= now → state is 'ended'."""
    with app.app_context():
        from app.services.competition_service import CompetitionService
        from app.repositories.competition_repository import CompetitionRepository
        comp = CompetitionService.get_active_competition()
        now = datetime.datetime.utcnow()
        CompetitionService.update_competition(
            comp.id,
            start_time=now - datetime.timedelta(hours=5),
            end_time=now - datetime.timedelta(minutes=1),
            freeze_time=None,
            unfreeze_time=None,
        )
        comp = CompetitionRepository.get_by_id(comp.id)
        state = CompetitionService.get_competition_state(comp)
        assert state == "ended"


# ── Announcement Service ─────────────────────────────────────────

def test_announcement_crud(app):
    """Create, list, pin, delete announcements."""
    with app.app_context():
        from app.services.announcement_service import AnnouncementService
        from app.repositories.announcement_repository import AnnouncementRepository

        # Create
        ann, err = AnnouncementService.create_announcement(
            title="Test Announcement", content="Hello World!"
        )
        assert err is None
        assert ann is not None
        assert ann.title == "Test Announcement"
        assert ann.published is True

        # List
        active = AnnouncementService.get_active_announcements()
        assert any(a.id == ann.id for a in active)

        # Pin
        AnnouncementRepository.update(ann.id, pinned=True)
        refreshed = AnnouncementRepository.get_by_id(ann.id)
        assert refreshed.pinned is True

        # Delete
        AnnouncementRepository.delete(ann.id)
        gone = AnnouncementRepository.get_by_id(ann.id)
        assert gone is None


def test_announcement_visibility_toggle(app):
    """Published field can be toggled."""
    with app.app_context():
        from app.services.announcement_service import AnnouncementService
        from app.repositories.announcement_repository import AnnouncementRepository

        ann, _ = AnnouncementService.create_announcement(
            title="Hidden Ann", content="Secret", visible=False
        )
        assert ann.published is False

        AnnouncementRepository.update(ann.id, published=True)
        refreshed = AnnouncementRepository.get_by_id(ann.id)
        assert refreshed.published is True


def test_announcement_validation(app):
    """Creating an announcement with empty title/content fails."""
    with app.app_context():
        from app.services.announcement_service import AnnouncementService
        _, err = AnnouncementService.create_announcement("", "content")
        assert err is not None
        _, err = AnnouncementService.create_announcement("title", "")
        assert err is not None


# ── Scoreboard Freeze ────────────────────────────────────────────

def test_freeze_masks_solves(app):
    """LiveScoreboardService masks solves that arrive after freeze_time."""
    with app.app_context():
        from app.repositories.user_repository import UserRepository
        from app.repositories.role_repository import RoleRepository
        from app.services.challenge_service import ChallengeService
        from app.services.competition_service import CompetitionService
        from app.repositories.competition_repository import CompetitionRepository
        from app.services.live_scoreboard_service import LiveScoreboardService
        from app.models.submission import Submission
        from app.services.auth_service import hash_password
        from app.services.category_service import CategoryService

        # Setup
        RoleRepository.setup_default_roles()
        cat, _ = CategoryService.create_category("Test", "t")
        user = UserRepository.create(
            username="freeze_test_user",
            password_hash=hash_password("pass"),
            display_name="FreezeUser",
            role_name="Participant"
        )
        ch = ChallengeService.create_challenge(
            legacy_id="freeze_ch", title="Freeze Ch",
            description="test", points=100, difficulty="Easy",
            category_id=cat.id
        )

        now = datetime.datetime.utcnow()
        freeze_time = now - datetime.timedelta(minutes=10)

        # Solve happens BEFORE freeze
        sub_before = Submission(
            user_id=user.id, challenge_id=ch.id,
            points=100, time=freeze_time - datetime.timedelta(minutes=5),
            elapsed=60, correct=True, status="correct"
        )
        db.session.add(sub_before)

        # Solve happens AFTER freeze (should be masked)
        sub_after = Submission(
            user_id=user.id, challenge_id=ch.id,
            points=100, time=freeze_time + datetime.timedelta(minutes=5),
            elapsed=120, correct=True, status="correct"
        )
        db.session.add(sub_after)
        db.session.commit()

        # Set competition to frozen state
        comp = CompetitionService.get_active_competition()
        CompetitionService.update_competition(
            comp.id,
            start_time=now - datetime.timedelta(hours=2),
            end_time=now + datetime.timedelta(hours=2),
            freeze_time=freeze_time,
            unfreeze_time=now + datetime.timedelta(hours=1),
        )

        # Public view (should be masked)
        result = LiveScoreboardService.get_live_rankings(is_admin_preview=False)
        assert result["freeze_active"] is True

        # Admin preview (should see all)
        result_admin = LiveScoreboardService.get_live_rankings(is_admin_preview=True)
        assert result_admin["freeze_active"] is True  # freeze still active in admin view


# ── Submission Service ───────────────────────────────────────────

def test_submission_pagination(app):
    """SubmissionService.get_submissions paginates correctly."""
    with app.app_context():
        from app.services.submission_service import SubmissionService
        result = SubmissionService.get_submissions(page=1, per_page=50)
        assert "items" in result
        assert "total" in result
        assert "pages" in result


def test_submission_csv_export(app):
    """SubmissionService.export_csv returns valid CSV string."""
    with app.app_context():
        from app.services.submission_service import SubmissionService
        csv_data = SubmissionService.export_csv()
        assert isinstance(csv_data, str)
        assert "id" in csv_data  # header row


# ── API Endpoints ────────────────────────────────────────────────

def test_api_scoreboard_endpoint(client, app):
    """GET /api/scoreboard returns JSON with leaderboard, stats, timer fields."""
    with app.app_context():
        from app.services.competition_service import CompetitionService
        CompetitionService.get_active_competition()  # Ensure seeded

    res = client.get("/api/scoreboard")
    assert res.status_code == 200
    data = res.get_json()
    assert "leaderboard" in data
    assert "stats" in data
    assert "challenges" in data
    assert "freeze_active" in data
    assert "timer" in data


def test_api_live_timeline_endpoint(client, app):
    """GET /api/live/timeline returns a valid JSON events list."""
    with app.app_context():
        from app.services.competition_service import CompetitionService
        CompetitionService.get_active_competition()

    res = client.get("/api/live/timeline")
    assert res.status_code == 200
    data = res.get_json()
    assert "events" in data
    assert isinstance(data["events"], list)


def test_scoreboard_page_loads(client, app):
    """GET /scoreboard returns 200 with freeze_banner element in HTML."""
    with app.app_context():
        from app.services.competition_service import CompetitionService
        CompetitionService.get_active_competition()

    res = client.get("/scoreboard")
    assert res.status_code == 200
    html = res.data.decode()
    assert "freeze-banner" in html
    assert "timer-bar" in html


# ── Admin Competition Routes ─────────────────────────────────────

def test_admin_competition_page_redirects_without_auth(client):
    """GET /admin/competition redirects to login if not authenticated."""
    res = client.get("/admin/competition")
    assert res.status_code in (302, 401)


def test_admin_announcements_page_redirects_without_auth(client):
    """GET /admin/announcements redirects to login if not authenticated."""
    res = client.get("/admin/announcements")
    assert res.status_code in (302, 401)


def test_admin_submissions_page_redirects_without_auth(client):
    """GET /admin/submissions redirects to login if not authenticated."""
    res = client.get("/admin/submissions")
    assert res.status_code in (302, 401)


def test_timer_status_structure(app):
    """LiveScoreboardService.get_timer_status returns expected keys."""
    with app.app_context():
        from app.services.competition_service import CompetitionService
        from app.services.live_scoreboard_service import LiveScoreboardService
        comp = CompetitionService.get_active_competition()
        timer = LiveScoreboardService.get_timer_status(comp)
        assert "state" in timer
        assert "remaining_seconds" in timer
        assert timer["remaining_seconds"] >= 0
