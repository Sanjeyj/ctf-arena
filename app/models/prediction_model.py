"""
PredictionModel model - Phase 27 Global Security Intelligence Network.
Represents a trained threat prediction model with versioning and accuracy metadata.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class PredictionModel(db.Model, TimestampMixin, TenantMixin):
    """Threat prediction model registry."""
    __tablename__ = 'prediction_models'

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(120), nullable=False)
    confidence = db.Column(db.Float, default=0.8, nullable=False)
    version = db.Column(db.String(32), default='1.0.0', nullable=False)
    accuracy = db.Column(db.Float, default=0.75, nullable=False)

    def __repr__(self):
        return f'<PredictionModel {self.model_name!r} v{self.version} acc={self.accuracy}>'

    def to_dict(self):
        return {
            'id': self.id,
            'model_name': self.model_name,
            'confidence': self.confidence,
            'version': self.version,
            'accuracy': self.accuracy,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
