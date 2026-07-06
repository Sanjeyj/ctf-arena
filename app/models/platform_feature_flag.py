"""
PlatformFeatureFlag model - Phase 31 Cyber Platform Control Plane.
Tenant-aware feature rollout configuration.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class PlatformFeatureFlag(db.Model, TimestampMixin, TenantMixin):
    """PlatformFeatureFlag model."""
    __tablename__ = 'platform_feature_flags'

    id = db.Column(db.Integer, primary_key=True)
    flag_key = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    enabled = db.Column(db.Boolean, default=False, nullable=False)
    rollout_percentage = db.Column(db.Integer, default=100, nullable=False)
    environment = db.Column(db.String(32), default='production', nullable=False)
    conditions_json = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<PlatformFeatureFlag key={self.flag_key!r} enabled={self.enabled}>'

    def to_dict(self):
        conds = {}
        if self.conditions_json:
            try:
                conds = json.loads(self.conditions_json)
            except Exception:
                pass
        return {
            'id': self.id,
            'flag_key': self.flag_key,
            'description': self.description,
            'enabled': self.enabled,
            'rollout_percentage': self.rollout_percentage,
            'environment': self.environment,
            'conditions': conds,
            'organization_id': self.organization_id,
        }
