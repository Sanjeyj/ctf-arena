"""
ResearcherProfile model - Phase 20 Researcher Profiles.
Caches cybersecurity stats, rankings, skills, and links for individuals.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class ResearcherProfile(db.Model, TimestampMixin, TenantMixin):
    """Researcher profile extension details."""
    __tablename__ = 'researcher_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    bio = db.Column(db.Text, nullable=True)
    country = db.Column(db.String(80), nullable=True)
    skills = db.Column(db.Text, nullable=True) # Comma-separated skills
    social_links = db.Column(db.Text, nullable=True) # JSON dictionary string
    reputation = db.Column(db.Integer, default=0)
    research_points = db.Column(db.Integer, default=0)
    ranking = db.Column(db.Integer, default=9999)
    hall_of_fame = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('researcher_profile', uselist=False, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<ResearcherProfile user_id={self.user_id} rank={self.ranking}>'

    def to_dict(self):
        try:
            links = json.loads(self.social_links) if self.social_links else {}
        except Exception:
            links = {}
            
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'unknown',
            'bio': self.bio,
            'country': self.country,
            'skills': [s.strip() for s in self.skills.split(',')] if self.skills else [],
            'social_links': links,
            'reputation': self.reputation,
            'research_points': self.research_points,
            'ranking': self.ranking,
            'hall_of_fame': self.hall_of_fame
        }
