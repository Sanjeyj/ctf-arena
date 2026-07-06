"""
TrustBoundary model - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class TrustBoundary(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'trust_boundaries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    source_zone_id = db.Column(db.Integer, db.ForeignKey('architecture_zones.id', name='fk_trust_boundaries_source_zone_id'), nullable=False)
    target_zone_id = db.Column(db.Integer, db.ForeignKey('architecture_zones.id', name='fk_trust_boundaries_target_zone_id'), nullable=False)
    boundary_type = db.Column(db.String(100), nullable=False, default='network')
    required_trust_score = db.Column(db.Float, nullable=False, default=0.5)
    control_requirements_json = db.Column(db.Text, nullable=True, default='[]')
    status = db.Column(db.String(50), nullable=False, default='active')
