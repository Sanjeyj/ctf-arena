"""
ValidationExecution model - Phase 35 Continuous Security Validation.
Tracks validation simulation run execution histories and scores.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class ValidationExecution(db.Model, TimestampMixin, TenantMixin):
    """ValidationExecution representation."""
    __tablename__ = 'validation_executions'

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('validation_campaigns.id', ondelete='CASCADE'), nullable=False)
    scenario_id = db.Column(db.Integer, db.ForeignKey('validation_scenarios.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(32), default='running', nullable=False)  # running, completed, failed
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    baseline_score = db.Column(db.Float, default=0.0, nullable=False)
    result_score = db.Column(db.Float, default=0.0, nullable=False)
    effectiveness_score = db.Column(db.Float, default=0.0, nullable=False)  # normalized 0.0 - 1.0
    result_summary = db.Column(db.Text, nullable=True)

    campaign = db.relationship('ValidationCampaign', backref=db.backref('executions', lazy='dynamic'))
    scenario = db.relationship('ValidationScenario', backref=db.backref('executions', lazy='dynamic'))

    def __repr__(self):
        return f'<ValidationExecution ID={self.id} status={self.status} eff={self.effectiveness_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'scenario_id': self.scenario_id,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'baseline_score': self.baseline_score,
            'result_score': self.result_score,
            'effectiveness_score': self.effectiveness_score,
            'result_summary': self.result_summary,
            'organization_id': self.organization_id
        }
