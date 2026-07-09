from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class DecisionRecommendation(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'decision_recommendations'

    id = db.Column(db.Integer, primary_key=True)
    decision_context_id = db.Column(db.Integer, db.ForeignKey('decision_contexts.id', ondelete='CASCADE'), nullable=False)
    recommendation_type = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    expected_risk_reduction = db.Column(db.Float, default=0.0)
    expected_resilience_gain = db.Column(db.Float, default=0.0)
    expected_control_improvement = db.Column(db.Float, default=0.0)
    estimated_cost = db.Column(db.Float, default=0.0)
    confidence_score = db.Column(db.Float, default=0.0)
    priority_score = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32), default='generated')  # generated, reviewing, accepted, rejected, superseded

    # Relationship
    decision_context = db.relationship('DecisionContext', backref=db.backref('recommendations', cascade='all, delete-orphan', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'decision_context_id': self.decision_context_id,
            'recommendation_type': self.recommendation_type,
            'title': self.title,
            'description': self.description,
            'expected_risk_reduction': self.expected_risk_reduction,
            'expected_resilience_gain': self.expected_resilience_gain,
            'expected_control_improvement': self.expected_control_improvement,
            'estimated_cost': self.estimated_cost,
            'confidence_score': self.confidence_score,
            'priority_score': self.priority_score,
            'status': self.status,
            'organization_id': self.organization_id
        }
