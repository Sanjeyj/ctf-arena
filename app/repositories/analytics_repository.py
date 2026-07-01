from app.extensions import db
from app.models.submission import Submission
from app.models.challenge import Challenge
from app.models.category import Category
from app.models.user import User
from sqlalchemy import func

class AnalyticsRepository:
    @staticmethod
    def get_basic_stats():
        total_users = User.query.count()
        total_challenges = Challenge.query.filter_by(is_deleted=False).count()
        total_submissions = Submission.query.count()
        
        correct_subs = Submission.query.filter_by(correct=True).count()
        wrong_subs = Submission.query.filter(Submission.correct == False, Submission.status == "wrong").count()
        duplicate_subs = Submission.query.filter_by(status="duplicate").count()

        return {
            "total_users": total_users,
            "total_challenges": total_challenges,
            "total_submissions": total_submissions,
            "correct_submissions": correct_subs,
            "wrong_submissions": wrong_subs,
            "duplicate_submissions": duplicate_subs
        }

    @staticmethod
    def get_solve_distribution():
        # Solves grouped by challenge title
        results = db.session.query(
            Challenge.title,
            func.count(Submission.id)
        ).join(Submission, Challenge.id == Submission.challenge_id)\
         .filter(Submission.correct == True, Challenge.is_deleted == False)\
         .group_by(Challenge.title).all()
        return dict(results)

    @staticmethod
    def get_category_distribution():
        # Solves grouped by category name
        results = db.session.query(
            Category.name,
            func.count(Submission.id)
        ).join(Challenge, Category.id == Challenge.category_id)\
         .join(Submission, Challenge.id == Submission.challenge_id)\
         .filter(Submission.correct == True, Challenge.is_deleted == False)\
         .group_by(Category.name).all()
        return dict(results)

    @staticmethod
    def get_difficulty_distribution():
        # Solves grouped by difficulty string
        results = db.session.query(
            Challenge.difficulty,
            func.count(Submission.id)
        ).join(Submission, Challenge.id == Submission.challenge_id)\
         .filter(Submission.correct == True, Challenge.is_deleted == False)\
         .group_by(Challenge.difficulty).all()
        return dict(results)

    @staticmethod
    def get_attempts_per_challenge():
        # Total attempts (both wrong and correct) grouped by challenge
        results = db.session.query(
            Challenge.title,
            func.count(Submission.id)
        ).join(Submission, Challenge.id == Submission.challenge_id)\
         .filter(Challenge.is_deleted == False)\
         .group_by(Challenge.title).all()
        return dict(results)

    @staticmethod
    def get_top_solvers(limit=10):
        # Users with most solves
        results = db.session.query(
            User.username,
            func.count(Submission.id)
        ).join(Submission, User.id == Submission.user_id)\
         .filter(Submission.correct == True)\
         .group_by(User.username)\
         .order_by(func.count(Submission.id).desc())\
         .limit(limit).all()
        return results
