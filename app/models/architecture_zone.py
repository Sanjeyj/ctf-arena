"""
ArchitectureZone model - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ArchitectureZone(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'architecture_zones'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    zone_type = db.Column(db.String(50), nullable=False, default='application')  # public, edge, application, data, management, security, development, restricted
    description = db.Column(db.Text, nullable=True)
    trust_level = db.Column(db.Float, nullable=False, default=1.0)
    criticality = db.Column(db.String(50), nullable=False, default='medium')
    status = db.Column(db.String(50), nullable=False, default='active')

    # Relationships
    boundaries_as_source = db.relationship('TrustBoundary', foreign_keys='TrustBoundary.source_zone_id', backref='source_zone', lazy=True, cascade='all, delete-orphan')
    boundaries_as_target = db.relationship('TrustBoundary', foreign_keys='TrustBoundary.target_zone_id', backref='target_zone', lazy=True, cascade='all, delete-orphan')
    exposure_assets = db.relationship('ExposureAsset', backref='architecture_zone', lazy=True)
