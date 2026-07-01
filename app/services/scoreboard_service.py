from app.utils.legacy import load_scores, compute_leaderboard, build_stats, CHALLENGES
from app.repositories.submission_repository import SubmissionRepository

class ScoreboardService:
    @staticmethod
    def get_scoreboard_data(username=None):
        data = load_scores()
        leaderboard = compute_leaderboard(data)
        stats = build_stats(data)
        solved = SubmissionRepository.get_solved_by_user(username) if username else {}
        return leaderboard, stats, solved, CHALLENGES
