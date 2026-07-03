"""
RiskRegister model - Phase 23 GRC.
Registers threat scenarios, likelihood estimates, impact assessments and mitigation plans.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class RiskRegister(db.Model, TimestampMixin, TenantMixin):
    """GRC Risk Register entry."""
    __tablename__ = 'risk_registers'

    id = db.Column(db.Integer, primary_key=True)
    scenario = db.Column(db.String(256), nullable=False, unique=True)
    impact = db.Column(db.Integer, default=3) # 1-5 scale
    likelihood = db.Column(db.Integer, default=3) # 1-5 scale
    risk_score = db.Column(db.Integer, default=9) # impact * likelihood
    mitigation_plan = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<RiskRegister {self.scenario!r} score={self.risk_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scenario': self.scenario,
            'impact': self.impact,
            'likelihood': self.likelihood,
            'risk_score': self.risk_score,
            'mitigation_plan': self.mitigation_plan
        }
