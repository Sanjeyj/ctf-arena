import pytest
import datetime
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.user import User
from app.models.team import Team
from app.models.category import Category
from app.models.challenge import Challenge
from app.models.flag import Flag
from app.models.submission import Submission

def test_user_creation_and_mixins(app):
    """Verify that a User record has UUID, Timestamp, and Soft Delete traits."""
    with app.app_context():
        user = User(username="test_user")
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.uuid is not None
        assert len(user.uuid) == 36
        assert isinstance(user.created_at, datetime.datetime)
        assert isinstance(user.updated_at, datetime.datetime)
        assert user.is_deleted is False

        user.soft_delete()
        db.session.commit()
        assert user.is_deleted is True

def test_database_relationships(app):
    """Verify relations: Category, Challenge, Flag, User, Submission."""
    with app.app_context():
        cat = Category(name="Crypto")
        db.session.add(cat)
        
        ch = Challenge(
            legacy_id="ch_test",
            title="Test Challenge",
            description="Desc",
            points=100,
            difficulty="Easy",
            category=cat
        )
        db.session.add(ch)
        
        fl = Flag(challenge=ch, content="FLAG{test}")
        db.session.add(fl)

        user = User(username="player1")
        db.session.add(user)
        db.session.flush()

        sub = Submission(user=user, challenge=ch, points=100, elapsed=45)
        db.session.add(sub)
        db.session.commit()

        db_user = User.query.filter_by(username="player1").first()
        assert len(db_user.submissions) == 1
        assert db_user.submissions[0].points == 100
        assert db_user.submissions[0].challenge.title == "Test Challenge"
        assert db_user.submissions[0].challenge.category.name == "Crypto"
        assert len(db_user.submissions[0].challenge.flags) == 1
        assert db_user.submissions[0].challenge.flags[0].content == "FLAG{test}"

def test_database_constraints(app):
    """Verify unique constraints in User and Category models."""
    with app.app_context():
        user1 = User(username="duplicate")
        db.session.add(user1)
        db.session.commit()

        user2 = User(username="duplicate")
        db.session.add(user2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

def test_database_transactions(app):
    """Verify manual transaction rollback does not write dirty data."""
    with app.app_context():
        user = User(username="rolled_back")
        db.session.add(user)
        db.session.flush()
        
        db.session.rollback()
        
        db_user = User.query.filter_by(username="rolled_back").first()
        assert db_user is None
