"""
MarketplaceCategory model - Phase 20 Marketplace.
Group offerings by domains (courses, labs, plugins, templates, reports).
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class MarketplaceCategory(db.Model, TimestampMixin, TenantMixin):
    """Marketplace item categories."""
    __tablename__ = 'marketplace_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)

    # Relationships
    items = db.relationship('MarketplaceItem', backref='category', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<MarketplaceCategory {self.name!r}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }
