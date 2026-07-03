"""
MarketplaceItem model - Phase 20 Marketplace.
Catalog courses, virtual labs, Docker plugins, templates, and reports.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class MarketplaceItem(db.Model, TimestampMixin, TenantMixin):
    """Marketplace digital assets."""
    __tablename__ = 'marketplace_items'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('marketplace_categories.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Integer, default=0) # Token credit price
    asset_type = db.Column(db.String(32), default='courses') # courses, labs, plugins, templates, reports
    asset_url = db.Column(db.String(256), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    purchases = db.relationship('MarketplacePurchase', backref='item', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<MarketplaceItem {self.name!r} type={self.asset_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'asset_type': self.asset_type,
            'asset_url': self.asset_url,
            'is_active': self.is_active
        }
