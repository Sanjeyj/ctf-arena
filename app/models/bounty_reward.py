"""
BountyReward model - Phase 20 Bug Bounty Platform.
Tracks payout amounts and transaction references for accepted reports.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class BountyReward(db.Model, TimestampMixin, TenantMixin):
    """Bug bounty cash/token rewards."""
    __tablename__ = 'bounty_rewards'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('vulnerability_reports.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Integer, default=0)
    payment_status = db.Column(db.String(32), default='pending') # pending, paid, cancelled
    reference_tx = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f'<BountyReward id={self.id} amount={self.amount}>'

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'amount': self.amount,
            'payment_status': self.payment_status,
            'reference_tx': self.reference_tx
        }
