"""
TrustDecision model - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Audit ledger for Zero Trust decision evaluation results.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class TrustDecision(db.Model, TimestampMixin, TenantMixin):
    """TrustDecision model."""
    __tablename__ = 'trust_decisions'

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.Integer, db.ForeignKey('trust_identities.id', ondelete='SET NULL'), nullable=True, index=True)
    device_posture_id = db.Column(db.Integer, db.ForeignKey('device_postures.id', ondelete='SET NULL'), nullable=True, index=True)
    resource_type = db.Column(db.String(120), nullable=False)
    resource_id = db.Column(db.String(120), nullable=False)
    requested_action = db.Column(db.String(120), nullable=False)
    trust_score = db.Column(db.Float, default=100.0, nullable=False)  # 0 to 100
    decision = db.Column(db.String(64), nullable=False)  # allow, allow_with_monitoring, require_step_up, deny_simulation
    explanation = db.Column(db.Text, nullable=True)
    policy_version = db.Column(db.String(32), default='1.0.0', nullable=False)

    def __repr__(self):
        return f'<TrustDecision decision={self.decision} score={self.trust_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'identity_id': self.identity_id,
            'device_posture_id': self.device_posture_id,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'requested_action': self.requested_action,
            'trust_score': self.trust_score,
            'decision': self.decision,
            'explanation': self.explanation,
            'policy_version': self.policy_version,
            'organization_id': self.organization_id,
        }
