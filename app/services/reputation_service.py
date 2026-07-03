"""
Reputation Service - Phase 20 Reputation System.
Aggregates points across different learning and defense systems to calculate tiers.
"""
from app.extensions import db
from app.models.researcher_profile import ResearcherProfile
from app.models.vulnerability_report import VulnerabilityReport
from app.models.research_report import ResearchReport
from app.models.case import Case
from app.models.badge import UserBadge

class ReputationService:

    @staticmethod
    def calculate_reputation(user_id: int) -> dict:
        """Aggregates points to determine active tier level."""
        profile = ResearcherProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return {"points": 0, "tier": "Bronze"}

        # 1. Bug bounties count
        bounty_count = VulnerabilityReport.query.filter_by(researcher_id=user_id, status='accepted').count()
        bounty_pts = bounty_count * 50

        # 2. Research reports count
        report_count = ResearchReport.query.filter_by(author_id=user_id).count()
        report_pts = report_count * 30

        # 3. SOC cases managed
        soc_count = db.session.query(Case).filter_by(analyst_id=user_id).count()
        soc_pts = soc_count * 20

        # 4. Certifications / LMS Badges
        badge_count = UserBadge.query.filter_by(user_id=user_id).count()
        badge_pts = badge_count * 15

        # Base profile points
        total_points = profile.research_points + bounty_pts + report_pts + soc_pts + badge_pts

        # Determine Tier
        if total_points >= 1000:
            tier = "Diamond"
        elif total_points >= 500:
            tier = "Platinum"
        elif total_points >= 250:
            tier = "Gold"
        elif total_points >= 100:
            tier = "Silver"
        else:
            tier = "Bronze"

        # Update cache profile
        profile.reputation = total_points
        db.session.commit()

        return {
            "user_id": user_id,
            "bounty_points": bounty_pts,
            "report_points": report_pts,
            "soc_points": soc_pts,
            "badge_points": badge_pts,
            "total_points": total_points,
            "tier": tier
        }
