"""
SigmaRule model — Phase 18 SOC Platform.
Stores Sigma detection rules for SIEM correlation (simulation only).
"""
from app.extensions import db
from app.models.mixins import TimestampMixin


SIGMA_STATUSES = ['experimental', 'test', 'stable', 'deprecated']
SIGMA_SEVERITIES = ['informational', 'low', 'medium', 'high', 'critical']


class SigmaRule(TimestampMixin, db.Model):
    """Sigma detection rule for SIEM correlation."""
    __tablename__ = 'sigma_rules'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, default='')
    author = db.Column(db.String(128), default='unknown')
    logsource = db.Column(db.String(128), default='')           # e.g. "windows/sysmon"
    detection_yaml = db.Column(db.Text, nullable=False)          # full Sigma YAML
    tags = db.Column(db.Text, default='')                        # comma-separated MITRE tags
    severity = db.Column(db.String(16), default='medium')
    status = db.Column(db.String(16), default='experimental')
    false_positives = db.Column(db.Text, default='')
    references = db.Column(db.Text, default='')

    # Validation / testing
    is_valid = db.Column(db.Boolean, default=False)
    validation_error = db.Column(db.Text, nullable=True)
    hit_count = db.Column(db.Integer, default=0)

    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)

    def __repr__(self):
        return f'<SigmaRule {self.title} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'author': self.author,
            'logsource': self.logsource,
            'tags': self.tags,
            'severity': self.severity,
            'status': self.status,
            'is_valid': self.is_valid,
            'hit_count': self.hit_count,
        }
