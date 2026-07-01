from app.repositories.user_repository import UserRepository
from app.repositories.challenge_repository import ChallengeRepository
from app.repositories.submission_repository import SubmissionRepository
from app.utils.legacy import compute_leaderboard, build_stats
import datetime

class ScoreboardService:
    @staticmethod
    def get_scoreboard_data(username=None):
        users = UserRepository.get_all_participants()
        challenges = ChallengeRepository.get_all(include_hidden=False)
        
        # Build legacy format dict for compatibility with compute_leaderboard & build_stats
        data = {"participants": {}}
        for u in users:
            solved_dict = {}
            for sub in u.submissions:
                if sub.points <= 0:
                    continue # skip failed attempts
                # Find challenge for this submission
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
        
        # Adjust leaderboard scores to deduct cost of unlocked hints
        for entry in leaderboard:
            u = next((user for user in users if user.username == entry["name"]), None)
            if u:
                hint_cost = sum(unlock.hint.cost for unlock in u.hint_unlocks if unlock.hint)
                entry["score"] = max(0, entry["score"] - hint_cost)
                
        # Re-sort leaderboard after adjustments
        leaderboard.sort(key=lambda x: (-x["score"], x["last_solve"]))
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
        
        # Get solved for the logged-in user
        solved_dict = {}
        if username:
            solved_list = SubmissionRepository.get_solved_by_user(username)
            for sub in solved_list:
                ch = next((c for c in challenges if c.id == sub.challenge_id), None)
                if ch:
                    solved_dict[ch.legacy_id] = {
                        "points": sub.points,
                        "time": sub.time.isoformat(),
                        "elapsed": sub.elapsed
                    }
                    
        # Build challenges dictionary keyed by legacy_id
        challenges_dict = {}
        for ch in challenges:
            challenges_dict[ch.legacy_id] = {
                "id": ch.legacy_id,
                "title": ch.title,
                "category": ch.category.name if ch.category else "General",
                "points": ch.current_points,
                "icon": ch.icon,
                "difficulty": ch.difficulty,
                "description": ch.description
            }
            
        return leaderboard, stats, solved_dict, challenges_dict
