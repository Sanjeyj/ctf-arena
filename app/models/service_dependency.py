"""
ServiceDependency model - Phase 31 Cyber Platform Control Plane.
Maps logical service dependencies.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ServiceDependency(db.Model, TimestampMixin, TenantMixin):
    """ServiceDependency model."""
    __tablename__ = 'service_dependencies'

    id = db.Column(db.Integer, primary_key=True)
    source_service_id = db.Column(db.Integer, db.ForeignKey('platform_services.id', ondelete='CASCADE'), nullable=False, index=True)
    target_service_id = db.Column(db.Integer, db.ForeignKey('platform_services.id', ondelete='CASCADE'), nullable=False, index=True)
    dependency_type = db.Column(db.String(64), default='data', nullable=False)  # data, authentication, analytics, ai, workflow, storage
    criticality = db.Column(db.String(32), default='medium', nullable=False)  # low, medium, high, critical
    health_impact = db.Column(db.Float, default=0.5, nullable=False)
    status = db.Column(db.String(32), default='active', nullable=False)

    def __repr__(self):
        return f'<ServiceDependency {self.source_service_id}->{self.target_service_id} type={self.dependency_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'source_service_id': self.source_service_id,
            'target_service_id': self.target_service_id,
            'dependency_type': self.dependency_type,
            'criticality': self.criticality,
            'health_impact': self.health_impact,
            'status': self.status,
            'organization_id': self.organization_id,
        }
