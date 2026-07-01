from app.repositories.analytics_repository import AnalyticsRepository
from app.models.submission import Submission
from app.models.challenge import Challenge
from app.models.user import User

class AnalyticsService:
    @staticmethod
    def get_full_analytics():
        basics = AnalyticsRepository.get_basic_stats()
        
        # Calculate rates
        total_subs = basics["total_submissions"]
        correct_subs = basics["correct_submissions"]
        
        acceptance_rate = (correct_subs / total_subs * 100.0) if total_subs > 0 else 0.0
        
        # Calculations of averages
        total_challs = basics["total_challenges"]
        average_attempts = (total_subs / total_challs) if total_challs > 0 else 0.0
        
        # Averages for solve elapsed time
        solves_with_time = Submission.query.filter_by(correct=True).all()
        times_list = [s.elapsed for s in solves_with_time if s.elapsed is not None]
        avg_solve_time = (sum(times_list) / len(times_list)) if times_list else 0.0

        return {
            "basics": basics,
            "acceptance_rate": round(acceptance_rate, 2),
            "average_attempts_per_challenge": round(average_attempts, 2),
            "average_solve_time_seconds": round(avg_solve_time, 2),
            "solve_distribution": AnalyticsRepository.get_solve_distribution(),
            "category_distribution": AnalyticsRepository.get_category_distribution(),
            "difficulty_distribution": AnalyticsRepository.get_difficulty_distribution(),
            "attempts_per_challenge": AnalyticsRepository.get_attempts_per_challenge(),
            "top_solvers": dict(AnalyticsRepository.get_top_solvers(limit=5))
        }

    @staticmethod
    def get_first_blood_feed():
        # Earliest correct solve for each active challenge
        challenges = Challenge.query.filter_by(is_deleted=False).all()
        feed = []
        for ch in challenges:
            first_solve = Submission.query.filter_by(challenge_id=ch.id, correct=True)\
                                    .order_by(Submission.time.asc()).first()
            if first_solve:
                user = User.query.get(first_solve.user_id)
                feed.append({
                    "challenge_title": ch.title,
                    "challenge_legacy_id": ch.legacy_id,
                    "username": user.username if user else "Unknown",
                    "time": first_solve.time,
                    "elapsed": first_solve.elapsed
                })
        # Sort feed by solve time descending to show recent first bloods first
        feed.sort(key=lambda x: x["time"], reverse=True)
        return feed
