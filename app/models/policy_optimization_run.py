import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class PolicyOptimizationRun(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'policy_optimization_runs'

    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey('control_policies.id', ondelete='CASCADE'), nullable=False)
    optimization_type = db.Column(db.String(64), nullable=False)  # threshold_tuning, coverage_improvement, conflict_reduction, risk_alignment, control_effectiveness, simulation
    baseline_score = db.Column(db.Float, default=0.0)
    optimized_score = db.Column(db.Float, default=0.0)
    risk_before = db.Column(db.Float, default=0.0)
    risk_after = db.Column(db.Float, default=0.0)
    constraint_count = db.Column(db.Integer, default=0)
    recommendation_json = db.Column(db.Text, nullable=True)
    random_seed = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(32), default='completed')
    started_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    completed_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationship
    policy = db.relationship('ControlPolicy', backref=db.backref('optimization_runs', cascade='all, delete-orphan', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'policy_id': self.policy_id,
            'optimization_type': self.optimization_type,
            'baseline_score': self.baseline_score,
            'optimized_score': self.optimized_score,
            'risk_before': self.risk_before,
            'risk_after': self.risk_after,
            'constraint_count': self.constraint_count,
            'recommendation_json': self.recommendation_json,
            'random_seed': self.random_seed,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'organization_id': self.organization_id
        }
