"""
Detection model — Phase 18 SOC Platform.
Records a triggered detection event from Sigma or YARA rules.
"""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin


DETECTION_STATUSES = ['new', 'reviewed', 'escalated', 'false_positive', 'closed']
RULE_TYPES = ['sigma', 'yara']


class Detection(TimestampMixin, db.Model):
    """A triggered detection from a Sigma or YARA rule match."""
    __tablename__ = 'detections'

    id = db.Column(db.Integer, primary_key=True)
    rule_type = db.Column(db.String(16), nullable=False)     # sigma / yara
    rule_id = db.Column(db.Integer, nullable=False)          # FK to sigma_rules or yara_rules
    rule_name = db.Column(db.String(256), default='')        # denormalized for display
    matched_data = db.Column(db.Text, default='')            # JSON-serialized match context
    severity = db.Column(db.String(16), default='medium')
    status = db.Column(db.String(24), default='new')
    analyst_notes = db.Column(db.Text, default='')

    # Alert linkage (optional — detection can be escalated to alert)
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'), nullable=True)

    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)

    def __repr__(self):
        return f'<Detection {self.rule_type}:{self.rule_id} sev={self.severity}>'

    def to_dict(self):
        return {
            'id': self.id,
            'rule_type': self.rule_type,
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'severity': self.severity,
            'status': self.status,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None,
        }
