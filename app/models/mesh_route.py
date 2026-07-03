"""
MeshRoute model - Phase 24 Global Cyber Security Cloud.
Tracks latency and weights routing between regional node endpoints.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class MeshRoute(db.Model, TimestampMixin, TenantMixin):
    """Detailed mesh route link weights mapping."""
    __tablename__ = 'mesh_routes'

    id = db.Column(db.Integer, primary_key=True)
    source_node = db.Column(db.String(120), nullable=False, index=True)
    destination_node = db.Column(db.String(120), nullable=False, index=True)
    weight = db.Column(db.Integer, default=1)
    latency = db.Column(db.Float, default=15.0) # in ms
    status = db.Column(db.String(32), default='active') # active, degraded, offline

    def __repr__(self):
        return f'<MeshRoute {self.source_node}->{self.destination_node} latency={self.latency}>'

    def to_dict(self):
        return {
            'id': self.id,
            'source_node': self.source_node,
            'destination_node': self.destination_node,
            'weight': self.weight,
            'latency': self.latency,
            'status': self.status
        }
