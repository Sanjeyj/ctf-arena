"""
ComplianceMonitor model - Phase 26 Autonomous Cyber Enterprise.
Measures continuous regulatory compliance alignment and compliance drift detections.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class ComplianceMonitor(db.Model, TimestampMixin, TenantMixin):
    """Compliance alignment tracker."""
    __tablename__ = 'compliance_monitors'

    id = db.Column(db.Integer, primary_key=True)
    framework = db.Column(db.String(120), nullable=False) # SOC2, ISO27001, HIPAA, NIST, etc.
    score = db.Column(db.Float, default=100.0, nullable=False)
    drift_status = db.Column(db.String(32), default='stable', nullable=False) # stable, drift_detected
    last_check = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<ComplianceMonitor framework={self.framework} score={self.score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'framework': self.framework,
            'score': self.score,
            'drift_status': self.drift_status,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'organization_id': self.organization_id
        }
