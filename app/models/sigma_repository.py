"""
SigmaRepository model - Phase 19 Security Research & CTI Platform.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class SigmaRepository(db.Model, TimestampMixin, TenantMixin):
    """SIEM correlation Sigma rules repository."""
    __tablename__ = 'sigma_repositories'

    id = db.Column(db.Integer, primary_key=True)
    rule_name = db.Column(db.String(120), nullable=False, index=True)
    rule_text = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='experimental') # e.g. experimental, production

    def __repr__(self):
        return f'<SigmaRepository {self.rule_name!r}>'

    def to_dict(self):
        return {
            'id': self.id,
            'rule_name': self.rule_name,
            'rule_text': self.rule_text,
            'status': self.status,
            'organization_id': self.organization_id
        }
