"""
DefenseAlliance model - Phase 28 Cyber Civilization Platform.
Tracks cyber nation defense alliances and security trust indices.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class DefenseAlliance(db.Model, TimestampMixin, TenantMixin):
    """Cyber nation defense alliance model."""
    __tablename__ = 'defense_alliances'

    id = db.Column(db.Integer, primary_key=True)
    alliance_name = db.Column(db.String(120), nullable=False)
    trust_score = db.Column(db.Float, default=0.5, nullable=False)  # 0.0 to 1.0
    members = db.Column(db.Text, nullable=True)  # comma-separated cyber nation names
    status = db.Column(db.String(32), default='active', nullable=False)  # active, disbanded, suspended

    def __repr__(self):
        return f'<DefenseAlliance {self.alliance_name!r} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'alliance_name': self.alliance_name,
            'trust_score': self.trust_score,
            'members': self.members,
            'status': self.status,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
