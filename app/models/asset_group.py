"""
AssetGroup model - Phase 22 Asset Management.
Organizes assets into logical organizational group sets.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class AssetGroup(db.Model, TimestampMixin, TenantMixin):
    """Categorized cluster grouping for target hosts."""
    __tablename__ = 'asset_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<AssetGroup {self.name!r}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }
