"""
CloudRegion model - Phase 24 Global Cyber Security Cloud.
Details cloud geographical regions registry (us-east, eu-west, asia-south, private-cloud).
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class CloudRegion(db.Model, TimestampMixin, TenantMixin):
    """Geographical cloud region database record."""
    __tablename__ = 'cloud_regions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    slug = db.Column(db.String(64), nullable=False, unique=True, index=True) # us-east, eu-west, etc.
    region_code = db.Column(db.String(64), nullable=True) # e.g. us-east-1
    status = db.Column(db.String(32), default='active') # active, inactive
    location = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f'<CloudRegion {self.slug!r} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'region_code': self.region_code,
            'status': self.status,
            'location': self.location
        }
