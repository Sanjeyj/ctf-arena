"""Phase 40 — Platform Readiness Metric Model."""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class PlatformReadinessMetric(db.Model, TimestampMixin, TenantMixin):
    """Periodic composite readiness snapshot across all platform capability domains.

    Readiness Index Weights (total = 100%):
      Security:     20%
      Reliability:  15%
      Governance:   15%
      Resilience:   20%
      Assurance:    15%
      Operations:   15%
    """
    __tablename__ = 'platform_readiness_metrics'

    METRIC_TYPES = ('scheduled', 'on_demand', 'pre_release', 'post_incident')

    # Documented weights — must sum to 1.0
    WEIGHT_SECURITY = 0.20
    WEIGHT_RELIABILITY = 0.15
    WEIGHT_GOVERNANCE = 0.15
    WEIGHT_RESILIENCE = 0.20
    WEIGHT_ASSURANCE = 0.15
    WEIGHT_OPERATIONS = 0.15

    id = db.Column(db.Integer, primary_key=True)
    metric_type = db.Column(db.String(40), nullable=False, default='on_demand', index=True)
    security_score = db.Column(db.Float, nullable=False, default=0.0)
    reliability_score = db.Column(db.Float, nullable=False, default=0.0)
    governance_score = db.Column(db.Float, nullable=False, default=0.0)
    resilience_score = db.Column(db.Float, nullable=False, default=0.0)
    assurance_score = db.Column(db.Float, nullable=False, default=0.0)
    operations_score = db.Column(db.Float, nullable=False, default=0.0)
    overall_readiness_score = db.Column(db.Float, nullable=False, default=0.0)
    measured_at = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'metric_type': self.metric_type,
            'security_score': round(float(self.security_score), 4),
            'reliability_score': round(float(self.reliability_score), 4),
            'governance_score': round(float(self.governance_score), 4),
            'resilience_score': round(float(self.resilience_score), 4),
            'assurance_score': round(float(self.assurance_score), 4),
            'operations_score': round(float(self.operations_score), 4),
            'overall_readiness_score': round(float(self.overall_readiness_score), 4),
            'measured_at': self.measured_at.isoformat() if self.measured_at else None,
            'notes': self.notes,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
