"""
CrisisEvent model - Phase 25 Cyber Resilience & Digital Enterprise.
Registers major crisis events, severity levels, timeline parameters, and computed impact scores.
"""
from app.extensions import db, utcnow
from app.models.mixins import TimestampMixin, TenantMixin

class CrisisEvent(db.Model, TimestampMixin, TenantMixin):
    """Crisis Event tracking log."""
    __tablename__ = 'crisis_events'

    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    severity = db.Column(db.String(32), default='medium', nullable=False) # low, medium, high, critical
    start_time = db.Column(db.DateTime, default=utcnow, nullable=False)
    status = db.Column(db.String(32), default='active', nullable=False) # active, resolved
    impact_score = db.Column(db.Float, default=0.0, nullable=False) # 0.0 - 100.0

    def __repr__(self):
        return f'<CrisisEvent {self.event_name!r} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'event_name': self.event_name,
            'severity': self.severity,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'status': self.status,
            'impact_score': self.impact_score,
            'organization_id': self.organization_id
        }
