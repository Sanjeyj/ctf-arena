"""
AuditFinding model - Phase 23 Governance & Compliance.
Logs findings identified during compliance gap analyses.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class AuditFinding(db.Model, TimestampMixin, TenantMixin):
    """Compliance audit deficiency record."""
    __tablename__ = 'audit_findings'

    id = db.Column(db.Integer, primary_key=True)
    control_id = db.Column(db.Integer, db.ForeignKey('compliance_controls.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(32), default='medium') # low, medium, high, critical
    status = db.Column(db.String(32), default='open') # open, closed

    # Relationships
    control = db.relationship('ComplianceControl', backref=db.backref('findings', cascade='all, delete-orphan', lazy='dynamic'))

    def __repr__(self):
        return f'<AuditFinding {self.title!r} severity={self.severity} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'control_id': self.control_id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'status': self.status
        }
