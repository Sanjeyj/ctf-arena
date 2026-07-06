"""
ModelGovernanceRecord model - Phase 31 Cyber Platform Control Plane.
Tracks AI provider/model governance records.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ModelGovernanceRecord(db.Model, TimestampMixin, TenantMixin):
    """ModelGovernanceRecord model."""
    __tablename__ = 'model_governance_records'

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(120), nullable=False)
    provider = db.Column(db.String(64), nullable=False)  # openai, anthropic, gemini, ollama, stub
    purpose = db.Column(db.Text, nullable=True)
    risk_level = db.Column(db.String(32), default='medium', nullable=False)  # low, medium, high, critical
    approval_status = db.Column(db.String(32), default='draft', nullable=False, index=True)  # draft, evaluation, approved, restricted, retired
    evaluation_score = db.Column(db.Float, default=1.0, nullable=False)
    last_reviewed_at = db.Column(db.DateTime, nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ModelGovernanceRecord {self.model_name!r} provider={self.provider} status={self.approval_status}>'

    def to_dict(self):
        meta = {}
        if self.metadata_json:
            try:
                meta = json.loads(self.metadata_json)
            except Exception:
                pass
        return {
            'id': self.id,
            'model_name': self.model_name,
            'provider': self.provider,
            'purpose': self.purpose,
            'risk_level': self.risk_level,
            'approval_status': self.approval_status,
            'evaluation_score': self.evaluation_score,
            'last_reviewed_at': self.last_reviewed_at.isoformat() if self.last_reviewed_at else None,
            'metadata': meta,
            'organization_id': self.organization_id,
        }
