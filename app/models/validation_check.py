"""
ValidationCheck model - Phase 35 Continuous Security Validation.
Logs granular check assertions executed in a simulation step.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ValidationCheck(db.Model, TimestampMixin, TenantMixin):
    """ValidationCheck representation."""
    __tablename__ = 'validation_checks'

    id = db.Column(db.Integer, primary_key=True)
    execution_id = db.Column(db.Integer, db.ForeignKey('validation_executions.id', ondelete='CASCADE'), nullable=False)
    check_type = db.Column(db.String(64), nullable=False)  # control, detection, playbook, architecture, resilience, remediation
    target_reference_type = db.Column(db.String(64), nullable=False)  # e.g., 'compliance_control'
    target_reference_id = db.Column(db.Integer, nullable=False)
    expected_result = db.Column(db.String(120), nullable=False)
    actual_result = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Float, default=100.0, nullable=False)
    status = db.Column(db.String(32), default='passed', nullable=False)  # passed, failed
    evidence_record_id = db.Column(db.Integer, db.ForeignKey('evidence_records.id', ondelete='SET NULL'), nullable=True)

    execution = db.relationship('ValidationExecution', backref=db.backref('checks', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<ValidationCheck type={self.check_type} target={self.target_reference_type}:{self.target_reference_id} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'check_type': self.check_type,
            'target_reference_type': self.target_reference_type,
            'target_reference_id': self.target_reference_id,
            'expected_result': self.expected_result,
            'actual_result': self.actual_result,
            'score': self.score,
            'status': self.status,
            'evidence_record_id': self.evidence_record_id,
            'organization_id': self.organization_id
        }
