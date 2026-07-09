"""
ValidationCampaign model - Phase 35 Continuous Security Validation.
Tracks security validation campaign definitions and overall lifecycle status.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class ValidationCampaign(db.Model, TimestampMixin, TenantMixin):
    """ValidationCampaign representation."""
    __tablename__ = 'validation_campaigns'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    campaign_type = db.Column(db.String(64), nullable=False)  # control_validation, detection_validation, etc.
    scope = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(32), default='draft', nullable=False)  # draft, scheduled, running, completed, failed, cancelled
    priority = db.Column(db.String(32), default='medium', nullable=False)  # low, medium, high
    scheduled_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<ValidationCampaign {self.name!r} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'campaign_type': self.campaign_type,
            'scope': self.scope,
            'status': self.status,
            'priority': self.priority,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'organization_id': self.organization_id
        }
