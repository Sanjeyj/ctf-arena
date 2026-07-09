"""
PlaybookReadiness model - Phase 35 Continuous Security Validation.
Tracks incident response playbook maturity, approvals, and dependencies.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class PlaybookReadiness(db.Model, TimestampMixin, TenantMixin):
    """PlaybookReadiness representation."""
    __tablename__ = 'playbook_readiness'

    id = db.Column(db.Integer, primary_key=True)
    playbook_id = db.Column(db.Integer, nullable=False)
    execution_id = db.Column(db.Integer, db.ForeignKey('validation_executions.id', ondelete='CASCADE'), nullable=False)
    step_coverage_score = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0
    dependency_score = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0
    approval_score = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0
    evidence_score = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0
    readiness_score = db.Column(db.Float, default=1.0, nullable=False)  # composite 0.0 to 1.0
    status = db.Column(db.String(32), default='ready', nullable=False)  # ready, draft, obsolete

    execution = db.relationship('ValidationExecution', backref=db.backref('playbook_readiness', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<PlaybookReadiness playbook={self.playbook_id} score={self.readiness_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'playbook_id': self.playbook_id,
            'execution_id': self.execution_id,
            'step_coverage_score': self.step_coverage_score,
            'dependency_score': self.dependency_score,
            'approval_score': self.approval_score,
            'evidence_score': self.evidence_score,
            'readiness_score': self.readiness_score,
            'status': self.status,
            'organization_id': self.organization_id
        }
