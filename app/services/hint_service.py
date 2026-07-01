from app.repositories.hint_repository import HintRepository
from app.repositories.user_repository import UserRepository
from app.services.scoreboard_service import ScoreboardService

class HintService:
    @staticmethod
    def get_hints_for_challenge(challenge_id, user_id=None):
        hints = HintRepository.get_for_challenge(challenge_id)
        result = []
        for h in hints:
            if not h.enabled:
                continue
            is_unlocked = h.cost == 0 or (user_id is not None and HintRepository.is_unlocked(h.id, user_id))
            result.append({
                "id": h.id,
                "title": h.title or f"Hint #{h.display_order or 1}",
                "content": h.content if is_unlocked else None,
                "cost": h.cost,
                "is_unlocked": is_unlocked,
                "display_order": h.display_order
            })
        return result

    @staticmethod
    def get_hint_by_id(hint_id):
        return HintRepository.get_by_id(hint_id)

    @staticmethod
    def create_hint(challenge_id, content, cost=0, title=None, visible=True, enabled=True, display_order=0):
        content = content.strip()
        if not content:
            return None, "Hint content cannot be empty."
        hint = HintRepository.create(challenge_id, content, cost, title, visible, enabled, display_order)
        return hint, None

    @staticmethod
    def update_hint(hint_id, **kwargs):
        hint = HintRepository.get_by_id(hint_id)
        if not hint:
            return None, "Hint not found."
        if "content" in kwargs and not kwargs["content"].strip():
            return None, "Hint content cannot be empty."
        updated = HintRepository.update(hint, **kwargs)
        return updated, None

    @staticmethod
    def delete_hint(hint_id):
        hint = HintRepository.get_by_id(hint_id)
        if not hint:
            return False, "Hint not found."
        HintRepository.delete(hint)
        return True, None

    @staticmethod
    def unlock_hint(hint_id, user_id):
        hint = HintRepository.get_by_id(hint_id)
        if not hint:
            return False, "Hint not found."
            
        if hint.cost == 0:
            return True, None
            
        if HintRepository.is_unlocked(hint.id, user_id):
            return True, None

        # Check user's current points
        user = UserRepository.get_by_id(user_id)
        if not user:
            return False, "User not found."

        # Compute dynamic user score
        from app.services.user_service import UserService
        stats = UserService.get_user_profile_data(user.username)
        user_score = stats["total_score"] if stats else 0

        if user_score < hint.cost:
            return False, f"Not enough points. This hint costs {hint.cost} points, but you only have {user_score}."

        unlocked = HintRepository.unlock(hint.id, user_id)
        if unlocked:
            return True, None
        return False, "Failed to unlock hint."
