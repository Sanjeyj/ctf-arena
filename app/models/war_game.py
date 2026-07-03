"""
WarGame model - Phase 29 Global Cyber Command Center.
Represents a strategic cyber war-game scenario with participants and score.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class WarGame(db.Model, TimestampMixin, TenantMixin):
    """War game model."""
    __tablename__ = 'war_games'

    id = db.Column(db.Integer, primary_key=True)
    scenario = db.Column(db.String(180), nullable=False)
    participants = db.Column(db.Integer, default=2, nullable=False)
    score = db.Column(db.Float, default=0.0, nullable=False)
    result = db.Column(db.String(64), default='pending', nullable=False)  # pending, blue_win, red_win, draw

    def __repr__(self):
        return f'<WarGame scenario={self.scenario!r} result={self.result}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scenario': self.scenario,
            'participants': self.participants,
            'score': self.score,
            'result': self.result,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
