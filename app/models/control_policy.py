"""
ControlPolicy model - Phase 31 Cyber Platform Control Plane.
Platform governance and operational policy rules.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ControlPolicy(db.Model, TimestampMixin, TenantMixin):
    """ControlPolicy model."""
    __tablename__ = 'control_policies'

    id = db.Column(db.Integer, primary_key=True)
    policy_name = db.Column(db.String(120), nullable=False)
    policy_type = db.Column(db.String(64), nullable=False)  # soc, cti, cloud, overall
    rule_json = db.Column(db.Text, nullable=True)
    enforcement_mode = db.Column(db.String(32), default='observe', nullable=False, index=True)  # observe, warn, require_approval, deny_simulation
    status = db.Column(db.String(32), default='active', nullable=False, index=True)
    version = db.Column(db.String(32), default='1.0.0', nullable=False)

    def __repr__(self):
        return f'<ControlPolicy {self.policy_name!r} status={self.status}>'

    def to_dict(self):
        rule = {}
        if self.rule_json:
            try:
                rule = json.loads(self.rule_json)
            except Exception:
                pass
        return {
            'id': self.id,
            'policy_name': self.policy_name,
            'policy_type': self.policy_type,
            'rule': rule,
            'enforcement_mode': self.enforcement_mode,
            'status': self.status,
            'version': self.version,
            'organization_id': self.organization_id,
        }
