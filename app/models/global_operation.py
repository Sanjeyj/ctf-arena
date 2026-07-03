"""
GlobalOperation model - Phase 29 Global Cyber Command Center.
Represents a global cyber operation with type, severity, status, and time bounds.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class GlobalOperation(db.Model, TimestampMixin, TenantMixin):
    """Global cyber operation model."""
    __tablename__ = 'global_operations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    operation_type = db.Column(db.String(64), nullable=False)  # offensive, defensive, intelligence
    severity = db.Column(db.String(32), default='medium', nullable=False)  # low, medium, high, critical
    status = db.Column(db.String(32), default='planned', nullable=False)  # planned, active, complete, aborted
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<GlobalOperation {self.name!r} type={self.operation_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'operation_type': self.operation_type,
            'severity': self.severity,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
