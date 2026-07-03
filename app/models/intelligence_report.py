"""
IntelligenceReport model - Phase 27 Global Security Intelligence Network.
Represents a structured intelligence report ingested from a source.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class IntelligenceReport(db.Model, TimestampMixin, TenantMixin):
    """Intelligence report with confidence scoring."""
    __tablename__ = 'intelligence_reports'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    severity = db.Column(db.String(32), default='medium', nullable=False)  # low, medium, high, critical
    source = db.Column(db.String(255), nullable=False)
    confidence = db.Column(db.Float, default=0.7, nullable=False)
    summary = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<IntelligenceReport {self.title!r} severity={self.severity}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'severity': self.severity,
            'source': self.source,
            'confidence': self.confidence,
            'summary': self.summary,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
