"""
EventSource model - Phase 22 Security Data Lake.
Manages ingestion endpoints sources configurations.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class EventSource(db.Model, TimestampMixin, TenantMixin):
    """Data Lake log collectors configurations."""
    __tablename__ = 'event_sources'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    source_type = db.Column(db.String(80), default='SOC') # SOC, CTI, Cyber Range, etc.
    status = db.Column(db.String(32), default='active') # active, inactive

    def __repr__(self):
        return f'<EventSource {self.name} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'source_type': self.source_type,
            'status': self.status
        }
