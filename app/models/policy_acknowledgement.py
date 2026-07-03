"""
PolicyAcknowledgement model - Phase 23 Enterprise Governance.
Logs user acknowledgment dates of corporate policies.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class PolicyAcknowledgement(db.Model, TimestampMixin, TenantMixin):
    """Logs policy compliance acknowledgments."""
    __tablename__ = 'policy_acknowledgements'

    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey('policies.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    acknowledged_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    policy = db.relationship('Policy', backref=db.backref('acknowledgements', cascade='all, delete-orphan', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('policy_acknowledgements', cascade='all, delete-orphan', lazy='dynamic'))

    def __repr__(self):
        return f'<PolicyAcknowledgement user_id={self.user_id} policy_id={self.policy_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'policy_id': self.policy_id,
            'user_id': self.user_id,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }
