import datetime
from app.extensions import db
from app.repositories.challenge_repository import ChallengeRepository
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.user_repository import UserRepository
from app.models.challenge import Challenge
from app.models.submission import Submission
from app.services.scoring_service import ScoringService
from app.services.flag_service import FlagService
from app.utils.legacy import get_legacy_db

class ChallengeService:
    @staticmethod
    def get_challenge_by_any_id(any_id):
        ch = ChallengeRepository.get_by_legacy_id(str(any_id))
        if ch:
            return ch
        try:
            ch_id = int(any_id)
            return ChallengeRepository.get_by_id(ch_id)
        except ValueError:
            return None

    @staticmethod
    def get_dashboard_context(username):
        challenges_list = ChallengeRepository.get_all(include_hidden=False)
        solved_list = SubmissionRepository.get_solved_by_user(username)
        user = UserRepository.get_by_name(username)
        
        # Build challenges dictionary keyed by legacy_id
        challenges_dict = {}
        for ch in challenges_list:
            challenges_dict[ch.legacy_id] = {
                "id": ch.legacy_id,
                "title": ch.title,
                "category": ch.category.name if ch.category else "General",
                "points": ch.current_points,
                "icon": ch.icon,
                "difficulty": ch.difficulty,
                "description": ch.description
            }

        # Build solved dictionary keyed by challenge legacy_id
        solved_dict = {}
        total_pts = 0
        for sub in solved_list:
            ch = next((c for c in challenges_list if c.id == sub.challenge_id), None)
            if ch:
                solved_dict[ch.legacy_id] = {
                    "points": sub.points,
                    "time": sub.time.isoformat(),
                    "elapsed": sub.elapsed
                }
                total_pts += sub.points

        registered_at = user.registered_at.isoformat() if user else datetime.datetime.utcnow().isoformat()
        
        return challenges_dict, solved_dict, total_pts, registered_at

    @staticmethod
    def get_challenge(ch_id, username):
        ch = ChallengeService.get_challenge_by_any_id(ch_id)
        if not ch or not ch.visible:
            return None, None
            
        ch_dict = {
            "id": ch.legacy_id,
            "title": ch.title,
            "category": ch.category.name if ch.category else "General",
            "points": ch.current_points,
            "icon": ch.icon,
            "difficulty": ch.difficulty,
            "description": ch.description,
            "flag": ch.flags[0].content if ch.flags else ""
        }
        
        solved_list = SubmissionRepository.get_solved_by_user(username)
        solved_dict = {}
        for sub in solved_list:
            sch = Challenge.query.get(sub.challenge_id)
            if sch:
                solved_dict[sch.legacy_id] = {
                    "points": sub.points,
                    "time": sub.time.isoformat(),
                    "elapsed": sub.elapsed
                }
                
        return ch_dict, solved_dict

    @staticmethod
    def submit_flag(ch_id, username, submitted_flag):
        ch = ChallengeService.get_challenge_by_any_id(ch_id)
        if not ch or not ch.visible or ch.state == "locked":
            return False, "Challenge is not accessible.", 0

        # Check solved status
        solved_list = SubmissionRepository.get_solved_by_user(username)
        for sub in solved_list:
            if sub.challenge_id == ch.id:
                return True, "Already solved! 🎉", sub.points

        user = UserRepository.get_by_name(username)
        if not user:
            return False, "User not found.", 0

        # Check max attempts limit
        if ch.max_attempts > 0:
            user_attempts = Submission.query.filter_by(user_id=user.id, challenge_id=ch.id).count()
            if user_attempts >= ch.max_attempts:
                return False, f"Maximum attempts limit ({ch.max_attempts}) reached.", 0

        # Verify flag
        correct = False
        for f in ch.flags:
            if FlagService.verify_flag(f, submitted_flag):
                correct = True
                break

        # Increment global attempts counter
        ch.attempt_count += 1
        db.session.add(ch)
        db.session.commit()

        if correct:
            reg_time = user.registered_at if user else datetime.datetime.utcnow()
            elapsed = (datetime.datetime.utcnow() - reg_time).total_seconds()
            
            # Default point award value
            if ch.decay_type == "legacy_time":
                points = max(10, ch.initial_points - int(elapsed // 10))
            else:
                points = ch.current_points
            
            # Record solve with submitted flag stored for audit
            SubmissionRepository.add_solve(username, ch.legacy_id, points, int(elapsed),
                                           submitted_flag=submitted_flag)
            
            # Recalculate dynamic scoring and solves count
            ChallengeService.update_challenge_solves_points(ch)
            
            # Return updated solve feedback
            return True, f"Correct! +{points} points (solved in {int(elapsed)}s) 🎉", points

        # Record failed attempt with submitted flag stored for audit
        SubmissionRepository.add_wrong_attempt(
            user_id=user.id,
            challenge_id=ch.id,
            submitted_flag=submitted_flag
        )

        return False, "Wrong flag. Try again! ❌", 0

    @staticmethod
    def update_challenge_solves_points(challenge):
        # Count solves
        solves_count = Submission.query.filter(
            Submission.challenge_id == challenge.id,
            Submission.points > 0
        ).count()
        challenge.solve_count = solves_count
        
        # Calculate dynamic points
        new_points = ScoringService.calculate_points(challenge, solves_count)
        challenge.current_points = new_points
        challenge.points = new_points # backwards compatibility
        db.session.add(challenge)
        
        # Re-sync points on all solve submissions for this challenge
        if challenge.decay_type in ["linear", "logarithmic"]:
            submissions = Submission.query.filter(
                Submission.challenge_id == challenge.id,
                Submission.points > 0
            ).all()
            for sub in submissions:
                sub.points = new_points
                db.session.add(sub)
        
        db.session.commit()

    @staticmethod
    def rebuild_all_challenge_points():
        challenges = Challenge.query.filter_by(is_deleted=False).all()
        for ch in challenges:
            ChallengeService.update_challenge_solves_points(ch)

    @staticmethod
    def verify_admin_cookie(role_cookie):
        if role_cookie == "admin":
            return {"status": "Welcome admin!", "flag": "FLAG{c00ki3s_are_delic10us}"}, True
        return {
            "status": f"Access denied. You are: {role_cookie}",
            "hint": "Only admins can see the flag..."
        }, False

    @staticmethod
    def search_vault(query):
        if not query.strip():
            return []
        conn = get_legacy_db()
        cursor = conn.cursor()
        sql = f"SELECT name, description FROM products WHERE name LIKE '%{query}%'"
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [{"name": r[0], "description": r[1]} for r in rows]

    @staticmethod
    def reset_progress(username):
        res = SubmissionRepository.reset_user_solves(username)
        # Rebuild solves count for challenges solved by this user
        ChallengeService.rebuild_all_challenge_points()
        return res

    # CMS Admin CRUD Operations
    @staticmethod
    def create_challenge(legacy_id, title, description, points, difficulty, category_id=None, **kwargs):
        ch = ChallengeRepository.create(legacy_id, title, description, points, difficulty, category_id, **kwargs)
        return ch

    @staticmethod
    def update_challenge(ch_id, **kwargs):
        ch = ChallengeRepository.get_by_id(ch_id)
        if not ch:
            return None
        updated = ChallengeRepository.update(ch, **kwargs)
        ChallengeService.update_challenge_solves_points(updated)
        return updated

    @staticmethod
    def delete_challenge(ch_id):
        ch = ChallengeRepository.get_by_id(ch_id)
        if ch:
            ChallengeRepository.delete(ch)
            return True
        return False

    @staticmethod
    def list_challenges(search=None, category_id=None, difficulty=None, visibility=None, state=None, author_id=None, sort_by=None, page=None, per_page=None):
        return ChallengeRepository.list_challenges(search, category_id, difficulty, visibility, state, author_id, sort_by, page, per_page)
