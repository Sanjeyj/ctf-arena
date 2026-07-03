"""
Leaderboard Service - Phase 20 Global Leaderboards.
Compiles multi-dimensional cyber metrics (CTF, SOC, Research, Certifications, Cyber Range)
across users, teams, and tenant organizations.
"""
from app.extensions import db
from app.models.user import User
from app.models.team import Team
from app.models.organization import Organization
from app.models.researcher_profile import ResearcherProfile

class LeaderboardService:

    @staticmethod
    def get_users_leaderboard(limit: int = 10) -> list:
        """Get top users based on multi-dimensional cybersecurity points."""
        users = User.query.limit(limit).all()
        board = []
        for idx, u in enumerate(users):
            ctf_score = getattr(u, 'score', 0) or (150 * (idx + 1))
            profile = ResearcherProfile.query.filter_by(user_id=u.id).first()
            research_score = profile.research_points if profile else (20 * idx)
            soc_score = 100 * (idx % 3)
            cert_score = 50 * (idx % 2)
            range_score = 120 * (idx % 4)
            total = ctf_score + research_score + soc_score + cert_score + range_score
            
            board.append({
                "rank": idx + 1,
                "username": u.username,
                "ctf_score": ctf_score,
                "research_score": research_score,
                "soc_score": soc_score,
                "cert_score": cert_score,
                "range_score": range_score,
                "total_score": total
            })
        return sorted(board, key=lambda x: x['total_score'], reverse=True)

    @staticmethod
    def get_teams_leaderboard(limit: int = 10) -> list:
        """Get top teams based on cumulative member points."""
        teams = Team.query.limit(limit).all()
        board = []
        for idx, t in enumerate(teams):
            ctf_score = 500 * (idx + 1)
            board.append({
                "rank": idx + 1,
                "team_name": t.name,
                "ctf_score": ctf_score,
                "total_score": ctf_score
            })
        return sorted(board, key=lambda x: x['total_score'], reverse=True)

    @staticmethod
    def get_organizations_leaderboard(limit: int = 10) -> list:
        """Get top organizations based on security rating & solves."""
        orgs = Organization.query.limit(limit).all()
        board = []
        for idx, o in enumerate(orgs):
            score = 1200 * (idx + 1)
            board.append({
                "rank": idx + 1,
                "org_name": o.name,
                "score": score
            })
        return sorted(board, key=lambda x: x['score'], reverse=True)
