"""
MarketplacePurchase model - Phase 20 Marketplace.
Tracks customer purchasing logs and license activation statuses.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class MarketplacePurchase(db.Model, TimestampMixin, TenantMixin):
    """Marketplace transaction record."""
    __tablename__ = 'marketplace_purchases'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('marketplace_items.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    purchase_price = db.Column(db.Integer, default=0)
    status = db.Column(db.String(32), default='completed') # completed, pending, refunded

    def __repr__(self):
        return f'<MarketplacePurchase id={self.id} item_id={self.item_id} user_id={self.user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'user_id': self.user_id,
            'purchase_price': self.purchase_price,
            'status': self.status,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None
        }
