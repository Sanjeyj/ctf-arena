"""
AssetTag model - Phase 22 Asset Tagging.
Associates labels for dynamic querying.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class AssetTag(db.Model, TimestampMixin, TenantMixin):
    """Dynamic tagging key-value maps on catalog items."""
    __tablename__ = 'asset_tags'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False)
    key = db.Column(db.String(80), nullable=False)
    value = db.Column(db.String(120), nullable=False)

    # Relationships
    asset = db.relationship('Asset', backref=db.backref('tags', cascade='all, delete-orphan', lazy='dynamic'))

    def __repr__(self):
        return f'<AssetTag {self.key}={self.value}>'

    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'key': self.key,
            'value': self.value
        }
