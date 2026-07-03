"""
Asset model - Phase 22 Asset Management.
Tracks network inventory elements, types, and risk posture.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class Asset(db.Model, TimestampMixin, TenantMixin):
    """Host or application asset in inventory list."""
    __tablename__ = 'assets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    type_label = db.Column(db.String(64), default='server') # server, workstation, container, application, cloud
    risk_level = db.Column(db.String(32), default='low') # low, medium, high, critical
    criticality = db.Column(db.Integer, default=1) # 1 to 10 scale
    ip_address = db.Column(db.String(45), nullable=True)
    status = db.Column(db.String(32), default='active')

    group_id = db.Column(db.Integer, db.ForeignKey('asset_groups.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    group = db.relationship('AssetGroup', backref=db.backref('assets', lazy='dynamic'))

    def __repr__(self):
        return f'<Asset {self.name!r} type={self.type_label} risk={self.risk_level}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type_label': self.type_label,
            'risk_level': self.risk_level,
            'criticality': self.criticality,
            'ip_address': self.ip_address,
            'status': self.status,
            'group_id': self.group_id
        }
