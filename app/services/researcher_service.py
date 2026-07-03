"""
Researcher Service - Phase 20 Researcher Profiles.
Handles cybersecurity stats, skills lists, badging indicators, and ranking updates.
"""
import json
from app.extensions import db
from app.models.researcher_profile import ResearcherProfile
from app.models.user import User

class ResearcherService:

    @staticmethod
    def get_or_create_profile(user_id: int, org_id: int = None) -> ResearcherProfile:
        """Fetch a researcher profile, or create it if not present."""
        profile = ResearcherProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            user = db.session.get(User, user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            profile = ResearcherProfile(
                user_id=user_id,
                bio="",
                country="",
                skills="",
                social_links="{}",
                reputation=0,
                research_points=0,
                ranking=9999,
                hall_of_fame=False,
                organization_id=org_id
            )
            db.session.add(profile)
            db.session.commit()
        return profile

    @staticmethod
    def update_profile(user_id: int, **kwargs) -> ResearcherProfile:
        profile = ResearcherService.get_or_create_profile(user_id)
        
        # Serialize social links if dictionary
        if 'social_links' in kwargs and isinstance(kwargs['social_links'], dict):
            profile.social_links = json.dumps(kwargs.pop('social_links'))
            
        for key, val in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, val)
        db.session.commit()
        return profile

    @staticmethod
    def list_hall_of_fame(limit: int = 50):
        """Retrieve highest ranked researchers ordered by reputation."""
        return ResearcherProfile.query.filter_by(hall_of_fame=True)\
            .order_by(ResearcherProfile.reputation.desc()).limit(limit).all()

    @staticmethod
    def calculate_rankings():
        """Recalculate ranking fields for all researchers by reputation."""
        profiles = ResearcherProfile.query.order_by(ResearcherProfile.reputation.desc()).all()
        for idx, p in enumerate(profiles):
            p.ranking = idx + 1
            if p.reputation >= 100:
                p.hall_of_fame = True
        db.session.commit()
