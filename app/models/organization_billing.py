import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin

BILLING_STATUSES = ('trial', 'active', 'past_due', 'cancelled')
BILLING_PLANS = ('free', 'professional', 'enterprise')

# Valid state machine transitions
ALLOWED_TRANSITIONS = {
    'trial': {'active'},
    'active': {'past_due', 'cancelled'},
    'past_due': {'active', 'cancelled'},
    'cancelled': set(),  # terminal state — must re-subscribe
}


class OrganizationBilling(db.Model, TimestampMixin):
    """
    Billing record for an organization.

    State machine:
        trial ──► active ──► past_due ──► cancelled
                    └──────────────────► cancelled
    """
    __tablename__ = 'organization_billing'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False, unique=True, index=True
    )

    plan_type = db.Column(db.String(20), default='free', nullable=False)
    status = db.Column(db.String(20), default='trial', nullable=False, index=True)

    trial_ends_at = db.Column(db.DateTime, nullable=True)
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)

    # External payment provider references (populated by webhooks in production)
    stripe_customer_id = db.Column(db.String(100), nullable=True, unique=True)
    razorpay_customer_id = db.Column(db.String(100), nullable=True, unique=True)

    organization = db.relationship('Organization', back_populates='billing')

    def transition_to(self, new_status: str) -> tuple[bool, str]:
        """
        Attempt a billing state transition.
        Returns (success, error_message).
        """
        allowed = ALLOWED_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            return False, f"Cannot transition from '{self.status}' to '{new_status}'."
        self.status = new_status
        return True, None

    def is_active(self) -> bool:
        return self.status in ('trial', 'active')

    def __repr__(self):
        return f'<OrganizationBilling org={self.organization_id} plan={self.plan_type} status={self.status}>'
