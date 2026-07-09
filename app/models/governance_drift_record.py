import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class GovernanceDriftRecord(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'governance_drift_records'

    id = db.Column(db.Integer, primary_key=True)
    resource_type = db.Column(db.String(128), nullable=False)
    resource_id = db.Column(db.Integer, nullable=True)
    drift_type = db.Column(db.String(64), nullable=False)  # risk_appetite, policy_effectiveness, control_coverage, decision_quality, objective_progress, evidence_quality, resilience_alignment
    baseline_value = db.Column(db.Float, default=0.0)
    current_value = db.Column(db.Float, default=0.0)
    drift_delta = db.Column(db.Float, default=0.0)
    severity = db.Column(db.String(32), default='low')
    recommended_action = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='detected')
    detected_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'drift_type': self.drift_type,
            'baseline_value': self.baseline_value,
            'current_value': self.current_value,
            'drift_delta': self.drift_delta,
            'severity': self.severity,
            'recommended_action': self.recommended_action,
            'status': self.status,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'organization_id': self.organization_id
        }
