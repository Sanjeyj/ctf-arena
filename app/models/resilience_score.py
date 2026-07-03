"""
ResilienceScore model - Phase 24 Global Cyber Security Cloud.
Stores organizational cyber resilience telemetry metric indicators.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class ResilienceScore(db.Model, TimestampMixin, TenantMixin):
    """Calculated resilience metric indexes records."""
    __tablename__ = 'resilience_scores'

    id = db.Column(db.Integer, primary_key=True)
    response_time = db.Column(db.Float, default=50.0) # 0 to 100 metric
    controls = db.Column(db.Float, default=50.0)
    incidents = db.Column(db.Float, default=50.0)
    training = db.Column(db.Float, default=50.0)
    risk = db.Column(db.Float, default=50.0)
    resilience = db.Column(db.Float, default=50.0) # aggregate computed rating

    def __repr__(self):
        return f'<ResilienceScore index={self.resilience} organization_id={self.organization_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'response_time': self.response_time,
            'controls': self.controls,
            'incidents': self.incidents,
            'training': self.training,
            'risk': self.risk,
            'resilience': self.resilience
        }
