"""
RiskAppetiteProfile model - Phase 36 Cyber Risk Quantification.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class RiskAppetiteProfile(db.Model, TimestampMixin, TenantMixin):
    """RiskAppetiteProfile representation."""
    __tablename__ = 'risk_appetite_profiles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    maximum_annualized_loss = db.Column(db.Float, default=1000000.0, nullable=False)
    maximum_single_event_loss = db.Column(db.Float, default=250000.0, nullable=False)
    maximum_residual_risk_score = db.Column(db.Float, default=50.0, nullable=False)
    critical_scenario_tolerance = db.Column(db.Integer, default=3, nullable=False)
    status = db.Column(db.String(32), default='draft', nullable=False)  # draft, active, retired
    approved_by = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f'<RiskAppetiteProfile {self.name!r} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'maximum_annualized_loss': self.maximum_annualized_loss,
            'maximum_single_event_loss': self.maximum_single_event_loss,
            'maximum_residual_risk_score': self.maximum_residual_risk_score,
            'critical_scenario_tolerance': self.critical_scenario_tolerance,
            'status': self.status,
            'approved_by': self.approved_by,
            'organization_id': self.organization_id
        }
