"""
ExposureAsset model - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ExposureAsset(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'exposure_assets'

    id = db.Column(db.Integer, primary_key=True)
    asset_reference_type = db.Column(db.String(100), nullable=False)  # asset, universe_node, cloud_node, platform_service
    asset_reference_id = db.Column(db.Integer, nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    exposure_type = db.Column(db.String(100), nullable=False, default='internal')  # internal, perimeter, external, data_exfil
    internet_exposed = db.Column(db.Boolean, nullable=False, default=False)
    criticality = db.Column(db.String(50), nullable=False, default='medium')
    business_impact_score = db.Column(db.Float, nullable=False, default=5.0)
    architecture_zone_id = db.Column(db.Integer, db.ForeignKey('architecture_zones.id', name='fk_exposure_assets_architecture_zone_id'), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='monitored')

    # Relationships
    findings = db.relationship('ExposureFinding', backref='exposure_asset', lazy=True, cascade='all, delete-orphan')
    attack_paths_as_source = db.relationship('AttackPath', foreign_keys='AttackPath.source_asset_id', backref='source_asset', lazy=True, cascade='all, delete-orphan')
    attack_paths_as_target = db.relationship('AttackPath', foreign_keys='AttackPath.target_asset_id', backref='target_asset', lazy=True, cascade='all, delete-orphan')
