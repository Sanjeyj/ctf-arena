from app.repositories.submission_repository import SubmissionRepository
from app.utils.legacy import load_scores, compute_leaderboard, build_stats, CHALLENGES

class AdminService:
    @staticmethod
    def get_dashboard_stats():
        data = load_scores()
        leaderboard = compute_leaderboard(data)
        stats = build_stats(data)
        return leaderboard, stats, CHALLENGES

    @staticmethod
    def reset_all():
        return SubmissionRepository.reset_all_solves()
