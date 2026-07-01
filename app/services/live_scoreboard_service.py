from app.repositories.user_repository import UserRepository
from app.repositories.challenge_repository import ChallengeRepository
from app.repositories.submission_repository import SubmissionRepository
from app.services.competition_service import CompetitionService
from app.utils.legacy import compute_leaderboard, build_stats
import datetime
from app.extensions import utcnow

class LiveScoreboardService:
    @staticmethod
    def get_live_rankings(is_admin_preview=False):
        comp = CompetitionService.get_active_competition()
        now = utcnow()
        
        # Check if freeze is active
        freeze_active = False
        cutoff_time = None
        if comp and comp.freeze_time and comp.unfreeze_time:
            if comp.freeze_time <= now < comp.unfreeze_time:
                freeze_active = True
                if not is_admin_preview:
                    cutoff_time = comp.freeze_time

        users = UserRepository.get_all_participants()
        challenges = ChallengeRepository.get_all(include_hidden=False)
        
        data = {"participants": {}}
        for u in users:
            solved_dict = {}
            # Filter submissions
            user_subs = u.submissions
            if cutoff_time:
                user_subs = [s for s in user_subs if s.time < cutoff_time]
                
            for sub in user_subs:
                if sub.points <= 0 or not sub.correct:
                    continue
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
        
        # Adjust leaderboard scores to deduct cost of unlocked hints
        for entry in leaderboard:
            u = next((user for user in users if user.username == entry["name"]), None)
            if u:
                hint_cost = 0
                for unlock in u.hint_unlocks:
                    if cutoff_time and unlock.created_at >= cutoff_time:
                        continue # bypass hints unlocked after freeze
                    if unlock.hint:
                        hint_cost += unlock.hint.cost
                entry["score"] = max(0, entry["score"] - hint_cost)

        # Re-sort leaderboard after adjustments
        leaderboard.sort(key=lambda x: (-x["score"], x["last_solve"]))
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
            
        # Enrich leaderboard with analytics: solved counts, penalty, first bloods
        for entry in leaderboard:
            username = entry["name"]
            u = next((user for user in users if user.username == username), None)
            if u:
                # Solve count
                entry["solved_count"] = entry["solve_count"]
                
                # Penalty time (sum of elapsed times in minutes for solves)
                user_subs = u.submissions
                if cutoff_time:
                    user_subs = [s for s in user_subs if s.time < cutoff_time]
                correct_subs = [s for s in user_subs if s.correct and s.points > 0]
                entry["penalty_time"] = sum(s.elapsed or 0 for s in correct_subs) // 60
                
                # First blood count
                fb_count = 0
                for sub in correct_subs:
                    # Is this sub the first blood for the challenge?
                    first = SubmissionRepository.get_earliest_solve(sub.challenge_id)
                    if first and first.id == sub.id:
                        fb_count += 1
                entry["first_blood_count"] = fb_count
                
                # Static default trend indicator
                entry["trend"] = "stable" # stable, up, down

        return {
            "leaderboard": leaderboard,
            "freeze_active": freeze_active,
            "timer": LiveScoreboardService.get_timer_status(comp)
        }

    @staticmethod
    def get_timer_status(comp):
        if not comp:
            return {"state": "practice", "remaining_seconds": 0}
        
        state = CompetitionService.get_competition_state(comp)
        now = utcnow()
        
        remaining = 0
        if state == "scheduled" and comp.start_time:
            remaining = int((comp.start_time - now).total_seconds())
        elif state == "registration_open" and comp.start_time:
            remaining = int((comp.start_time - now).total_seconds())
        elif state in ["running", "frozen"] and comp.end_time:
            remaining = int((comp.end_time - now).total_seconds())
            
        return {
            "state": state,
            "remaining_seconds": max(0, remaining),
            "start_time": comp.start_time.isoformat() if comp.start_time else None,
            "end_time": comp.end_time.isoformat() if comp.end_time else None
        }
