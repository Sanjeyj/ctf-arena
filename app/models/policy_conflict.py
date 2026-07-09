import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class PolicyConflict(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'policy_conflicts'

    id = db.Column(db.Integer, primary_key=True)
    source_policy_id = db.Column(db.Integer, db.ForeignKey('control_policies.id', ondelete='CASCADE'), nullable=False)
    target_policy_id = db.Column(db.Integer, db.ForeignKey('control_policies.id', ondelete='CASCADE'), nullable=False)
    conflict_type = db.Column(db.String(64), nullable=False)  # contradiction, overlap, coverage_gap, priority_conflict, scope_conflict, enforcement_conflict
    severity = db.Column(db.String(32), default='medium')
    description = db.Column(db.Text, nullable=True)
    confidence_score = db.Column(db.Float, default=0.0)
    resolution_recommendation = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='open')  # open, reviewing, accepted, resolved, false_positive
    detected_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationships
    source_policy = db.relationship('ControlPolicy', foreign_keys=[source_policy_id], backref=db.backref('conflicts_as_source', cascade='all, delete-orphan', lazy='dynamic'))
    target_policy = db.relationship('ControlPolicy', foreign_keys=[target_policy_id], backref=db.backref('conflicts_as_target', cascade='all, delete-orphan', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'source_policy_id': self.source_policy_id,
            'target_policy_id': self.target_policy_id,
            'conflict_type': self.conflict_type,
            'severity': self.severity,
            'description': self.description,
            'confidence_score': self.confidence_score,
            'resolution_recommendation': self.resolution_recommendation,
            'status': self.status,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'organization_id': self.organization_id
        }
