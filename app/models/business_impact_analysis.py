"""
BusinessImpactAnalysis model - Phase 25 Cyber Resilience & Digital Enterprise.
Tracks Business Impact Analysis (BIA) assessments mapping processes to impact domains.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class BusinessImpactAnalysis(db.Model, TimestampMixin, TenantMixin):
    """Business Impact Analysis record."""
    __tablename__ = 'business_impact_analyses'

    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey('business_processes.id', ondelete='CASCADE'), nullable=False)
    financial_impact = db.Column(db.Integer, default=3, nullable=False) # 1-5 scale
    operational_impact = db.Column(db.Integer, default=3, nullable=False) # 1-5 scale
    reputation_impact = db.Column(db.Integer, default=3, nullable=False) # 1-5 scale
    recovery_priority = db.Column(db.String(32), default='medium', nullable=False) # low, medium, high, critical

    # Relationship
    process = db.relationship('BusinessProcess', backref=db.backref('bias', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<BusinessImpactAnalysis process_id={self.process_id} priority={self.recovery_priority}>'

    def to_dict(self):
        return {
            'id': self.id,
            'process_id': self.process_id,
            'financial_impact': self.financial_impact,
            'operational_impact': self.operational_impact,
            'reputation_impact': self.reputation_impact,
            'recovery_priority': self.recovery_priority,
            'organization_id': self.organization_id
        }
