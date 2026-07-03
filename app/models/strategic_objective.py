"""
StrategicObjective model - Phase 29 Global Cyber Command Center.
Represents a high-level strategic cyber objective with priority and progress.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class StrategicObjective(db.Model, TimestampMixin, TenantMixin):
    """Strategic objective model."""
    __tablename__ = 'strategic_objectives'

    id = db.Column(db.Integer, primary_key=True)
    objective = db.Column(db.String(255), nullable=False)
    priority = db.Column(db.Integer, default=3, nullable=False)  # 1=critical, 5=low
    progress = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 - 1.0
    status = db.Column(db.String(32), default='open', nullable=False)  # open, in_progress, achieved, cancelled

    def __repr__(self):
        return f'<StrategicObjective {self.objective[:40]!r} priority={self.priority}>'

    def to_dict(self):
        return {
            'id': self.id,
            'objective': self.objective,
            'priority': self.priority,
            'progress': self.progress,
            'status': self.status,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
