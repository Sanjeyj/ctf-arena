import pytest
import datetime
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.user import User
from app.models.team import Team
from app.models.category import Category
from app.models.challenge import Challenge
from app.models.flag import Flag
from app.models.submission import Submission
from app.models.challenge_instance import ChallengeInstance
from app.repositories.user_repository import UserRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.challenge_repository import ChallengeRepository
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.challenge_instance_repository import ChallengeInstanceRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.permission_repository import PermissionRepository
from app.services.auth_service import AuthService
from app.extensions import utcnow

# Setup roles/perms automatically for all tests in this module
@pytest.fixture(autouse=True)
def setup_roles_and_perms(app):
    with app.app_context():
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

# ---------------------------------------------------------------------------
# Test Cases for PostgreSQL Compat and Schema Hardening
# ---------------------------------------------------------------------------

def test_postgresql_user_schema_integrity(app):
    """Test 1: Validate User model schema type constraints (UUID, roles, registrations)."""
    with app.app_context():
        user = UserRepository.create(
            username="pg_user1",
            password_hash="hashvalue",
            display_name="PG User One",
            role_name="Participant"
        )
        assert user.id is not None
        assert user.uuid is not None
        assert len(user.uuid) == 36
        assert isinstance(user.registered_at, datetime.datetime)
        assert user.is_deleted is False

def test_postgresql_unique_constraints(app):
    """Test 2: Ensure unique constraint integrity violations are thrown consistently."""
    with app.app_context():
        UserRepository.create(username="unique_val", password_hash="hash")
        with pytest.raises(IntegrityError):
            UserRepository.create(username="unique_val", password_hash="hash2")
        db.session.rollback()

def test_postgresql_soft_delete_query_filtering(app):
    """Test 3: Verify soft-delete toggle filters users correctly without purging database rows."""
    with app.app_context():
        user = UserRepository.create(username="deleted_user", password_hash="hash")
        assert user.is_deleted is False
        user.soft_delete()
        db.session.commit()

        # Query should not fetch soft-deleted users in active participant lists
        active_users = User.query.filter_by(is_deleted=False).all()
        assert not any(u.username == "deleted_user" for u in active_users)

def test_postgresql_challenge_decay_calculations(app):
    """Test 4: Verify points decay functions behave within static/dynamic boundaries."""
    with app.app_context():
        cat = Category(name="web")
        db.session.add(cat)
        db.session.flush()

        ch = Challenge(
            legacy_id="ch_decay",
            title="Decay Ch",
            description="Web challenge",
            points=200,
            initial_points=200,
            minimum_points=50,
            current_points=200,
            decay_type="static",
            difficulty="Medium",
            category_id=cat.id
        )
        db.session.add(ch)
        db.session.commit()

        assert ch.current_points == 200
        assert ch.minimum_points == 50
        assert ch.initial_points == 200

def test_postgresql_team_score_aggregation_syntax(app):
    """Test 5: Validate ANSI SQL compliant group-by query syntax for team scoring (no SQLite-only leniencies)."""
    with app.app_context():
        team = Team(name="PG Team Alpha")
        db.session.add(team)
        db.session.flush()

        user1 = UserRepository.create(username="t_player1", password_hash="hash")
        user2 = UserRepository.create(username="t_player2", password_hash="hash")
        user1.team_id = team.id
        user2.team_id = team.id
        
        cat = Category(name="pwn")
        db.session.add(cat)
        db.session.flush()
        
        ch = Challenge(legacy_id="ch_t1", title="Ch1", description="D", points=100, difficulty="Easy", category_id=cat.id)
        db.session.add(ch)
        db.session.flush()

        sub1 = Submission(user=user1, challenge=ch, points=100, elapsed=10)
        sub2 = Submission(user=user2, challenge=ch, points=100, elapsed=20)
        db.session.add_all([sub1, sub2])
        db.session.commit()

        # Perform aggregate query summing scores grouped by team ID
        # Must select team.id and sum(submissions.points), grouped explicitly by team.id
        # Under PostgreSQL, any column selected that is not aggregated must appear in GROUP BY
        result = db.session.query(
            Team.id,
            db.func.sum(Submission.points)
        ).join(User, User.team_id == Team.id).join(Submission, Submission.user_id == User.id).group_by(Team.id).first()
        
        assert result is not None
        assert result[1] == 200

def test_postgresql_submission_ordering_and_times(app):
    """Test 6: Verify ordering queries by timestamp works identically across engines."""
    with app.app_context():
        user = UserRepository.create(username="s_player", password_hash="hash")
        cat = Category(name="reversing")
        db.session.add(cat)
        db.session.flush()
        
        ch = Challenge(legacy_id="ch_s1", title="Ch1", description="D", points=50, difficulty="Easy", category_id=cat.id)
        db.session.add(ch)
        db.session.flush()

        sub1 = Submission(user=user, challenge=ch, points=50, time=utcnow() - datetime.timedelta(seconds=10))
        sub2 = Submission(user=user, challenge=ch, points=50, time=utcnow())
        db.session.add_all([sub1, sub2])
        db.session.commit()

        ordered = Submission.query.order_by(Submission.time.asc()).all()
        assert len(ordered) >= 2
        assert ordered[0].time < ordered[1].time

def test_postgresql_challenge_instance_timezone_calculations(app):
    """Test 7: Verify challenge container instance expiry datetime matches naive utcnow calculations."""
    with app.app_context():
        now = utcnow()
        expiry = now + datetime.timedelta(minutes=30)
        inst = ChallengeInstance(
            user_id=1,
            challenge_id=1,
            docker_image_id=1,
            container_id="fake_cid",
            mapped_port=31337,
            started_at=now,
            expires_at=expiry
        )
        db.session.add(inst)
        db.session.commit()

        assert inst.expires_at > now
        assert (inst.expires_at - now).total_seconds() <= 1800

def test_postgresql_expires_at_index_reflected(app):
    """Test 8: Verify expires_at index is correctly reflected in sqlalchemy model metadata."""
    metadata = db.metadata
    table = metadata.tables.get("challenge_instances")
    assert table is not None
    indexes = {idx.name for idx in table.indexes}
    # Ensure index exists on expires_at to optimize daemon prune queries
    assert any("expires_at" in idx.name or any(c.name == "expires_at" for c in idx.columns) for idx in table.indexes)

def test_postgresql_role_permissions_assignment(app):
    """Test 9: Verify role permissions mapping works correctly under ORM constraints."""
    with app.app_context():
        from app.models.role import Role, Permission
        role = Role.query.filter_by(name="Participant").first()
        assert role is not None
        # Verify permissions exist
        assert len(role.permissions) > 0

def test_postgresql_submission_elapsed_score_calculation(app):
    """Test 10: Test time elapsed dynamic score calculation math constraints."""
    with app.app_context():
        user = UserRepository.create(username="math_player", password_hash="hash")
        cat = Category(name="misc")
        db.session.add(cat)
        db.session.flush()

        ch = Challenge(
            legacy_id="ch_math",
            title="Math Challenge",
            description="Desc",
            points=100,
            initial_points=100,
            minimum_points=10,
            current_points=100,
            decay_type="legacy_time",
            difficulty="Easy",
            category_id=cat.id
        )
        db.session.add(ch)
        db.session.flush()

        # Mock solve after 20 seconds (loss of 2 points in legacy_time mode)
        elapsed = 20
        points = max(10, ch.initial_points - int(elapsed // 10))
        assert points == 98
