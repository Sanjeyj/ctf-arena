"""
ControlCoverageMap model - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class ControlCoverageMap(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'control_coverage_maps'

    id = db.Column(db.Integer, primary_key=True)
    control_reference = db.Column(db.String(255), nullable=False, index=True)  # maps to compliance_controls.control_reference
    resource_type = db.Column(db.String(100), nullable=False)  # asset, zone, platform_service
    resource_id = db.Column(db.Integer, nullable=False)
    coverage_score = db.Column(db.Float, nullable=False, default=0.0)
    effectiveness_score = db.Column(db.Float, nullable=False, default=0.0)
    validation_status = db.Column(db.String(50), nullable=False, default='unvalidated')
    last_validated_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
