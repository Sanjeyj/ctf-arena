"""
SecurityEvent model - Phase 22 Security Data Lake.
Stores normalized security events collected from diverse logs sources.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class SecurityEvent(db.Model, TimestampMixin, TenantMixin):
    """Normalized security log records."""
    __tablename__ = 'security_events'

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(80), nullable=False, index=True) # e.g. authentication, network, process
    severity = db.Column(db.String(32), default='medium') # low, medium, high, critical
    source = db.Column(db.String(120), default='SOC') # SOC, CTI, Range, Research, Marketplace, Agents
    payload_json = db.Column(db.Text, default='{}')
    timestamp = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<SecurityEvent {self.event_type} severity={self.severity}>'

    def to_dict(self):
        import json
        try:
            payload = json.loads(self.payload_json) if self.payload_json else {}
        except Exception:
            payload = {}
        return {
            'id': self.id,
            'event_type': self.event_type,
            'severity': self.severity,
            'source': self.source,
            'payload': payload,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
