"""
VendorAssessment model - Phase 25 Cyber Resilience & Digital Enterprise.
Records results of third-party compliance, security audits, and risk recommendations.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class VendorAssessment(db.Model, TimestampMixin, TenantMixin):
    """Third Party Vendor Assessment detailed logs."""
    __tablename__ = 'vendor_assessments'

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('third_party_vendors.id', ondelete='CASCADE'), nullable=False)
    assessment_score = db.Column(db.Float, default=0.0, nullable=False) # 0.0 - 100.0
    compliance_score = db.Column(db.Float, default=0.0, nullable=False) # 0.0 - 100.0
    recommendations = db.Column(db.Text, nullable=True)

    # Relationship
    vendor = db.relationship('ThirdPartyVendor', backref=db.backref('assessments', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<VendorAssessment vendor_id={self.vendor_id} score={self.assessment_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'vendor_id': self.vendor_id,
            'assessment_score': self.assessment_score,
            'compliance_score': self.compliance_score,
            'recommendations': self.recommendations,
            'organization_id': self.organization_id
        }
