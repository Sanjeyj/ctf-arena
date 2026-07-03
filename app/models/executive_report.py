"""
ExecutiveReport model - Phase 22 Executive Reporting.
Logs strategic metrics summary profiles.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class ExecutiveReport(db.Model, TimestampMixin, TenantMixin):
    """CISO report snapshot."""
    __tablename__ = 'executive_reports'

    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(32), default='weekly') # daily, weekly, monthly
    open_incidents = db.Column(db.Integer, default=0)
    risk_score = db.Column(db.Float, default=50.0)
    asset_health = db.Column(db.Float, default=100.0)
    training_status = db.Column(db.String(120), default='85% complete')
    threat_level = db.Column(db.String(32), default='LOW')

    def __repr__(self):
        return f'<ExecutiveReport id={self.id} type={self.report_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'report_type': self.report_type,
            'open_incidents': self.open_incidents,
            'risk_score': self.risk_score,
            'asset_health': self.asset_health,
            'training_status': self.training_status,
            'threat_level': self.threat_level,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None
        }
