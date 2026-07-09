import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class DecisionOutcome(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'decision_outcomes'

    id = db.Column(db.Integer, primary_key=True)
    recommendation_id = db.Column(db.Integer, db.ForeignKey('decision_recommendations.id', ondelete='CASCADE'), nullable=False)
    decision_record_id = db.Column(db.Integer, db.ForeignKey('strategic_decision_records.id', ondelete='CASCADE'), nullable=False)
    baseline_metric = db.Column(db.Float, default=0.0)
    result_metric = db.Column(db.Float, default=0.0)
    improvement_delta = db.Column(db.Float, default=0.0)
    expected_improvement = db.Column(db.Float, default=0.0)
    variance = db.Column(db.Float, default=0.0)
    outcome_status = db.Column(db.String(32), default='pending')  # pending, effective, partially_effective, ineffective, regressed, requires_review
    review_notes = db.Column(db.Text, nullable=True)
    measured_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationships
    recommendation = db.relationship('DecisionRecommendation', backref=db.backref('outcomes', cascade='all, delete-orphan', lazy='dynamic'))
    decision_record = db.relationship('StrategicDecisionRecord', backref=db.backref('outcomes', cascade='all, delete-orphan', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'recommendation_id': self.recommendation_id,
            'decision_record_id': self.decision_record_id,
            'baseline_metric': self.baseline_metric,
            'result_metric': self.result_metric,
            'improvement_delta': self.improvement_delta,
            'expected_improvement': self.expected_improvement,
            'variance': self.variance,
            'outcome_status': self.outcome_status,
            'review_notes': self.review_notes,
            'measured_at': self.measured_at.isoformat() if self.measured_at else None,
            'organization_id': self.organization_id
        }
