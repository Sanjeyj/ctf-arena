"""
ComplianceControl model - Phase 23 Governance & Compliance.
Tracks individual controls evaluations and scoring states.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class ComplianceControl(db.Model, TimestampMixin, TenantMixin):
    """Compliance control evaluation indicator."""
    __tablename__ = 'compliance_controls'

    id = db.Column(db.Integer, primary_key=True)
    framework_id = db.Column(db.Integer, db.ForeignKey('governance_frameworks.id', ondelete='CASCADE'), nullable=False)
    control_code = db.Column(db.String(64), nullable=False, index=True) # e.g. A.12.6.1
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='failed') # passed, failed, partial, not_applicable

    # Relationships
    framework = db.relationship('GovernanceFramework', backref=db.backref('controls', cascade='all, delete-orphan', lazy='dynamic'))

    def __repr__(self):
        return f'<ComplianceControl code={self.control_code} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'framework_id': self.framework_id,
            'control_code': self.control_code,
            'description': self.description,
            'status': self.status
        }
