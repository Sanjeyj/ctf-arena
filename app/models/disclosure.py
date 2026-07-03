"""
Disclosure model - Phase 20 Bug Bounty Platform.
Manages vulnerability coordinates and publication advisories.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class Disclosure(db.Model, TimestampMixin, TenantMixin):
    """Bug bounty coordinated vulnerability disclosure tracking."""
    __tablename__ = 'disclosures'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('vulnerability_reports.id', ondelete='CASCADE'), nullable=False)
    disclosure_type = db.Column(db.String(32), default='coordinated') # coordinated, full, private
    public_url = db.Column(db.String(256), nullable=True)
    advisory_text = db.Column(db.Text, nullable=True)
    disclosed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Disclosure id={self.id} type={self.disclosure_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'disclosure_type': self.disclosure_type,
            'public_url': self.public_url,
            'advisory_text': self.advisory_text,
            'disclosed_at': self.disclosed_at.isoformat() if self.disclosed_at else None
        }
