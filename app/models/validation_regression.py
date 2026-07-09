"""
ValidationRegression model - Phase 35 Continuous Security Validation.
Tracks detected drops in validation scores compared to historical baselines.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class ValidationRegression(db.Model, TimestampMixin, TenantMixin):
    """ValidationRegression representation."""
    __tablename__ = 'validation_regressions'

    id = db.Column(db.Integer, primary_key=True)
    resource_type = db.Column(db.String(64), nullable=False)
    resource_id = db.Column(db.Integer, nullable=False)
    metric_type = db.Column(db.String(64), nullable=False)
    previous_score = db.Column(db.Float, default=100.0, nullable=False)
    current_score = db.Column(db.Float, default=100.0, nullable=False)
    regression_delta = db.Column(db.Float, default=0.0, nullable=False)
    severity = db.Column(db.String(32), default='medium', nullable=False)  # low, medium, high, critical
    status = db.Column(db.String(32), default='open', nullable=False)  # open, investigating, accepted, resolved
    detected_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<ValidationRegression resource={self.resource_type}:{self.resource_id} delta={self.regression_delta} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'metric_type': self.metric_type,
            'previous_score': self.previous_score,
            'current_score': self.current_score,
            'regression_delta': self.regression_delta,
            'severity': self.severity,
            'status': self.status,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'organization_id': self.organization_id
        }
