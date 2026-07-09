"""
BusinessDependencyRisk model - Phase 37 Strategic Cyber Resilience.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class BusinessDependencyRisk(db.Model, TimestampMixin, TenantMixin):
    """BusinessDependencyRisk representation."""
    __tablename__ = 'business_dependency_risks'

    id = db.Column(db.Integer, primary_key=True)
    business_process_id = db.Column(db.Integer, db.ForeignKey('business_processes.id', ondelete='CASCADE'), nullable=False)
    dependency_reference_type = db.Column(db.String(64), nullable=False)  # third_party_vendors, platform_services, cloud_regions, etc.
    dependency_reference_id = db.Column(db.Integer, nullable=False)
    dependency_type = db.Column(db.String(64), nullable=False)  # service, vendor, cloud_region, application, identity, network_simulation, data, security_control
    criticality_score = db.Column(db.Float, default=50.0, nullable=False)
    concentration_risk_score = db.Column(db.Float, default=0.0, nullable=False)
    failure_impact_score = db.Column(db.Float, default=0.0, nullable=False)
    recovery_dependency_score = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.String(32), default='active', nullable=False)

    business_process = db.relationship('BusinessProcess', backref=db.backref('dependencies', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<BusinessDependencyRisk process_id={self.business_process_id} type={self.dependency_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'business_process_id': self.business_process_id,
            'dependency_reference_type': self.dependency_reference_type,
            'dependency_reference_id': self.dependency_reference_id,
            'dependency_type': self.dependency_type,
            'criticality_score': self.criticality_score,
            'concentration_risk_score': self.concentration_risk_score,
            'failure_impact_score': self.failure_impact_score,
            'recovery_dependency_score': self.recovery_dependency_score,
            'status': self.status,
            'organization_id': self.organization_id
        }
