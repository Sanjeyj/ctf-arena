"""
Program model - Phase 20 Bug Bounty Platform.
Tracks public, private, or invite-only bug bounty programs.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class Program(db.Model, TimestampMixin, TenantMixin):
    """Bug bounty program catalog."""
    __tablename__ = 'programs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    program_type = db.Column(db.String(32), default='public') # public, private, invite-only
    reward_min = db.Column(db.Integer, default=0)
    reward_max = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    reports = db.relationship('VulnerabilityReport', backref='program', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<Program {self.name!r} type={self.program_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'program_type': self.program_type,
            'reward_min': self.reward_min,
            'reward_max': self.reward_max,
            'is_active': self.is_active,
            'organization_id': self.organization_id
        }
