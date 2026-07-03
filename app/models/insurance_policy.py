"""
InsurancePolicy model - Phase 25 Cyber Resilience & Digital Enterprise.
Stores cyber risk transfer policies, coverage levels, deductibles, and renewals.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class InsurancePolicy(db.Model, TimestampMixin, TenantMixin):
    """Cyber Insurance Policy database record."""
    __tablename__ = 'insurance_policies'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(120), nullable=False, index=True)
    coverage = db.Column(db.Float, default=0.0, nullable=False) # Total financial coverage (USD)
    deductible = db.Column(db.Float, default=0.0, nullable=False) # Policy deductible (USD)
    renewal_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<InsurancePolicy provider={self.provider!r} coverage={self.coverage}>'

    def to_dict(self):
        return {
            'id': self.id,
            'provider': self.provider,
            'coverage': self.coverage,
            'deductible': self.deductible,
            'renewal_date': self.renewal_date.isoformat() if self.renewal_date else None,
            'organization_id': self.organization_id
        }
