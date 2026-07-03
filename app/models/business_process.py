"""
BusinessProcess model - Phase 25 Cyber Resilience & Digital Enterprise.
Tracks critical enterprise business processes, their owners, criticality, and recovery objectives.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class BusinessProcess(db.Model, TimestampMixin, TenantMixin):
    """Critical Business Process record."""
    __tablename__ = 'business_processes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    owner = db.Column(db.String(120), nullable=True)
    criticality = db.Column(db.String(32), default='medium', nullable=False) # low, medium, high, critical
    rto = db.Column(db.Float, default=4.0, nullable=False) # Recovery Time Objective (hours)
    rpo = db.Column(db.Float, default=4.0, nullable=False) # Recovery Point Objective (hours)
    status = db.Column(db.String(32), default='active', nullable=False) # active, inactive

    def __repr__(self):
        return f'<BusinessProcess {self.name!r} criticality={self.criticality}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'owner': self.owner,
            'criticality': self.criticality,
            'rto': self.rto,
            'rpo': self.rpo,
            'status': self.status,
            'organization_id': self.organization_id
        }
