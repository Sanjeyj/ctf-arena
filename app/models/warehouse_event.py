"""
WarehouseEvent model - Phase 23 Security Data Warehouse.
Stores historically aggregated event logs.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class WarehouseEvent(db.Model, TimestampMixin, TenantMixin):
    """Data warehouse records log."""
    __tablename__ = 'warehouse_events'

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(80), nullable=False, index=True)
    source = db.Column(db.String(80), default='SOC') # SOC, CTI, LMS, Cyber Range, Research, AI Agents
    severity = db.Column(db.String(32), default='medium')
    payload_json = db.Column(db.Text, default='{}')
    timestamp = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<WarehouseEvent {self.event_type} source={self.source}>'

    def to_dict(self):
        import json
        try:
            payload = json.loads(self.payload_json) if self.payload_json else {}
        except Exception:
            payload = {}
        return {
            'id': self.id,
            'event_type': self.event_type,
            'source': self.source,
            'severity': self.severity,
            'payload': payload,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
