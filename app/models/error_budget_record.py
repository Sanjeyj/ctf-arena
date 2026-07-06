"""
ErrorBudgetRecord model - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Tracks consumption and burn rate of SLO error budgets.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ErrorBudgetRecord(db.Model, TimestampMixin, TenantMixin):
    """ErrorBudgetRecord model."""
    __tablename__ = 'error_budget_records'

    id = db.Column(db.Integer, primary_key=True)
    reliability_objective_id = db.Column(db.Integer, db.ForeignKey('reliability_objectives.id', ondelete='CASCADE'), nullable=False)
    budget_total = db.Column(db.Float, default=1.0, nullable=False)
    budget_consumed = db.Column(db.Float, default=0.0, nullable=False)
    budget_remaining = db.Column(db.Float, default=1.0, nullable=False)
    burn_rate = db.Column(db.Float, default=1.0, nullable=False)  # 1.0 = normal consumption
    window_start = db.Column(db.DateTime, nullable=False)
    window_end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(32), default='within_budget', nullable=False)  # within_budget, warning, exhausted

    def __repr__(self):
        return f'<ErrorBudgetRecord objective_id={self.reliability_objective_id} status={self.status} remaining={self.budget_remaining}>'

    def to_dict(self):
        return {
            'id': self.id,
            'reliability_objective_id': self.reliability_objective_id,
            'budget_total': self.budget_total,
            'budget_consumed': self.budget_consumed,
            'budget_remaining': self.budget_remaining,
            'burn_rate': self.burn_rate,
            'window_start': self.window_start.isoformat() if self.window_start else None,
            'window_end': self.window_end.isoformat() if self.window_end else None,
            'status': self.status,
            'organization_id': self.organization_id,
        }
