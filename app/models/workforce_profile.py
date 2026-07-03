"""
WorkforceProfile model - Phase 28 Cyber Civilization Platform.
Tracks national security workforce skills, profiles, and experience metrics.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class WorkforceProfile(db.Model, TimestampMixin, TenantMixin):
    """Security workforce profile model."""
    __tablename__ = 'workforce_profiles'

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(120), nullable=False)  # Analyst, Architect, Developer, Lead
    skill_score = db.Column(db.Float, default=0.5, nullable=False)  # 0.0 to 1.0
    experience = db.Column(db.Integer, default=1, nullable=False)  # years
    certifications = db.Column(db.Text, nullable=True)  # JSON or comma-separated list

    def __repr__(self):
        return f'<WorkforceProfile role={self.role!r} skill={self.skill_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'skill_score': self.skill_score,
            'experience': self.experience,
            'certifications': self.certifications,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
