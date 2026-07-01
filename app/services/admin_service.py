from app.repositories.user_repository import UserRepository
from app.repositories.challenge_repository import ChallengeRepository
from app.repositories.submission_repository import SubmissionRepository
from app.utils.legacy import compute_leaderboard, build_stats
import datetime

class AdminService:
    @staticmethod
    def get_dashboard_stats():
        users = UserRepository.get_all_participants()
        challenges = ChallengeRepository.get_all()
        
        # Build legacy format dict for compatibility
        data = {"participants": {}}
        for u in users:
            solved_dict = {}
            for sub in u.submissions:
                ch = next((c for c in challenges if c.id == sub.challenge_id), None)
                if ch:
                    solved_dict[ch.legacy_id] = {
                        "time": sub.time.isoformat(),
                        "points": sub.points,
                        "elapsed": sub.elapsed
                    }
            data["participants"][u.username] = {
                "registered_at": u.registered_at.isoformat(),
                "solved": solved_dict
            }
            
        leaderboard = compute_leaderboard(data)
        stats = build_stats(data)
        
        # Build challenges dictionary keyed by legacy_id
        challenges_dict = {}
        for ch in challenges:
            challenges_dict[ch.legacy_id] = {
                "id": ch.legacy_id,
                "title": ch.title,
                "category": ch.category.name if ch.category else "General",
                "points": ch.points,
                "icon": ch.icon,
                "difficulty": ch.difficulty,
                "description": ch.description
            }
            
        return leaderboard, stats, challenges_dict

    @staticmethod
    def reset_all():
        return SubmissionRepository.reset_all_solves()
