"""
DigitalWorker model - Phase 26 Autonomous Cyber Enterprise.
Represents AI/digital workforce bots assigned to security roles and specializations.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class DigitalWorker(db.Model, TimestampMixin, TenantMixin):
    """Digital worker bot profile."""
    __tablename__ = 'digital_workers'

    id = db.Column(db.Integer, primary_key=True)
    worker_name = db.Column(db.String(120), nullable=False)
    specialization = db.Column(db.String(120), nullable=False) # e.g. Sigma Parser, Threat Hunter
    utilization = db.Column(db.Float, default=0.0, nullable=False) # percentage (0-100)
    performance_score = db.Column(db.Float, default=100.0, nullable=False) # percentage (0-100)

    def __repr__(self):
        return f'<DigitalWorker {self.worker_name!r} spec={self.specialization}>'

    def to_dict(self):
        return {
            'id': self.id,
            'worker_name': self.worker_name,
            'specialization': self.specialization,
            'utilization': self.utilization,
            'performance_score': self.performance_score,
            'organization_id': self.organization_id
        }
