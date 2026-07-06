"""
UniverseEvent model - Phase 30 Unified Cyber Defense Universe.
Stores chronological simulation events.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class UniverseEvent(db.Model, TimestampMixin, TenantMixin):
    """Universe event model."""
    __tablename__ = 'universe_events'

    id = db.Column(db.Integer, primary_key=True)
    simulation_id = db.Column(db.Integer, db.ForeignKey('universe_simulations.id', ondelete='CASCADE'), nullable=False, index=True)
    event_type = db.Column(db.String(64), nullable=False)
    domain = db.Column(db.String(64), nullable=True)
    severity = db.Column(db.String(32), default='info', nullable=False)  # info, low, medium, high, critical
    description = db.Column(db.Text, nullable=False)
    score_delta = db.Column(db.Float, default=0.0, nullable=False)
    event_time = db.Column(db.DateTime, nullable=False, index=True)
    metadata_json = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<UniverseEvent type={self.event_type} simulation={self.simulation_id}>'

    def to_dict(self):
        meta = {}
        if self.metadata_json:
            try:
                meta = json.loads(self.metadata_json)
            except Exception:
                pass
        return {
            'id': self.id,
            'simulation_id': self.simulation_id,
            'event_type': self.event_type,
            'domain': self.domain,
            'severity': self.severity,
            'description': self.description,
            'score_delta': self.score_delta,
            'event_time': self.event_time.isoformat() if self.event_time else None,
            'metadata': meta,
            'organization_id': self.organization_id,
        }
