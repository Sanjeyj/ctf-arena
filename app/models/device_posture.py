"""
DevicePosture model - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Stores simulated device security posture.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class DevicePosture(db.Model, TimestampMixin, TenantMixin):
    """DevicePosture model."""
    __tablename__ = 'device_postures'

    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(120), nullable=False)
    device_type = db.Column(db.String(64), nullable=False)  # laptop, workstation, mobile, server
    os_family = db.Column(db.String(64), nullable=False)  # windows, macos, linux, ios, android
    patch_score = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0
    encryption_enabled = db.Column(db.Boolean, default=True, nullable=False)
    endpoint_protection_status = db.Column(db.String(64), default='active', nullable=False)  # active, inactive, not_installed
    posture_score = db.Column(db.Float, default=100.0, nullable=False)  # 0 to 100
    compliance_status = db.Column(db.String(64), default='compliant', nullable=False)  # compliant, non_compliant, restricted
    last_assessed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<DevicePosture name={self.device_name!r} score={self.posture_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'os_family': self.os_family,
            'patch_score': self.patch_score,
            'encryption_enabled': self.encryption_enabled,
            'endpoint_protection_status': self.endpoint_protection_status,
            'posture_score': self.posture_score,
            'compliance_status': self.compliance_status,
            'last_assessed_at': self.last_assessed_at.isoformat() if self.last_assessed_at else None,
            'organization_id': self.organization_id,
        }
