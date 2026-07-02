"""
YaraRule model — Phase 18 SOC Platform.
Stores YARA detection rules for malware/artifact scanning (simulation only).
"""
from app.extensions import db
from app.models.mixins import TimestampMixin


YARA_STATUSES = ['draft', 'testing', 'production', 'deprecated']


class YaraRule(TimestampMixin, db.Model):
    """YARA rule for file/memory artifact detection."""
    __tablename__ = 'yara_rules'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, default='')
    author = db.Column(db.String(128), default='unknown')
    rule_text = db.Column(db.Text, nullable=False)           # raw YARA rule text
    tags = db.Column(db.Text, default='')                    # comma-separated
    status = db.Column(db.String(16), default='draft')
    references = db.Column(db.Text, default='')

    # Validation / testing
    is_valid = db.Column(db.Boolean, default=False)
    validation_error = db.Column(db.Text, nullable=True)
    hit_count = db.Column(db.Integer, default=0)

    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)

    def __repr__(self):
        return f'<YaraRule {self.name} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'author': self.author,
            'tags': self.tags,
            'status': self.status,
            'is_valid': self.is_valid,
            'hit_count': self.hit_count,
        }
