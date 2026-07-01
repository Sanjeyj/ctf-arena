from sqlalchemy.orm import joinedload
from app.extensions import db, safe_commit, utcnow
from app.models.submission import Submission
from app.models.user import User
from app.models.challenge import Challenge
import datetime

class SubmissionRepository:
    @staticmethod
    def get_solved_by_user(username):
        return Submission.query.options(joinedload(Submission.challenge)).join(User).filter(
            User.username == username,
            User.is_deleted == False,
            Submission.correct == True,
            Submission.points > 0
        ).all()

    @staticmethod
    def get_all_by_user(username):
        """Get ALL submissions (correct + wrong) by a user."""
        return Submission.query.options(joinedload(Submission.challenge)).join(User).filter(
            User.username == username,
            User.is_deleted == False
        ).order_by(Submission.time.desc()).all()

    @staticmethod
    def get_by_id(sub_id):
        return Submission.query.get(sub_id)

    @staticmethod
    def get_all(page=1, per_page=50, user_id=None, challenge_id=None,
                status=None, correct=None, order_by="time_desc"):
        """Paginated, filtered, sorted submission query for admin manager."""
        q = Submission.query

        if user_id:
            q = q.filter_by(user_id=user_id)
        if challenge_id:
            q = q.filter_by(challenge_id=challenge_id)
        if status:
            q = q.filter_by(status=status)
        if correct is not None:
            q = q.filter_by(correct=correct)

        if order_by == "time_asc":
            q = q.order_by(Submission.time.asc())
        else:
            q = q.order_by(Submission.time.desc())

        total = q.count()
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def get_earliest_solve(challenge_id):
        """Get the first correct solve for a challenge (for first blood tracking)."""
        return Submission.query.filter_by(
            challenge_id=challenge_id,
            correct=True
        ).filter(Submission.points > 0).order_by(Submission.time.asc()).first()

    @staticmethod
    def add_solve(username, ch_id, points, elapsed, submitted_flag=None):
        user = User.query.filter_by(username=username, is_deleted=False).first()
        if not user:
            raise ValueError(f"User {username} not found")

        # Resolve challenge by legacy_id or integer PK
        if isinstance(ch_id, int) or (isinstance(ch_id, str) and ch_id.isdigit()):
            challenge = Challenge.query.filter_by(id=int(ch_id), is_deleted=False).first()
        else:
            challenge = Challenge.query.filter_by(legacy_id=str(ch_id), is_deleted=False).first()

        if not challenge:
            raise ValueError(f"Challenge {ch_id} not found")

        sub = Submission(
            user_id=user.id,
            challenge_id=challenge.id,
            points=points,
            elapsed=elapsed,
            time=datetime.datetime.utcnow(),
            submitted_flag=submitted_flag,
            correct=True,
            status="correct"
        )
        db.session.add(sub)
        safe_commit()
        return sub

    @staticmethod
    def add_wrong_attempt(user_id, challenge_id, submitted_flag=None):
        """Record a wrong submission attempt."""
        sub = Submission(
            user_id=user_id,
            challenge_id=challenge_id,
            points=0,
            time=datetime.datetime.utcnow(),
            elapsed=0,
            submitted_flag=submitted_flag,
            correct=False,
            status="wrong"
        )
        db.session.add(sub)
        safe_commit()
        return sub

    @staticmethod
    def delete(sub_id):
        sub = Submission.query.get(sub_id)
        if sub:
            db.session.delete(sub)
            safe_commit()
            return True
        return False

    @staticmethod
    def update_status(sub_id, correct, status, points=None):
        sub = Submission.query.get(sub_id)
        if sub:
            sub.correct = correct
            sub.status = status
            if points is not None:
                sub.points = points
            safe_commit()
        return sub

    @staticmethod
    def reset_user_solves(username):
        user = User.query.filter_by(username=username, is_deleted=False).first()
        if user:
            Submission.query.filter_by(user_id=user.id).delete()
            user.registered_at = utcnow()
            safe_commit()
            return True
        return False

    @staticmethod
    def reset_all_solves():
        Submission.query.delete()
        User.query.delete()
        safe_commit()
        return True

    @staticmethod
    def get_recent(limit=20, correct_only=False):
        q = Submission.query
        if correct_only:
            q = q.filter_by(correct=True).filter(Submission.points > 0)
        return q.order_by(Submission.time.desc()).limit(limit).all()
