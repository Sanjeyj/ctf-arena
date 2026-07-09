import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class GovernanceScorecard(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'governance_scorecards'

    id = db.Column(db.Integer, primary_key=True)
    scorecard_type = db.Column(db.String(64), nullable=False, default='overall')
    overall_score = db.Column(db.Float, default=0.0)
    risk_alignment_score = db.Column(db.Float, default=0.0)
    policy_effectiveness_score = db.Column(db.Float, default=0.0)
    evidence_quality_score = db.Column(db.Float, default=0.0)
    decision_quality_score = db.Column(db.Float, default=0.0)
    objective_progress_score = db.Column(db.Float, default=0.0)
    measured_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'scorecard_type': self.scorecard_type,
            'overall_score': self.overall_score,
            'risk_alignment_score': self.risk_alignment_score,
            'policy_effectiveness_score': self.policy_effectiveness_score,
            'evidence_quality_score': self.evidence_quality_score,
            'decision_quality_score': self.decision_quality_score,
            'objective_progress_score': self.objective_progress_score,
            'measured_at': self.measured_at.isoformat() if self.measured_at else None,
            'organization_id': self.organization_id
        }
