"""
Hunt model — Phase 18 SOC Platform / Threat Hunting.
Represents a threat hunting session (simulation only).
"""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin


HUNT_TYPES = ['ioc', 'behavioral', 'anomaly', 'mitre']
HUNT_STATUSES = ['planned', 'active', 'completed', 'cancelled']


class Hunt(TimestampMixin, db.Model):
    """Threat hunting session."""
    __tablename__ = 'hunts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, default='')
    hunt_type = db.Column(db.String(32), nullable=False)     # ioc/behavioral/anomaly/mitre
    status = db.Column(db.String(24), default='planned')

    # Analyst
    analyst_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Hunt context
    hypothesis = db.Column(db.Text, default='')
    query = db.Column(db.Text, default='')                   # search query / IOC list / technique
    findings = db.Column(db.Text, default='')                # JSON-serialized findings

    # Results summary
    artifacts_found = db.Column(db.Integer, default=0)
    iocs_identified = db.Column(db.Integer, default=0)
    systems_affected = db.Column(db.Integer, default=0)
    true_positive = db.Column(db.Boolean, nullable=True)

    # Timing
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)

    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)

    # Relationships
    analyst = db.relationship('User', foreign_keys=[analyst_id], lazy='joined',
                              primaryjoin='Hunt.analyst_id == User.id')

    def __repr__(self):
        return f'<Hunt {self.name!r} type={self.hunt_type} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hunt_type': self.hunt_type,
            'status': self.status,
            'hypothesis': self.hypothesis,
            'artifacts_found': self.artifacts_found,
            'iocs_identified': self.iocs_identified,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
        }
