from app.repositories.challenge_repository import ChallengeRepository
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.user_repository import UserRepository
from app.utils.legacy import get_legacy_db
import datetime

class ChallengeService:
    @staticmethod
    def get_dashboard_context(username):
        challenges = ChallengeRepository.get_all()
        solved = SubmissionRepository.get_solved_by_user(username)
        user = UserRepository.get_by_name(username)
        
        # Calculate scores
        total_pts = sum(solved[c]["points"] for c in solved if c in challenges and solved[c].get("points") is not None)
        registered_at = user["registered_at"] if user else datetime.datetime.now().isoformat()
        
        return challenges, solved, total_pts, registered_at

    @staticmethod
    def get_challenge(ch_id, username):
        ch = ChallengeRepository.get_by_id(ch_id)
        if not ch:
            return None, None
        solved = SubmissionRepository.get_solved_by_user(username)
        return ch, solved

    @staticmethod
    def submit_flag(ch_id, username, submitted_flag):
        ch = ChallengeRepository.get_by_id(ch_id)
        if not ch:
            return False, "Challenge not found.", 0

        solved = SubmissionRepository.get_solved_by_user(username)
        if ch_id in solved:
            return True, "Already solved! 🎉", solved[ch_id]["points"]

        if submitted_flag.strip() == ch["flag"]:
            user = UserRepository.get_by_name(username)
            reg_time = datetime.datetime.fromisoformat(user["registered_at"]) if user else datetime.datetime.now()
            elapsed = (datetime.datetime.now() - reg_time).total_seconds()
            
            # Time-based decay: 1 point per 10 seconds elapsed since registration, minimum 10 points
            points = max(10, ch["points"] - int(elapsed // 10))
            
            SubmissionRepository.add_solve(username, ch_id, points, int(elapsed))
            return True, f"Correct! +{points} points (solved in {int(elapsed)}s) 🎉", points

        return False, "Wrong flag. Try again! ❌", 0

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
        # Vulnerable SQL Injection!
        sql = f"SELECT name, description FROM products WHERE name LIKE '%{query}%'"
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [{"name": r[0], "description": r[1]} for r in rows]

    @staticmethod
    def reset_progress(username):
        return SubmissionRepository.reset_user_solves(username)
