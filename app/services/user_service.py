from app.repositories.user_repository import UserRepository
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.challenge_repository import ChallengeRepository

class UserService:
    @staticmethod
    def get_user_profile_data(username):
        user = UserRepository.get_by_name(username)
        if not user:
            return None

        challenges = ChallengeRepository.get_all(include_hidden=True)
        solved_list = SubmissionRepository.get_solved_by_user(username)

        solved_dict = {}
        total_score = 0
        for sub in solved_list:
            ch = next((c for c in challenges if c.id == sub.challenge_id), None)
            if ch:
                solved_dict[ch.legacy_id] = {
                    "title": ch.title,
                    "category": ch.category.name if ch.category else "General",
                    "points": sub.points,
                    "time": sub.time.isoformat(),
                    "elapsed": sub.elapsed
                }
                total_score += sub.points

        # Deduct hint cost values
        hint_cost = sum(unlock.hint.cost for unlock in user.hint_unlocks if unlock.hint)
        total_score = max(0, total_score - hint_cost)

        return {
            "username": user.username,
            "display_name": user.display_name or user.username,
            "registered_at": user.registered_at,
            "role": user.role,
            "total_score": total_score,
            "solved_count": len(solved_dict),
            "solves": solved_dict,
            "bio": user.bio or "No bio provided.",
            "timezone": user.timezone or "UTC",
            "preferred_theme": user.preferred_theme or "default"
        }
