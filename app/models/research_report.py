"""
ResearchReport model - Phase 19 Security Research & CTI Platform.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class ResearchReport(db.Model, TimestampMixin, TenantMixin):
    """CTI Research Report containing static threat analysis, metadata, and mitigations."""
    __tablename__ = 'research_reports'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    executive_summary = db.Column(db.Text, nullable=True)
    technical_analysis = db.Column(db.Text, nullable=True)
    ioc_json = db.Column(db.Text, nullable=True) # JSON list of associated IOCs
    mitre_techniques_json = db.Column(db.Text, nullable=True) # JSON list of ATT&CK techniques
    recommendations = db.Column(db.Text, nullable=True)
    
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    # Relationships
    author = db.relationship('User', backref=db.backref('research_reports', lazy='dynamic'))

    def __repr__(self):
        return f'<ResearchReport {self.title!r}>'

    def to_dict(self):
        try:
            iocs = json.loads(self.ioc_json) if self.ioc_json else []
        except Exception:
            iocs = []
        try:
            techniques = json.loads(self.mitre_techniques_json) if self.mitre_techniques_json else []
        except Exception:
            techniques = []
        return {
            'id': self.id,
            'title': self.title,
            'executive_summary': self.executive_summary,
            'technical_analysis': self.technical_analysis,
            'iocs': iocs,
            'mitre_techniques': techniques,
            'recommendations': self.recommendations,
            'author_id': self.author_id,
            'author_name': self.author.username if self.author else 'System',
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None
        }
