"""
ThirdPartyVendor model - Phase 25 Cyber Resilience & Digital Enterprise.
Registers third-party vendor names, supply chain dependencies, and risk ratings.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class ThirdPartyVendor(db.Model, TimestampMixin, TenantMixin):
    """Third Party Vendor profiles database table."""
    __tablename__ = 'third_party_vendors'

    id = db.Column(db.Integer, primary_key=True)
    vendor_name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    service_type = db.Column(db.String(120), nullable=True) # e.g. SaaS, cloud, hardware
    risk_score = db.Column(db.Float, default=0.0, nullable=False) # 0.0 - 100.0
    contract_status = db.Column(db.String(32), default='active', nullable=False) # active, expired, under_review

    def __repr__(self):
        return f'<ThirdPartyVendor {self.vendor_name!r} risk={self.risk_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'vendor_name': self.vendor_name,
            'service_type': self.service_type,
            'risk_score': self.risk_score,
            'contract_status': self.contract_status,
            'organization_id': self.organization_id
        }
